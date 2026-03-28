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
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ── OpenVINO 裝置優先順序 ──────────────────────────────────────────────────────
# GPU = Intel Arc iGPU, NPU = Intel AI Boost, CPU = OpenVINO CPU 優化版
OV_DEVICE_PRIORITY = ["GPU", "NPU", "CPU"]


def get_best_ov_device() -> Optional[str]:
    """
    回傳最佳可用的 OpenVINO 裝置 ID，或 None（若 OpenVINO 不可用）。

    優先：GPU > NPU > CPU
    """
    try:
        import openvino as ov
        core = ov.Core()
        available = set(core.available_devices)
        for dev in OV_DEVICE_PRIORITY:
            if dev in available:
                return dev
        return None
    except ImportError:
        return None


def is_openvino_available() -> bool:
    """回傳 OpenVINO 是否已安裝。"""
    try:
        import openvino  # noqa: F401
        return True
    except ImportError:
        return False


# ── OVStaticModel：靜態圖模型（一次 trace + compile）────────────────────────────

class OVStaticModel:
    """
    把 PyTorch nn.Module 轉換為 OpenVINO 靜態圖並在 GPU/NPU 上執行。

    適合：
    - 編碼器（Encoder）
    - 音訊 codec（Decoder）
    - 任何輸入形狀固定的模型

    不適合：
    - 自回歸 generate()（輸入長度會變化）
    - 有 if/while 動態分支的模型

    使用範例：
        encoder = SomeEncoder().eval()
        ov_enc = OVStaticModel(encoder, example_input=torch.zeros(1, 80, 3000))
        output = ov_enc(audio_features)
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

        # 準備輸入（支援 Tensor 或 numpy）
        inputs = {}
        for i, inp in enumerate(args):
            if isinstance(inp, torch.Tensor):
                inputs[self._compiled.input(i)] = inp.detach().cpu().numpy()
            elif isinstance(inp, np.ndarray):
                inputs[self._compiled.input(i)] = inp
            else:
                # 無法序列化 → 降級
                with torch.no_grad():
                    return self._module(*args, **kwargs)

        self._infer_req.infer(inputs)

        # 轉回 Tensor
        outputs = [
            torch.from_numpy(self._infer_req.get_output_tensor(i).data.copy())
            for i in range(len(self._compiled.outputs))
        ]
        return outputs[0] if len(outputs) == 1 else tuple(outputs)

    @property
    def device_name(self) -> str:
        return self._ov_device or "cpu-fallback"

    @property
    def using_openvino(self) -> bool:
        return not self._fallback and self._compiled is not None


# ── OVHFModel：HuggingFace transformers 自回歸模型包裝 ──────────────────────────

class OVHFModel:
    """
    用 optimum-intel 把 HuggingFace 模型包裝為 OpenVINO 推理。

    支援 generate()，可處理動態長度的自回歸解碼（Whisper、Qwen TTS 等）。

    使用範例：
        ov_whisper = OVHFModel.from_pretrained(
            "openai/whisper-base",
            task="speech-seq2seq",
            ov_device="GPU",
        )
        ids = ov_whisper.generate(input_features)
    """

    _TASK_CLASS_MAP = {
        "speech-seq2seq": "OVModelForSpeechSeq2Seq",
        "causal-lm":      "OVModelForCausalLM",
        "seq2seq":        "OVModelForSeq2SeqLM",
    }

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
        """
        從 HuggingFace model ID 載入並包裝為 OpenVINO 推理。

        Args:
            model_id:  HuggingFace repo ID
            task:      "speech-seq2seq" / "causal-lm" / "seq2seq"
            ov_device: OpenVINO 裝置 ("GPU", "NPU", "CPU")；None = 自動選最佳
            export:    True = 匯出並快取 IR；False = 載入已快取的 IR
        """
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
            logger.info("OVHFModel: loading %s via optimum-intel on %s…", model_id, device)
            ov_model = OVClass.from_pretrained(
                model_id,
                export=export,
                device=device,
                **kwargs,
            )
            logger.info("OVHFModel: %s ready on %s", model_id, device)
            return cls(ov_model)
        except ImportError:
            logger.warning("optimum-intel not installed; OVHFModel unavailable for %s", model_id)
            return cls(None)
        except Exception as e:
            logger.warning("OVHFModel load failed for %s (%s): %s", model_id, device, e)
            return cls(None)

    def is_available(self) -> bool:
        return self._ov_model is not None

    def __getattr__(self, name: str):
        """把所有屬性 / 方法代理到底層 OV 模型。"""
        if name.startswith("_"):
            raise AttributeError(name)
        return getattr(self._ov_model, name)

    def __call__(self, *args, **kwargs):
        return self._ov_model(*args, **kwargs)
