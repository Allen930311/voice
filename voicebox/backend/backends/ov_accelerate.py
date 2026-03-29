"""
OpenVINO 加速輔助模組
====================
提供兩種加速路徑：

1. OVStaticModel  — 把任意 PyTorch nn.Module 轉成 OpenVINO IR，
                    用於非自回歸組件（encoder、codec）。
                    使用 torch.jit.trace → ov.convert_model → ov.compile_model，
                    無需 MSVC cl.exe。

2. OVHFModel      — 透過 optimum-intel 把 HuggingFace transformers 模型
                    （含自回歸 generate()）包裝為 OpenVINO 推理，
                    適用於 Whisper STT、Qwen TTS 等標準 HF 模型。

自動降級：若 OpenVINO 不可用，所有包裝器都直接 pass-through 到原始模型。
"""

from __future__ import annotations

import logging
import shutil
from threading import Lock
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ── 全域共用鎖：防止多執行緒併發匯出同一個模型造成損壞 ──────────────────────────────
_EXPORT_LOCKS: dict[str, Lock] = {}

# ── OpenVINO 裝置優先順序 ──────────────────────────────────────────────────────
# GPU = Intel Arc iGPU, NPU = Intel AI Boost, CPU = OpenVINO CPU 優化版
OV_DEVICE_PRIORITY = ["NPU", "GPU", "CPU"]


def get_best_ov_device(exclude_npu: bool = False) -> Optional[str]:
    """
    回傳最佳可用的 OpenVINO 裝置 ID，或 None（若 OpenVINO 不可用）。

    優先：NPU > GPU > CPU
    """
    try:
        import openvino as ov
        core = ov.Core()
        available = list(core.available_devices)
        print(f"[OV] 偵測到的硬體列表: {available}")
        
        priority = list(OV_DEVICE_PRIORITY)
        if exclude_npu and "NPU" in priority:
            priority.remove("NPU")
            
        for dev in priority:
            if dev in available:
                print(f"[OV] 🚀 選定最優硬體加速器: {dev}")
                return dev
        return None
    except Exception as e:
        print(f"[OV] ❌ 裝置偵測失敗: {e}")
        return None


def get_ov_cache_dir(model_id: str, task: str) -> str:
    """
    建立並回傳 OpenVINO 模型快取目錄。
    預設位於 ~/.cache/voicebox/ov_models/
    """
    # 處理路徑相容性 (openai/whisper-base -> openai--whisper-base)
    safe_id = model_id.replace("/", "--").replace("\\", "--")
    cache_dir = Path.home() / ".cache" / "voicebox" / "ov_models" / f"{safe_id}_{task}"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return str(cache_dir)


def safe_load_ov_model(model_id: str, task: str, device: str = "GPU"):
    """
    執行緒安全的 OpenVINO 模型載入。
    若快取不存在則執行 Export，若存在則直接從快取載入並 Compile。
    """
    from optimum.intel import OVModelForSpeechSeq2Seq
    
    cache_dir = get_ov_cache_dir(model_id, task)
    cache_path = Path(cache_dir)
    xml_path = cache_path / "openvino_model.xml"

    # 使用 Lock 防止併發 Export
    lock = _EXPORT_LOCKS.setdefault(model_id, Lock())
    with lock:
        # 如果 XML 不存在，或者目錄是空的（可能上一次 Export 中斷了）
        is_cached = xml_path.exists()
        
        if not is_cached:
            logger.info("OpenVINO: Exporting %s to %s (First run only)...", model_id, cache_dir)
            try:
                # 1. 執行 Export 但暫不 Compile
                model = OVModelForSpeechSeq2Seq.from_pretrained(
                    model_id, 
                    export=True, 
                    compile=False,
                    trust_remote_code=True
                )
                # 2. 儲存 IR 檔案到快取目錄
                model.save_pretrained(cache_dir)
                logger.info("OpenVINO: Model IR saved successfully.")
            except Exception as e:
                logger.error("OpenVINO Export failed: %s. Cleaning up %s", e, cache_dir)
                if cache_path.exists():
                    shutil.rmtree(cache_dir, ignore_errors=True)
                raise
            
        # 3. 從快取目錄載入並 Compile 到目標裝置
        logger.info("OpenVINO: Compiling model from cache on %s...", device)
        return OVModelForSpeechSeq2Seq.from_pretrained(
            cache_dir, 
            device=device, 
            compile=True,
            trust_remote_code=True
        )


def is_openvino_available() -> bool:
    """回傳 OpenVINO 是否已安裝。"""
    try:
        import openvino  # noqa: F401
        import optimum.intel  # noqa: F401
        return True
    except ImportError:
        return False


# ── OVStaticModel：靜態圖模型（一次 trace + compile）────────────────────────────

class OVStaticModel:
    """
    把 PyTorch nn.Module 轉換為 OpenVINO 靜態圖並在 GPU/NPU 上執行。
    """

    def __init__(
        self,
        module: Any,
        example_input: Any,
        ov_device: Optional[str] = None,
    ):
        self._module = module
        self._compiled = None
        self._infer_req = None
        self._ov_device = ov_device or get_best_ov_device()
        self._fallback = not is_openvino_available() or self._ov_device is None

        if not self._fallback:
            try:
                self._compile(module, example_input)
            except Exception as e:
                logger.warning("OVStaticModel compile failed (%s), falling back to CPU: %s",
                               type(e).__name__, e)
                self._fallback = True

    def _compile(self, module: Any, example_input: Any):
        import torch
        import openvino as ov

        logger.info("OVStaticModel: tracing model…")
        with torch.no_grad():
            traced = torch.jit.trace(module, example_input)

        logger.info("OVStaticModel: converting to OpenVINO IR…")
        ov_model = ov.convert_model(traced, example_input=example_input)

        core = ov.Core()
        logger.info("OVStaticModel: compiling for %s…", self._ov_device)
        self._compiled = core.compile_model(ov_model, self._ov_device)
        self._infer_req = self._compiled.create_infer_request()
        logger.info("OVStaticModel: ready on %s", self._ov_device)

    def __call__(self, *args, **kwargs):
        """推理呼叫：若已編譯則走 OpenVINO，否則走原始模型。"""
        if self._fallback or self._compiled is None:
            import torch
            with torch.no_grad():
                return self._module(*args, **kwargs)

        import torch
        import numpy as np

        # 準備輸入
        inputs = {}
        for i, inp in enumerate(args):
            if isinstance(inp, torch.Tensor):
                inputs[self._compiled.input(i)] = inp.detach().cpu().numpy()
            elif isinstance(inp, np.ndarray):
                inputs[self._compiled.input(i)] = inp
            else:
                with torch.no_grad():
                    return self._module(*args, **kwargs)

        self._infer_req.infer(inputs)

        outputs = [
            torch.from_numpy(self._infer_req.get_output_tensor(i).data.copy())
            for i in range(len(self._compiled.outputs))
        ]
        return outputs[0] if len(outputs) == 1 else tuple(outputs)


# ── OVHFModel：HuggingFace transformers 自回歸模型包裝 ──────────────────────────

class OVHFModel:
    """
    用 optimum-intel 把 HuggingFace 模型包裝為 OpenVINO 推理。
    """

    def __init__(self, ov_model: Any, fallback_model: Any = None):
        self._ov_model = ov_model
        self._fallback = fallback_model

    @classmethod
    def from_pretrained(
        cls,
        model_id: str,
        task: str = "causal-lm",
        ov_device: Optional[str] = None,
        export: bool = True,
        **kwargs,
    ) -> "OVHFModel":
        device = ov_device or get_best_ov_device() or "CPU"

        try:
            from optimum.intel import (
                OVModelForSpeechSeq2Seq,
                OVModelForCausalLM,
                OVModelForSeq2SeqLM,
            )
            class_map = {
                "speech-seq2seq": OVModelForSpeechSeq2Seq,
                "causal-lm":      OVModelForCausalLM,
                "seq2seq":        OVModelForSeq2SeqLM,
            }
            OVClass = class_map[task]
            print(f"[OV] ⏳ 正在將 {model_id} 佈署至 {device} 硬體核心...")
            ov_model = OVClass.from_pretrained(
                model_id,
                export=export,
                device=device,
                trust_remote_code=True,
                **kwargs,
            )
            print(f"[OV] ✅ {model_id} 已成功在 {device} 上運行！")
            return cls(ov_model)
        except Exception as e:
            print(f"[OV] ❌ {model_id} 佈署至 {device} 失敗: {e}")
            return cls(None)

    def is_available(self) -> bool:
        return self._ov_model is not None

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        return getattr(self._ov_model, name)

    def __call__(self, *args, **kwargs):
        return self._ov_model(*args, **kwargs)


class OVSTTBackend:
    """
    OpenVINO-based STT backend using Whisper.
    Explicitly optimized for Intel NPU and Arc GPU.
    Falls back to PyTorch CPU if OV load or runtime inference fails.
    """

    def __init__(self, model_size: str = "base"):
        self.model = None           # OVHFModel (GPU/NPU)
        self._fallback_model = None # WhisperForConditionalGeneration (CPU)
        self._use_fallback = False
        self.processor = None
        self.model_size = model_size
        self.device = get_best_ov_device() or "CPU"
        self._loaded_model_id = None

    def is_loaded(self) -> bool:
        return self.model is not None or self._fallback_model is not None

    def _load_pytorch_fallback(self, model_id: str):
        """載入 PyTorch CPU 備援模型（同步，在執行緒中呼叫）。"""
        from transformers import WhisperForConditionalGeneration
        logger.info("[OV→CPU] 載入 PyTorch Whisper 備援模型: %s", model_id)
        self._fallback_model = WhisperForConditionalGeneration.from_pretrained(model_id)
        self._fallback_model.to("cpu")
        self._use_fallback = True

    async def load_model(self, model_size: Optional[str] = None) -> None:
        """
        Lazy load Whisper via OVHFModel (optimum-intel).
        若 OV 載入失敗，自動降至 PyTorch CPU。
        """
        import asyncio
        from transformers import WhisperProcessor
        from .constants import WHISPER_HF_REPOS

        target_size = model_size or self.model_size
        model_id = WHISPER_HF_REPOS.get(target_size, f"openai/whisper-{target_size}")

        if self._loaded_model_id == model_id and self.is_loaded():
            return

        def _load():
            self.processor = WhisperProcessor.from_pretrained(model_id)

            logger.info("[OV] 正在加載 STT 模型: %s 至 %s...", model_id, self.device)
            ov_model = OVHFModel.from_pretrained(
                model_id,
                task="speech-seq2seq",
                ov_device=self.device,
                compile=True,
            )

            if ov_model.is_available():
                self.model = ov_model
                self._use_fallback = False
                logger.info("[OV] STT 模型成功載入至 %s", self.device)
            else:
                # OV 失敗 → 降至 PyTorch CPU
                logger.warning("[OV→CPU] OV 載入失敗，改用 PyTorch CPU 備援")
                self._load_pytorch_fallback(model_id)

            self._loaded_model_id = model_id
            self.model_size = target_size

        await asyncio.to_thread(_load)

    async def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        model_size: Optional[str] = None,
    ) -> str:
        """
        Perform transcription. 優先用 OV GPU/NPU；推理失敗時降至 PyTorch CPU。
        """
        import asyncio
        import torch
        from ..utils.audio import load_audio

        await self.load_model(model_size)

        def _run(active_model):
            audio, _ = load_audio(audio_path, sample_rate=16000)
            inputs = self.processor(audio, sampling_rate=16000, return_tensors="pt")

            gen_kwargs = {}
            if language:
                gen_kwargs["forced_decoder_ids"] = self.processor.get_decoder_prompt_ids(
                    language=language, task="transcribe"
                )

            with torch.no_grad():
                predicted_ids = active_model.generate(inputs.input_features, **gen_kwargs)

            return self.processor.batch_decode(predicted_ids, skip_special_tokens=True)[0].strip()

        def _run_with_fallback():
            active = self._fallback_model if self._use_fallback else self.model
            try:
                return _run(active)
            except Exception as e:
                if not self._use_fallback:
                    logger.warning("[OV→CPU] OV 推理失敗 (%s)，載入 PyTorch CPU 備援...", e)
                    self._load_pytorch_fallback(self._loaded_model_id)
                    return _run(self._fallback_model)
                raise

        return await asyncio.to_thread(_run_with_fallback)

    def unload_model(self):
        """釋放內存。"""
        if self.model is not None:
            del self.model
            self.model = None
        if self._fallback_model is not None:
            del self._fallback_model
            self._fallback_model = None
        if self.processor is not None:
            del self.processor
            self.processor = None
        self._loaded_model_id = None
        self._use_fallback = False
        logger.info("[OV] STT 模型已卸載。")
