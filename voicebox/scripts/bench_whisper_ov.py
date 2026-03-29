import sys
import time
import torch
import numpy as np
import logging
from pathlib import Path
import os
import traceback

# Disable progress bars for cleaner logs
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

# Set logging level
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("whisper_bench")

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

# Test audio path
AUDIO_PATH = Path(r"C:\Users\Allen\OneDrive\Desktop\Voicebox\sample\sample.wav")
if not AUDIO_PATH.exists():
    print(f"Error: Audio file not found at {AUDIO_PATH}")
    sys.exit(1)

# Models to test
MODELS = ["tiny", "base", "small"]
N_RUNS = 3

def load_audio(path: str, sample_rate: int = 16000):
    import librosa
    audio, sr = librosa.load(path, sr=sample_rate)
    return audio, len(audio) / sr

def bench_whisper_pt(model_id: str, device: str):
    from transformers import WhisperProcessor, WhisperForConditionalGeneration
    
    model_name = f"openai/whisper-{model_id}"
    logger.info(f"--- PyTorch {model_id} on {device} ---")
    
    processor = WhisperProcessor.from_pretrained(model_name)
    model = WhisperForConditionalGeneration.from_pretrained(model_name).to(device)
    
    audio, duration = load_audio(str(AUDIO_PATH))
    inputs = processor(audio, sampling_rate=16000, return_tensors="pt").to(device)
    input_features = inputs["input_features"]
    
    # Warmup
    with torch.no_grad():
        model.generate(input_features)
    
    times = []
    for i in range(N_RUNS):
        start = time.perf_counter()
        with torch.no_grad():
            predicted_ids = model.generate(input_features, max_length=128)
            processor.batch_decode(predicted_ids, skip_special_tokens=True)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        logger.info(f"  Run {i+1}: {elapsed:.2f}s")
        
    return {
        "device": f"{device}-PT",
        "avg_s": sum(times) / len(times),
        "min_s": min(times),
        "duration": duration
    }

def bench_whisper_ov(model_id: str, device_id: str):
    from transformers import WhisperProcessor
    from optimum.intel import OVModelForSpeechSeq2Seq
    
    model_name = f"openai/whisper-{model_id}"
    ov_dir = (PROJECT_ROOT / f"whisper-{model_id}-ov").resolve()
    
    # Check if pre-exported directory exists
    if ov_dir.exists():
        load_path = str(ov_dir)
        is_export = False
        logger.info(f"--- OpenVINO {model_id} on {device_id} (Local IR: {ov_dir}) ---")
    else:
        load_path = model_name
        is_export = True
        logger.info(f"--- OpenVINO {model_id} on {device_id} (Auto Export, checked: {ov_dir}) ---")
    
    processor = WhisperProcessor.from_pretrained(model_name)
    model = OVModelForSpeechSeq2Seq.from_pretrained(
        load_path,
        export=is_export,
        device=device_id,
        compile=True
    )
    
    audio, duration = load_audio(str(AUDIO_PATH))
    inputs = processor(audio, sampling_rate=16000, return_tensors="pt")
    
    # Warmup
    model.generate(inputs["input_features"])
    
    times = []
    for i in range(N_RUNS):
        start = time.perf_counter()
        model.generate(inputs["input_features"])
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        logger.info(f"  Run {i+1}: {elapsed:.2f}s")
        
    return {
        "device": f"{device_id}-OV",
        "avg_s": sum(times) / len(times),
        "min_s": min(times),
        "duration": duration
    }

def print_results(all_results):
    results_list = []
    for model_id, results in all_results.items():
        for r in results:
            rtf = r["duration"] / r["avg_s"]
            results_list.append({
                "model": model_id,
                "device": r["device"],
                "avg_time": r["avg_s"],
                "rtf": rtf
            })

    print("\n" + "="*60)
    print("WHISPER BENCHMARK RESULTS")
    print("="*60)
    print(f"{'Model':<10} | {'Device':<15} | {'Avg Time (s)':<12} | {'RTF':<8}")
    print("-" * 60)
    for res in results_list:
        print(f"{res['model']:<10} | {res['device']:<15} | {res['avg_time']:<12.2f} | {res['rtf']:<8.2f}")
    
    # Save to file
    with open("whisper_bench_results.csv", "w") as f:
        f.write("Model,Device,AvgTime,RTF\n")
        for res in results_list:
            f.write(f"{res['model']},{res['device']},{res['avg_time']:.2f},{res['rtf']:.2f}\n")
    print("="*60 + "\nResults saved to whisper_bench_results.csv")

if __name__ == "__main__":
    all_results = {}
    
    # Find OpenVINO devices
    try:
        import openvino as ov
        core = ov.Core()
        ov_devices = core.available_devices
        logger.info(f"Available OpenVINO devices: {ov_devices}")
    except ImportError:
        ov_devices = []
    
    for model_id in MODELS:
        model_results = []
        
        # 1. PyTorch CPU
        try:
            model_results.append(bench_whisper_pt(model_id, "cpu"))
        except Exception:
            logger.error(f"PyTorch CPU failed for {model_id}:\n{traceback.format_exc()}")
            
        # OpenVINO tests
        for dev in ov_devices:
            # Skip non-relevant devices if needed, but here we test all
            try:
                model_results.append(bench_whisper_ov(model_id, dev))
            except Exception:
                logger.error(f"OpenVINO {dev} failed for {model_id}:\n{traceback.format_exc()}")
                
        all_results[model_id] = model_results
        
    print_results(all_results)
