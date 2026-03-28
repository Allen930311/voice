"""
Intel Arc GPU vs CPU 效能基準測試
=================================
使用 Qwen TTS 0.6B 測試 CPU vs XPU/DirectML 推理速度差異。

使用方式：
    cd voicebox
    python ../test_intel_arc.py

前置需求（擇一）：
    # Intel Arc 方案 A：XPU (需要 IPEX)
    pip install intel_extension_for_pytorch

    # Intel Arc 方案 B：DirectML (Windows 內建驅動即可)
    pip install torch-directml
"""

import asyncio
import sys
import time
from pathlib import Path

import numpy as np

# ── 路徑設定 ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
BACKEND_ROOT = ROOT / "voicebox" / "backend"
sys.path.insert(0, str(BACKEND_ROOT.parent))  # 讓 import backend.* 可用

SAMPLE_WAV = ROOT / "sample" / "sample.wav"
OUT_DIR = ROOT / "output" / "arc_bench"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TEST_TEXT = "在那風雲變幻的年代，一個男人站在命運的十字路口，他的選擇將改變整個世界的走向。"
REFERENCE_TEXT = "This is a sample voice reference for voice cloning."
MODEL_SIZE = "0.6B"  # 用最小模型加快測試速度
N_RUNS = 2           # 每個 device 跑幾次（取平均）

# ── 裝置偵測 ──────────────────────────────────────────────────────────────────

def detect_devices() -> dict:
    """回傳可用裝置清單"""
    import torch
    result = {"cpu": True, "cuda": False, "xpu": False, "directml": False}

    if torch.cuda.is_available():
        result["cuda"] = True

    try:
        import intel_extension_for_pytorch as ipex  # noqa: F401
        if hasattr(torch, "xpu") and torch.xpu.is_available():
            result["xpu"] = True
    except ImportError:
        pass

    try:
        import torch_directml
        if torch_directml.device_count() > 0:
            result["directml"] = True
    except ImportError:
        pass

    return result


def pick_gpu_device(devices: dict) -> str | None:
    """選出最佳 GPU 裝置"""
    if devices["cuda"]:
        return "cuda"
    if devices["xpu"]:
        return "xpu"
    if devices["directml"]:
        import torch_directml
        return str(torch_directml.device(0))
    return None


# ── Backend 包裝（強制指定 device）────────────────────────────────────────────

def make_backend(forced_device: str):
    """建立強制使用指定 device 的 PyTorchTTSBackend"""
    from backend.backends.pytorch_backend import PyTorchTTSBackend

    class _ForcedDeviceBackend(PyTorchTTSBackend):
        def _get_device(self):
            return forced_device

    return _ForcedDeviceBackend(model_size=MODEL_SIZE)


# ── 核心基準函式 ───────────────────────────────────────────────────────────────

async def run_benchmark(device: str, label: str) -> dict:
    """
    在指定 device 上跑 N_RUNS 次推理，回傳計時結果。

    Returns:
        {
            "device": str,
            "label": str,
            "load_time": float,       # 模型載入秒數（含 voice prompt）
            "times": list[float],     # 各次推理秒數
            "avg": float,
            "min": float,
            "output_files": list[Path],
        }
    """
    print(f"\n{'='*60}")
    print(f"  測試裝置：{label}  ({device})")
    print(f"{'='*60}")

    backend = make_backend(device)

    # ── 載入模型 ──
    print("  [1/3] 載入模型中…", end="", flush=True)
    t0 = time.perf_counter()
    await backend.load_model_async(MODEL_SIZE)
    print(f" done ({time.perf_counter()-t0:.1f}s)")

    # ── 建立 voice prompt ──
    print("  [2/3] 建立 voice prompt…", end="", flush=True)
    t1 = time.perf_counter()
    if not SAMPLE_WAV.exists():
        raise FileNotFoundError(f"找不到 sample：{SAMPLE_WAV}")
    voice_prompt, _ = await backend.create_voice_prompt(str(SAMPLE_WAV), REFERENCE_TEXT)
    load_time = time.perf_counter() - t0
    print(f" done ({time.perf_counter()-t1:.1f}s)")

    # ── 推理計時 ──
    print(f"  [3/3] 推理 {N_RUNS} 次…")
    times = []
    output_files = []

    for i in range(N_RUNS):
        print(f"    run {i+1}/{N_RUNS}… ", end="", flush=True)
        t = time.perf_counter()
        audio, sr = await backend.generate(
            text=TEST_TEXT,
            voice_prompt=voice_prompt,
            language="zh",
            seed=42,
        )
        elapsed = time.perf_counter() - t
        times.append(elapsed)
        print(f"{elapsed:.2f}s  ({len(audio)/sr:.1f}s 音訊)")

        # 儲存音訊
        out_path = OUT_DIR / f"{label.lower().replace(' ', '_')}_run{i+1}.wav"
        _save_wav(audio, sr, out_path)
        output_files.append(out_path)

    avg = sum(times) / len(times)
    print(f"  平均：{avg:.2f}s  最快：{min(times):.2f}s")

    # 卸載模型、釋放記憶體
    backend.unload_model()

    return {
        "device": device,
        "label": label,
        "load_time": load_time,
        "times": times,
        "avg": avg,
        "min": min(times),
        "output_files": output_files,
    }


def _save_wav(audio: np.ndarray, sr: int, path: Path):
    """儲存 numpy array 為 WAV 檔"""
    import struct, wave
    audio_int16 = np.clip(audio * 32767, -32768, 32767).astype(np.int16)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(audio_int16.tobytes())


# ── 主流程 ────────────────────────────────────────────────────────────────────

async def main():
    print("\n🔍 偵測可用裝置…")
    devices = detect_devices()
    for name, avail in devices.items():
        status = "✅" if avail else "❌"
        print(f"  {status} {name}")

    gpu_device = pick_gpu_device(devices)
    if gpu_device is None:
        print("\n⚠️  未偵測到 GPU（XPU / DirectML / CUDA）。")
        print("   請先安裝 intel_extension_for_pytorch 或 torch-directml。")
        sys.exit(1)

    results = []

    # CPU 基準
    cpu_result = await run_benchmark("cpu", "CPU")
    results.append(cpu_result)

    # GPU 基準
    gpu_label = gpu_device.upper().split(":")[0]  # "XPU", "CUDA", "PRIVATEUSEONE"
    gpu_result = await run_benchmark(gpu_device, gpu_label)
    results.append(gpu_result)

    # ── 比較表格 ──────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("  📊 結果比較")
    print(f"{'='*60}")
    print(f"  {'裝置':<12} {'載入(s)':<12} {'平均推理(s)':<14} {'最快(s)':<10} {'加速比'}")
    print(f"  {'-'*58}")
    cpu_avg = results[0]["avg"]
    for r in results:
        speedup = f"{cpu_avg / r['avg']:.2f}x" if r["avg"] > 0 else "N/A"
        print(f"  {r['label']:<12} {r['load_time']:<12.1f} {r['avg']:<14.2f} {r['min']:<10.2f} {speedup}")

    print(f"\n  📁 輸出音訊已存到：{OUT_DIR}")
    for r in results:
        for f in r["output_files"]:
            print(f"     {f.name}")

    # ── 結論 ──────────────────────────────────────────────────────────────────
    speedup_ratio = cpu_avg / results[1]["avg"]
    print(f"\n{'='*60}")
    if speedup_ratio >= 1.5:
        print(f"  ✅ Intel Arc ({gpu_label}) 加速效果顯著：{speedup_ratio:.1f}x 速度提升")
        print("     建議：執行全面替換（改各引擎的 _get_device 呼叫）")
    elif speedup_ratio >= 1.1:
        print(f"  🟡 Intel Arc ({gpu_label}) 有小幅提升：{speedup_ratio:.1f}x")
        print("     建議：可以嘗試更大模型（1.7B）再測試一次")
    else:
        print(f"  ❌ Intel Arc ({gpu_label}) 無明顯加速（{speedup_ratio:.2f}x）")
        print("     可能原因：模型太小、記憶體傳輸開銷 > 計算收益")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
