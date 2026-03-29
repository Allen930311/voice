"""
Qwen TTS DirectML GPU 推理速度實測
=====================================
使用 torch-directml (venv312) 在 Intel Arc iGPU 上跑 Qwen3-TTS 完整推理，
對比 CPU baseline，量化真實加速倍率。

執行方式（必須使用 venv312）：
    $gpu_python = "C:/Users/Allen/AppData/Local/voicebox-venv312/Scripts/python.exe"
    & $gpu_python test_qwen_directml.py

    # 或指定模型大小：
    & $gpu_python test_qwen_directml.py --model 0.6B
    & $gpu_python test_qwen_directml.py --model 1.7B

注意事項：
  - DirectML 不支援 bfloat16 → 統一使用 float16
  - Qwen3TTSModel 使用 .to(device) 移至 DirectML（不用 device_map）
  - 第一次推理含 JIT 暖機時間，第 2-3 次才是穩態速度
"""

import argparse
import sys
import time
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parent
OUT_DIR = ROOT / "output" / "directml_bench"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 讓 backend import 正常運作
BACKEND_DIR = ROOT / "voicebox" / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(BACKEND_DIR.parent) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR.parent))

SAMPLE_WAV   = ROOT / "sample" / "sample.wav"
REF_TEXT     = "This is a sample voice reference for voice cloning."
TEST_TEXT_ZH = "在那風雲變幻的年代，一個男人站在命運的十字路口，他的選擇將改變整個世界的走向。"
TEST_TEXT_EN = "In those turbulent times, a man stood at the crossroads of fate, his choice about to change the world."
N_RUNS_CPU   = 1   # CPU 只跑 1 次（純 baseline，太慢不值得跑多次）
N_RUNS_DML   = 3   # DirectML 跑 3 次（第 1 次暖機，後 2 次穩態）


# ── 工具 ──────────────────────────────────────────────────────────────────────

def _save_wav(audio: np.ndarray, sr: int, path: Path):
    a = np.clip(audio * 32767, -32768, 32767).astype(np.int16)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1); wf.setsampwidth(2)
        wf.setframerate(sr); wf.writeframes(a.tobytes())


def _check_prereqs() -> bool:
    if not SAMPLE_WAV.exists():
        print(f"  [ERROR] sample.wav not found: {SAMPLE_WAV}")
        print("  Please place a reference voice file at sample/sample.wav")
        return False

    try:
        import torch_directml
        n = torch_directml.device_count()
        if n == 0:
            print("  [ERROR] torch_directml installed but no DML devices found.")
            return False
        print(f"  torch_directml: {n} device(s)")
        for i in range(n):
            print(f"    [{i}] {torch_directml.device_name(i)}")
    except ImportError:
        print("  [ERROR] torch_directml not installed.")
        print("  Run:  pip install torch-directml")
        print("  This test requires venv312 (Python 3.12 + torch-directml).")
        return False

    try:
        from qwen_tts import Qwen3TTSModel  # noqa: F401
    except ImportError as e:
        print(f"  [ERROR] qwen_tts not found: {e}")
        print("  Run:  pip install git+https://github.com/QwenLM/Qwen3-TTS.git")
        return False

    return True


def _get_model_path(model_size: str) -> str:
    return {
        "0.6B": "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
        "1.7B": "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
    }[model_size]


# ── 推理計時器 ─────────────────────────────────────────────────────────────────

def bench_device(model, voice_prompt, device_label: str, n_runs: int, model_size: str,
                 lang: str = "zh", extra_gen_kwargs: dict = None):
    """
    在已載入的 model 上執行 n_runs 次推理並計時。
    回傳 {"label", "times", "avg", "audios"}
    """
    from qwen_tts import Qwen3TTSModel  # noqa: F401
    from backend.backends import LANGUAGE_CODE_TO_NAME

    test_text = TEST_TEXT_ZH if lang == "zh" else TEST_TEXT_EN
    times = []
    audios = []

    for i in range(n_runs):
        label = "warm-up" if i == 0 else f"run {i+1}/{n_runs}"
        print(f"    [{device_label}] {label}… ", end="", flush=True)

        gen_kwargs = {"max_new_tokens": 512}  # 限制生成長度
        if extra_gen_kwargs:
            gen_kwargs.update(extra_gen_kwargs)
        t = time.perf_counter()
        wavs, sr = model.generate_voice_clone(
            text=test_text,
            voice_clone_prompt=voice_prompt,
            language=LANGUAGE_CODE_TO_NAME.get(lang, "auto"),
            **gen_kwargs,
        )
        elapsed = time.perf_counter() - t

        audio = wavs[0]
        audio_duration = len(audio) / sr
        times.append(elapsed)
        audios.append((audio, sr))
        print(f"{elapsed:.2f}s  (audio={audio_duration:.1f}s)")

        out = OUT_DIR / f"qwen{model_size}_{device_label.lower()}_run{i+1}.wav"
        _save_wav(audio, sr, out)

    # 第 1 次為暖機，取後面幾次平均；只有 1 次時直接用該次
    stable = times[1:] if len(times) > 1 else times
    avg = sum(stable) / len(stable)
    return {"label": device_label, "all_times": times, "avg": avg, "warm_ms": times[0],
            "only_one": len(times) == 1}


# ── 主流程 ────────────────────────────────────────────────────────────────────

def main(model_size: str):
    import torch
    import torch_directml
    from qwen_tts import Qwen3TTSModel

    model_path = _get_model_path(model_size)
    dml_device = torch_directml.device(0)

    print(f"\n{'='*64}")
    print(f"  Qwen TTS {model_size} DirectML GPU 推理速度實測")
    print(f"{'='*64}")
    print(f"  模型：{model_path}")
    print(f"  DirectML 裝置：{torch_directml.device_name(0)}")
    print(f"  CPU 推理次數：{N_RUNS_CPU}（baseline 只跑一次）")
    print(f"  DirectML 推理次數：{N_RUNS_DML}（第1次暖機，後{N_RUNS_DML-1}次穩態）")
    print(f"  輸出目錄：{OUT_DIR}")

    results = []

    # ── 1. CPU Baseline ────────────────────────────────────────────────────────
    print(f"\n{'-'*64}")
    print(f"  [CPU] 載入 Qwen TTS {model_size}… ", end="", flush=True)

    t0 = time.perf_counter()
    try:
        cpu_model = Qwen3TTSModel.from_pretrained(
            model_path,
            dtype=torch.float32,
            low_cpu_mem_usage=True,
        )
        try:
            cpu_model.eval()
        except AttributeError:
            pass  # Qwen3TTSModel is not a plain nn.Module
    except Exception as e:
        print(f"FAILED: {e}")
        return
    load_s = time.perf_counter() - t0
    print(f"  {load_s:.1f}s")

    print(f"  [CPU] 建立 voice prompt… ", end="", flush=True)
    t0 = time.perf_counter()
    try:
        voice_prompt_cpu = cpu_model.create_voice_clone_prompt(
            ref_audio=str(SAMPLE_WAV),
            ref_text=REF_TEXT,
            x_vector_only_mode=False,
        )
    except Exception as e:
        print(f"FAILED: {e}")
        return
    vp_s = time.perf_counter() - t0
    print(f"  {vp_s:.2f}s")

    with torch.no_grad():
        cpu_result = bench_device(cpu_model, voice_prompt_cpu, "CPU", N_RUNS_CPU, model_size)
    results.append(cpu_result)
    del cpu_model  # voice_prompt_cpu is a separate list of VoiceClonePromptItem — still alive

    # Keep voice_prompt_cpu alive for DirectML reuse (avoids speech_tokenizer DirectML issues)
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # ── 2. DirectML — LLM only (float32) ──────────────────────────────────────
    # Strategy:
    #   - speech_tokenizer + speaker_encoder have DirectML-incompatible ops:
    #       * replication_pad1d (float16 only) → Mimi encoder
    #       * version_counter error under inference_mode → speaker_encoder conv1d
    #   - Solution: move only the LLM transformer to DirectML, keep audio codecs on CPU
    #   - Reuse voice_prompt_cpu (already built on CPU) — skip create_voice_clone_prompt
    #   - generate() internally moves ref_code to codes.device (DirectML) via .to()
    print(f"\n{'-'*64}")
    print(f"  [DirectML] 載入 Qwen TTS {model_size} (LLM on GPU, audio codecs on CPU)… ", end="", flush=True)

    dml_result = None
    t0 = time.perf_counter()
    try:
        dml_model = Qwen3TTSModel.from_pretrained(
            model_path,
            dtype=torch.float32,
            low_cpu_mem_usage=True,
        )
        # Move entire model to DirectML first, then move audio sub-modules back to CPU.
        # Qwen3TTSForConditionalGeneration contains:
        #   - main LLM transformer  → keep on DirectML
        #   - speech_tokenizer      → Qwen3TTSTokenizer wrapper (speech_tokenizer.model is the nn.Module)
        #   - speaker_encoder       → Qwen3TTSSpeakerEncoder (nn.Module, supports .to())
        dml_model.model = dml_model.model.to(dml_device)
        # speech_tokenizer is a wrapper — move its inner nn.Module back to CPU
        dml_model.model.speech_tokenizer.model  = dml_model.model.speech_tokenizer.model.to("cpu")
        dml_model.model.speech_tokenizer.device = "cpu"
        # speaker_encoder is a plain nn.Module
        if dml_model.model.speaker_encoder is not None:
            dml_model.model.speaker_encoder = dml_model.model.speaker_encoder.to("cpu")
        dml_model.device = dml_device
        load_s_dml = time.perf_counter() - t0
        print(f"  {load_s_dml:.1f}s")

        # Reuse voice_prompt built on CPU — no need to re-create on DirectML
        print(f"  [DirectML] 重用 CPU voice prompt（跳過 speech_tokenizer）")

        with torch.no_grad():
            # DirectML breaks on int-tensor ops (torch.gather, torch.cat) in generation loop.
            # do_sample=False uses greedy decoding → minimal logits processing, avoids gather.
            dml_result = bench_device(dml_model, voice_prompt_cpu, "DirectML", N_RUNS_DML, model_size,
                                      extra_gen_kwargs={
                                          "do_sample": False,
                                          "repetition_penalty": 1.0,
                                          "subtalker_dosample": False,
                                      })
        results.append(dml_result)

        del dml_model

    except Exception as e:
        load_s_dml = time.perf_counter() - t0
        print(f"\n  [DirectML] FAILED after {load_s_dml:.1f}s: {e}")
        import traceback
        traceback.print_exc()

    # ── 結果表格 ───────────────────────────────────────────────────────────────
    print(f"\n{'='*64}")
    print(f"  Qwen TTS {model_size} 推理速度結果（穩態平均，排除第1次暖機）")
    print(f"{'='*64}")
    print(f"  {'裝置':<14} {'單次/暖機(s)':<16} {'穩態avg(s)':<14} {'vs CPU'}")
    print(f"  {'-'*58}")

    cpu_avg = next((r["avg"] for r in results if r["label"] == "CPU"), None)
    for r in results:
        warm = f"{r['warm_ms']:.2f}s"
        avg  = f"{r['avg']:.2f}s"
        if r.get("only_one"):
            avg = f"{r['avg']:.2f}s (1次)"
        if cpu_avg and r["label"] != "CPU":
            ratio = f"{cpu_avg / r['avg']:.2f}x" if r["avg"] > 0 else "-"
        elif r["label"] == "CPU":
            ratio = "1.00x (baseline)"
        else:
            ratio = "-"
        print(f"  {r['label']:<14} {warm:<16} {avg:<14} {ratio}")

    if dml_result and cpu_avg:
        speedup = cpu_avg / dml_result["avg"]
        print(f"\n  結論：DirectML 加速 {speedup:.2f}x")
        if speedup >= 5.0:
            print("  -> 顯著加速！建議在生產環境啟用 DirectML")
        elif speedup >= 2.0:
            print("  -> 有效加速，值得在 GPU 路徑優先啟用")
        elif speedup >= 1.0:
            print("  -> 輕微加速，DirectML 開銷與計算收益相當")
        else:
            print("  -> DirectML 比 CPU 慢（記憶體傳輸 overhead 超過計算收益）")
            print("  -> 建議維持 CPU 推理，或改試 OpenVINO GPU 路徑")

    print(f"\n  音訊輸出：{OUT_DIR}")
    print(f"{'='*64}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Qwen TTS DirectML GPU benchmark")
    parser.add_argument("--model", choices=["0.6B", "1.7B"], default="0.6B",
                        help="Model size to test (default: 0.6B)")
    args = parser.parse_args()

    print("\n=== 環境檢查 ===")
    if not _check_prereqs():
        sys.exit(1)

    main(args.model)
