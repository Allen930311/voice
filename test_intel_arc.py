"""
Intel Arc / NPU vs CPU 效能基準測試（OpenVINO 原生 API 版）
=============================================================
不需要 MSVC cl.exe，直接用 ov.convert_model + ov.compile_model

裝置：
  CPU  → Intel Core Ultra 9 185H
  GPU  → Intel Arc iGPU
  NPU  → Intel AI Boost

使用方式：
    cd voicebox/backend && source venv/Scripts/activate && cd ../..
    PYTHONIOENCODING=utf-8 python test_intel_arc.py
"""

import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parent
OUT_DIR = ROOT / "output" / "arc_bench"
OUT_DIR.mkdir(parents=True, exist_ok=True)

N_RUNS    = 3     # 每個裝置跑幾次（取平均）
SEQ_LEN   = 256   # 模擬 TTS 序列長度


# ── 1. 列出 OpenVINO 裝置 ─────────────────────────────────────────────────────

def list_ov_devices():
    import openvino as ov
    core = ov.Core()
    result = []
    for d in core.available_devices:
        try:
            name = core.get_property(d, "FULL_DEVICE_NAME")
        except Exception:
            name = d
        result.append((d, name))
    return result, core


# ── 2. 建立測試模型（兩種規模）────────────────────────────────────────────────

def build_models():
    """
    返回兩個 PyTorch 模型，用於模擬 TTS 的計算量：
      - small_model : 類似 0.6B 的 MLP+Attention 規模
      - large_model : 類似 1.7B 的規模
    """
    import torch
    import torch.nn as nn

    class TTSSimModel(nn.Module):
        """模擬 TTS 解碼器的 Feed-Forward + Multi-Head Attention 計算量"""
        def __init__(self, d_model=512, nhead=8, ff_dim=2048, n_layers=8):
            super().__init__()
            enc_layer = nn.TransformerEncoderLayer(
                d_model=d_model, nhead=nhead, dim_feedforward=ff_dim,
                batch_first=True, dropout=0.0,
            )
            self.net = nn.TransformerEncoder(enc_layer, num_layers=n_layers)
            self.embed = nn.Embedding(8192, d_model)
            self.out = nn.Linear(d_model, d_model)

        def forward(self, x):
            return self.out(self.net(self.embed(x)))

    small = TTSSimModel(d_model=512, nhead=8, ff_dim=2048, n_layers=6).eval()   # ~55M params
    large = TTSSimModel(d_model=768, nhead=12, ff_dim=3072, n_layers=12).eval() # ~180M params
    return small, large


# ── 3. 轉換並跑 OpenVINO 推理 ─────────────────────────────────────────────────

def bench_ov_device(core, model_pt, device_id: str, n_runs: int, seq_len: int) -> dict:
    """
    把 PyTorch 模型轉為 OpenVINO IR，在指定裝置上推理計時。
    不需要 MSVC — 全程 Python only。
    """
    import torch
    import openvino as ov

    dummy = torch.randint(0, 8192, (1, seq_len))

    # ── 轉換 ──
    print(f"    convert→{device_id}… ", end="", flush=True)
    try:
        t0 = time.perf_counter()
        ov_model = ov.convert_model(model_pt, example_input=dummy)
        compiled  = core.compile_model(ov_model, device_id)
        compile_ms = (time.perf_counter() - t0) * 1000
        infer_req  = compiled.create_infer_request()
        print(f"compile {compile_ms:.0f}ms")
    except Exception as e:
        print(f"FAILED")
        return {"device": device_id, "error": str(e)[:80], "times_ms": [], "avg_ms": float("inf")}

    # ── 計時 ──
    times = []
    for i in range(n_runs):
        inp = {compiled.input(0): dummy.numpy()}
        t = time.perf_counter()
        infer_req.infer(inp)
        times.append((time.perf_counter() - t) * 1000)

    return {
        "device": device_id,
        "compile_ms": compile_ms,
        "times_ms": times,
        "avg_ms": sum(times) / len(times),
        "min_ms": min(times),
        "error": None,
    }


def bench_cpu_pytorch(model_pt, n_runs: int, seq_len: int) -> dict:
    """純 PyTorch CPU 基準（不走 OpenVINO）"""
    import torch
    dummy = torch.randint(0, 8192, (1, seq_len))

    # warm-up
    t0 = time.perf_counter()
    with torch.no_grad():
        model_pt(dummy)
    wu_ms = (time.perf_counter() - t0) * 1000
    print(f"    warm-up CPU… {wu_ms:.0f}ms")

    times = []
    for _ in range(n_runs):
        t = time.perf_counter()
        with torch.no_grad():
            model_pt(dummy)
        times.append((time.perf_counter() - t) * 1000)

    return {
        "device": "CPU-PT",
        "compile_ms": wu_ms,
        "times_ms": times,
        "avg_ms": sum(times) / len(times),
        "min_ms": min(times),
        "error": None,
    }


# ── 4. Qwen TTS 完整推理 ──────────────────────────────────────────────────────

def _setup_backend_path():
    """讓 voicebox backend 的 import 正常運作"""
    backend_dir = ROOT / "voicebox" / "backend"
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    # 確保 __init__.py 能相對引用
    parent = str(backend_dir.parent)
    if parent not in sys.path:
        sys.path.insert(0, parent)


async def run_tts_bench_pair():
    """
    比較 CPU vs 最佳 OV 裝置的 Qwen TTS 推理時間。
    回傳計時 dict 或 None（如果模型未下載）。
    """
    import asyncio

    sample_wav = ROOT / "sample" / "sample.wav"
    if not sample_wav.exists():
        print("  sample.wav 不存在，跳過 Phase 2")
        return []

    _setup_backend_path()

    try:
        from backend.backends.pytorch_backend import PyTorchTTSBackend
    except ImportError as e:
        print(f"  無法載入 backend（{e}），跳過 Phase 2")
        return []

    results = []
    ref_text = "This is a sample voice reference for voice cloning."
    test_text = "在那風雲變幻的年代，一個男人站在命運的十字路口，他的選擇將改變整個世界的走向。"

    for dev_label, forced_dev in [("CPU", "cpu")]:
        class _B(PyTorchTTSBackend):
            def _get_device(self):
                return forced_dev

        b = _B(model_size="0.6B")
        print(f"\n  [{dev_label}] 載入 Qwen TTS 0.6B…", end="", flush=True)
        try:
            t0 = time.perf_counter()
            await b.load_model_async("0.6B")
            vp, _ = await b.create_voice_prompt(str(sample_wav), ref_text)
            load_s = time.perf_counter() - t0
            print(f" {load_s:.1f}s")
        except Exception as e:
            print(f" FAILED: {e}")
            results.append({"label": dev_label, "error": str(e)})
            continue

        times = []
        for i in range(2):
            print(f"    run {i+1}/2… ", end="", flush=True)
            t = time.perf_counter()
            audio, sr = await b.generate(test_text, vp, language="zh", seed=42)
            elapsed = time.perf_counter() - t
            times.append(elapsed)
            print(f"{elapsed:.2f}s ({len(audio)/sr:.1f}s audio)")
            out = OUT_DIR / f"tts_{dev_label}_run{i+1}.wav"
            _save_wav(audio, sr, out)

        b.unload_model()
        results.append({
            "label": dev_label, "load_s": load_s,
            "times": times, "avg": sum(times)/len(times),
        })

    return results


def _save_wav(audio: np.ndarray, sr: int, path: Path):
    import wave
    a = np.clip(audio * 32767, -32768, 32767).astype(np.int16)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1); wf.setsampwidth(2)
        wf.setframerate(sr); wf.writeframes(a.tobytes())


# ── 5. 主流程 ─────────────────────────────────────────────────────────────────

async def main():
    import asyncio

    print("\n" + "="*62)
    print("  Intel Arc / NPU  Voicebox 加速基準測試")
    print("="*62)

    devices, core = list_ov_devices()
    print("\n可用裝置：")
    for ov_id, name in devices:
        print(f"  {ov_id:<6} -> {name}")

    # ── Phase 1：輕量 Transformer 基準 ────────────────────────────────────────
    print("\n" + "-"*62)
    print("  Phase 1-A：小型模型 (55M params, seq=256)")
    print("-"*62)
    small_model, large_model = build_models()

    results_s = []
    print("  [PyTorch CPU 基準]")
    results_s.append(bench_cpu_pytorch(small_model, N_RUNS, SEQ_LEN))

    for ov_id, _ in devices:
        print(f"  [OpenVINO {ov_id}]")
        results_s.append(bench_ov_device(core, small_model, ov_id, N_RUNS, SEQ_LEN))

    print("\n  Phase 1-B：大型模型 (180M params, seq=256)")
    print("-"*62)
    results_l = []
    print("  [PyTorch CPU 基準]")
    results_l.append(bench_cpu_pytorch(large_model, N_RUNS, SEQ_LEN))

    for ov_id, _ in devices:
        print(f"  [OpenVINO {ov_id}]")
        results_l.append(bench_ov_device(core, large_model, ov_id, N_RUNS, SEQ_LEN))

    # ── 顯示表格 ──────────────────────────────────────────────────────────────
    def print_table(results, title):
        print(f"\n  {title}")
        print(f"  {'裝置':<10} {'compile/wu':<13} {'avg(ms)':<11} {'min(ms)':<10} {'vs CPU-PT'}")
        print(f"  {'-'*56}")
        cpu_avg = next((r["avg_ms"] for r in results if r["device"] == "CPU-PT" and not r.get("error")), None)
        for r in results:
            if r.get("error"):
                print(f"  {r['device']:<10} ERR: {r['error'][:40]}")
                continue
            sp = f"{cpu_avg/r['avg_ms']:.2f}x" if cpu_avg and r["avg_ms"] > 0 else "-"
            print(f"  {r['device']:<10} {r['compile_ms']:<13.0f} {r['avg_ms']:<11.1f} {r['min_ms']:<10.1f} {sp}")

    print_table(results_s, "小型模型結果")
    print_table(results_l, "大型模型結果")

    # ── Phase 2：Qwen TTS 完整推理 ────────────────────────────────────────────
    print("\n" + "-"*62)
    print("  Phase 2：Qwen TTS 0.6B 完整推理（需模型已下載）")
    print("-"*62)
    tts_results = await run_tts_bench_pair()

    if tts_results and not any(r.get("error") for r in tts_results):
        print("\n  Qwen TTS 結果：")
        for r in tts_results:
            print(f"  {r['label']:<8} avg={r['avg']:.2f}s  (載入 {r['load_s']:.1f}s)")
        print(f"  音訊輸出：{OUT_DIR}")

    # ── 綜合建議 ──────────────────────────────────────────────────────────────
    print("\n" + "="*62)
    print("  建議")
    print("="*62)

    cpu_pt_s = next((r for r in results_s if r["device"] == "CPU-PT" and not r.get("error")), None)
    best_s   = min((r for r in results_s if not r.get("error") and r["device"] != "CPU-PT"),
                   key=lambda r: r["avg_ms"], default=None)
    best_l   = min((r for r in results_l if not r.get("error") and r["device"] != "CPU-PT"),
                   key=lambda r: r["avg_ms"], default=None)

    if best_s and cpu_pt_s:
        ratio_s = cpu_pt_s["avg_ms"] / best_s["avg_ms"]
        print(f"  小型模型：{best_s['device']} 達 {ratio_s:.2f}x 加速")

    if best_l and cpu_pt_s:
        cpu_pt_l = next((r for r in results_l if r["device"] == "CPU-PT" and not r.get("error")), None)
        if cpu_pt_l:
            ratio_l = cpu_pt_l["avg_ms"] / best_l["avg_ms"]
            print(f"  大型模型：{best_l['device']} 達 {ratio_l:.2f}x 加速")

            if ratio_l >= 2.0:
                print("\n  -> 建議全面替換（Qwen、Chatterbox、LuxTTS、TADA）")
            elif ratio_l >= 1.4:
                print("\n  -> 建議先替換 Qwen TTS + TADA（最耗時的引擎）")
            else:
                print("\n  -> 加速有限，建議先測試 1.7B 模型後再決定")

    if any(d == "NPU" for d, _ in devices):
        print("  NPU 可用：適合背景長時間推理、省電場景")

    print("="*62 + "\n")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
