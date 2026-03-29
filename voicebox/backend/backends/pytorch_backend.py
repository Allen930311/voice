"""
PyTorch backend implementation for TTS and STT.
"""

from typing import Optional, List, Tuple
import asyncio
import os
import logging
import torch
import numpy as np

logger = logging.getLogger(__name__)

from . import TTSBackend, STTBackend
from .constants import WHISPER_HF_REPOS, LANGUAGE_CODE_TO_NAME
from .base import (
    is_model_cached,
    get_torch_device,
    combine_voice_prompts as _combine_voice_prompts,
    model_load_progress,
)
from ..utils.cache import get_cache_key, get_cached_voice_prompt, cache_voice_prompt
from ..utils.audio import load_audio


class PyTorchTTSBackend:
    """PyTorch-based TTS backend using Qwen3-TTS."""

    def __init__(self, model_size: str = "1.7B"):
        self.model = None
        self.model_size = model_size
        self.device = self._get_device()
        self._current_model_size = None
        self._log_device()

    def _get_device(self) -> str:
        """Get the best available device."""
        return get_torch_device(allow_xpu=True, allow_directml=True)

    def _log_device(self):
        """Log selected device and hint at available OpenVINO devices."""
        logger.info("Qwen TTS device: %s", self.device)
        try:
            from .ov_accelerate import get_best_ov_device
            ov_dev = get_best_ov_device()
            if ov_dev and self.device == "cpu":
                logger.info(
                    "OpenVINO %s detected but Qwen TTS uses custom qwen_tts pipeline; "
                    "XPU/DirectML will be used when available.",
                    ov_dev,
                )
        except Exception:
            pass

    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self.model is not None

    def _get_model_path(self, model_size: str) -> str:
        """
        Get the HuggingFace Hub model ID.

        Args:
            model_size: Model size (1.7B or 0.6B)

        Returns:
            HuggingFace Hub model ID
        """
        hf_model_map = {
            "1.7B": "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
            "0.6B": "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
        }

        if model_size not in hf_model_map:
            raise ValueError(f"Unknown model size: {model_size}")

        return hf_model_map[model_size]

    def _is_model_cached(self, model_size: str) -> bool:
        return is_model_cached(self._get_model_path(model_size))

    async def load_model_async(self, model_size: Optional[str] = None):
        """
        Lazy load the TTS model with automatic downloading from HuggingFace Hub.

        Args:
            model_size: Model size to load (1.7B or 0.6B)
        """
        if model_size is None:
            model_size = self.model_size

        # If already loaded with correct size, return
        if self.model is not None and self._current_model_size == model_size:
            return

        # Unload existing model if different size requested
        if self.model is not None and self._current_model_size != model_size:
            self.unload_model()

        # Run blocking load in thread pool
        await asyncio.to_thread(self._load_model_sync, model_size)

    # Alias for compatibility
    load_model = load_model_async

    def _load_model_sync(self, model_size: str):
        """Synchronous model loading."""
        model_name = f"qwen-tts-{model_size}"
        is_cached = self._is_model_cached(model_size)

        with model_load_progress(model_name, is_cached):
            from qwen_tts import Qwen3TTSModel

            model_path = self._get_model_path(model_size)
            logger.info("Loading TTS model %s on %s...", model_size, self.device)

            if self.device == "cpu":
                self.model = Qwen3TTSModel.from_pretrained(
                    model_path,
                    torch_dtype=torch.float32,
                    low_cpu_mem_usage=False,
                )
            else:
                try:
                    self.model = Qwen3TTSModel.from_pretrained(
                        model_path,
                        device_map=self.device,
                        torch_dtype=torch.bfloat16,
                    )
                except Exception as e:
                    logger.warning(
                        "TTS load on %s failed (%s), retrying on CPU...", self.device, e
                    )
                    self.device = "cpu"
                    self.model = Qwen3TTSModel.from_pretrained(
                        model_path,
                        torch_dtype=torch.float32,
                        low_cpu_mem_usage=False,
                    )

        self._current_model_size = model_size
        self.model_size = model_size
        logger.info("TTS model %s loaded successfully", model_size)

    def unload_model(self):
        """Unload the model to free memory."""
        if self.model is not None:
            del self.model
            self.model = None
            self._current_model_size = None

            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            logger.info("TTS model unloaded")

    async def create_voice_prompt(
        self,
        audio_path: str,
        reference_text: str,
        use_cache: bool = True,
    ) -> Tuple[dict, bool]:
        """
        Create voice prompt from reference audio.

        Args:
            audio_path: Path to reference audio file
            reference_text: Transcript of reference audio
            use_cache: Whether to use cached prompt if available

        Returns:
            Tuple of (voice_prompt_dict, was_cached)
        """
        await self.load_model_async(None)

        # Check cache if enabled
        if use_cache:
            cache_key = get_cache_key(audio_path, reference_text)
            cached_prompt = get_cached_voice_prompt(cache_key)
            if cached_prompt is not None:
                # Cache stores as torch.Tensor but actual prompt is dict
                # Convert if needed
                if isinstance(cached_prompt, dict):
                    # For PyTorch backend, the dict should contain tensors, not file paths
                    # So we can safely return it
                    return cached_prompt, True
                elif isinstance(cached_prompt, torch.Tensor):
                    # Legacy cache format - convert to dict
                    # This shouldn't happen in practice, but handle it
                    return {"prompt": cached_prompt}, True

        def _create_prompt_sync():
            """Run synchronous voice prompt creation in thread pool."""
            return self.model.create_voice_clone_prompt(
                ref_audio=str(audio_path),
                ref_text=reference_text,
                x_vector_only_mode=False,
            )

        # Run blocking operation in thread pool
        voice_prompt_items = await asyncio.to_thread(_create_prompt_sync)

        # Cache if enabled
        if use_cache:
            cache_key = get_cache_key(audio_path, reference_text)
            cache_voice_prompt(cache_key, voice_prompt_items)

        return voice_prompt_items, False

    async def combine_voice_prompts(
        self,
        audio_paths: List[str],
        reference_texts: List[str],
    ) -> Tuple[np.ndarray, str]:
        return await _combine_voice_prompts(audio_paths, reference_texts)

    async def generate(
        self,
        text: str,
        voice_prompt: dict,
        language: str = "en",
        seed: Optional[int] = None,
        instruct: Optional[str] = None,
    ) -> Tuple[np.ndarray, int]:
        """
        Generate audio from text using voice prompt.

        Args:
            text: Text to synthesize
            voice_prompt: Voice prompt dictionary from create_voice_prompt
            language: Language code (en or zh)
            seed: Random seed for reproducibility
            instruct: Natural language instruction for speech delivery control

        Returns:
            Tuple of (audio_array, sample_rate)
        """
        # Load model
        await self.load_model_async(None)

        def _generate_sync():
            """Run synchronous generation in thread pool."""
            # Set seed if provided
            if seed is not None:
                torch.manual_seed(seed)
                if torch.cuda.is_available():
                    torch.cuda.manual_seed(seed)

            # Generate audio - this is the blocking operation
            wavs, sample_rate = self.model.generate_voice_clone(
                text=text,
                voice_clone_prompt=voice_prompt,
                language=LANGUAGE_CODE_TO_NAME.get(language, "auto"),
                instruct=instruct,
            )
            return wavs[0], sample_rate

        # Run blocking inference; if GPU fails at runtime, reload on CPU and retry
        try:
            audio, sample_rate = await asyncio.to_thread(_generate_sync)
        except Exception as e:
            if self.device != "cpu":
                logger.warning(
                    "TTS generate on %s failed (%s), reloading on CPU...", self.device, e
                )
                current_size = self._current_model_size or self.model_size
                self.unload_model()
                self.device = "cpu"
                await self.load_model_async(current_size)
                audio, sample_rate = await asyncio.to_thread(_generate_sync)
            else:
                raise

        return audio, sample_rate


class PyTorchSTTBackend:
    """PyTorch-based STT backend using Whisper."""

    def __init__(self, model_size: str = "base"):
        self.model = None
        self.processor = None
        self.model_size = model_size
        self.device = self._get_device()
        self.is_ov_accelerated = False

    def _get_device(self) -> str:
        """Get the best available device."""
        return get_torch_device(allow_xpu=True, allow_directml=True)

    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self.model is not None

    def _is_model_cached(self, model_size: str) -> bool:
        hf_repo = WHISPER_HF_REPOS.get(model_size, f"openai/whisper-{model_size}")
        return is_model_cached(hf_repo)

    async def load_model_async(self, model_size: Optional[str] = None):
        """
        Lazy load the Whisper model.

        Args:
            model_size: Model size (tiny, base, small, medium, large)
        """
        if model_size is None:
            model_size = self.model_size

        if self.model is not None and self.model_size == model_size:
            return

        await asyncio.to_thread(self._load_model_sync, model_size)

    # Alias for compatibility
    load_model = load_model_async

    def _load_model_sync(self, model_size: str):
        """同步載入模型：針對模型大小進行設備路由(Tiny->CPU, 其它->OV/PT)。"""
        progress_model_name = f"whisper-{model_size}"
        is_cached = self._is_model_cached(model_size)
        model_id = WHISPER_HF_REPOS.get(model_size, f"openai/whisper-{model_size}")

        with model_load_progress(progress_model_name, is_cached):
            from transformers import WhisperProcessor, WhisperForConditionalGeneration
            self.processor = WhisperProcessor.from_pretrained(model_id)

            # 1. 設備路由與加速邏輯
            # 根據 Benchmark，tiny 模型走 CPU 開銷最小；其餘模型嘗試 OpenVINO GPU/NPU
            use_ov = False
            is_tiny = "tiny" in model_size.lower()
            
            enable_npu = os.environ.get("ENABLE_EXPERIMENTAL_NPU", "0") == "1"
            
            if is_tiny:
                logger.info("Tiny model detected: using standard PyTorch CPU for optimal low-latency (Bench: RTF 0.05-0.08x)")
                use_ov = False
            else:
                try:
                    logger.info("OpenVINO: Attempting acceleration for %s (NPU Experimental: %s)", model_size, enable_npu)
                    from .ov_accelerate import get_best_ov_device, safe_load_ov_model
                    target_device = get_best_ov_device(exclude_npu=not enable_npu)
                    
                    if target_device and target_device != "CPU":
                        logger.info("OpenVINO: Found accelerator %s, routing %s...", target_device, model_size)
                        self.model = safe_load_ov_model(model_id, "stt", device=target_device)
                        self.device = "cpu"  # OV 模型內部處理設備，輸入維持在 CPU
                        self.is_ov_accelerated = True
                        use_ov = True
                    else:
                        logger.info("OpenVINO: No hardware accelerator found or forced to CPU; staying on PyTorch Native.")
                except Exception as e:
                    import traceback
                    logger.warning("OpenVINO load failed: %s", str(e))
                    logger.debug("OpenVINO Error Stack: %s", traceback.format_exc())
                    logger.info("Falling back to native PyTorch CPU mode.")

            # 2. PyTorch Fallback
            if not use_ov:
                logger.info("Loading Whisper model %s on CPU (Standard PyTorch)...", model_size)
                self.model = WhisperForConditionalGeneration.from_pretrained(model_id)
                self.model.to("cpu")
                self.device = "cpu"
                self.is_ov_accelerated = False

        self.model_size = model_size
        logger.info("Whisper model %s loaded successfully (OV: %s)", model_size, self.is_ov_accelerated)

    def unload_model(self):
        """Unload the model to free memory."""
        if self.model is not None:
            del self.model
            del self.processor
            self.model = None
            self.processor = None

            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            logger.info("Whisper model unloaded")

    async def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        model_size: Optional[str] = None,
    ) -> str:
        """
        Transcribe audio to text.

        Args:
            audio_path: Path to audio file
            language: Optional language hint
            model_size: Optional model size override

        Returns:
            Transcribed text
        """
        await self.load_model_async(model_size)

        def _transcribe_sync():
            """Run synchronous transcription in thread pool."""
            # Load audio
            audio, sr = load_audio(audio_path, sample_rate=16000)

            # Process audio
            inputs = self.processor(
                audio,
                sampling_rate=16000,
                return_tensors="pt",
            )
            inputs = inputs.to(self.device)

            # Generate transcription
            # If language is provided, force it; otherwise let Whisper auto-detect
            generate_kwargs = {}
            if language:
                forced_decoder_ids = self.processor.get_decoder_prompt_ids(
                    language=language,
                    task="transcribe",
                )
                generate_kwargs["forced_decoder_ids"] = forced_decoder_ids

            with torch.no_grad():
                predicted_ids = self.model.generate(
                    inputs["input_features"],
                    **generate_kwargs,
                )

            # Decode
            transcription = self.processor.batch_decode(
                predicted_ids,
                skip_special_tokens=True,
            )[0]

            return transcription.strip()

        # Run blocking transcription; if OV inference fails at runtime, reload on CPU
        try:
            return await asyncio.to_thread(_transcribe_sync)
        except Exception as e:
            if self.is_ov_accelerated:
                logger.warning(
                    "OV STT runtime inference failed (%s), reloading with PyTorch CPU...", e
                )
                self.unload_model()
                self.is_ov_accelerated = False
                target_size = model_size or self.model_size
                await asyncio.to_thread(self._load_model_sync, target_size)
                return await asyncio.to_thread(_transcribe_sync)
            raise
