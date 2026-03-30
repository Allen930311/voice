import argparse
import sys
import time
import wave
from pathlib import Path
import numpy as np
import torch
import torch_directml

# 1. 設置路徑
ROOT = Path("C:/Users/Allen/OneDrive/Desktop/Voicebox")
BACKEND_DIR = ROOT / "voicebox" / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(BACKEND_DIR.parent) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR.parent))

from qwen_tts import Qwen3TTSModel
from backend.backends import LANGUAGE_CODE_TO_NAME

# 2. 定義參數
SAMPLE_WAV = ROOT / "sample" / "shohei_ohtani_sample_10s.wav"
REF_TEXT = "大谷翔平の野球に対する情熱は誰にも負けない。"
OUT_FILE = ROOT / "output" / "shohei_ohtani_final.wav"
REMOTION_PUBLIC = Path("C:/Users/Allen/OneDrive/Desktop/remotion/public/narration.wav")

SCRIPT = """大家好，我是大谷翔平。現在，讓我們一起展開這段台灣環島的旅程。
首先出現在眼前的，是全世界知名的台北 101。這座標誌性的摩天大樓，象徵著這座城市的繁榮與活力。
接著，我們將沿著海岸線南下，領略太平洋的壯闊。
最後回到台北，準備好跟我一起感受這份感動了嗎？出發吧！"""

def save_wav(audio: np.ndarray, sr: int, path: Path):
    a = np.clip(audio * 32767, -32768, 32767).astype(np.int16)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1); wf.setsampwidth(2)
        wf.setframerate(sr); wf.writeframes(a.tobytes())

def main():
    print(f"--- 啟動大谷翔平語音生成 (DirectML GPU) ---")
    device = torch_directml.device(0)
    model_path = "Qwen/Qwen3-TTS-12Hz-0.6B-Base"
    
    print(f"1. 載入模型: {model_path}")
    model = Qwen3TTSModel.from_pretrained(
        model_path,
        dtype=torch.float32,
        low_cpu_mem_usage=True,
    )
    
    # 按照 test_qwen_directml.py 的成功經驗進行設備分配
    model.model = model.model.to(device)
    model.model.speech_tokenizer.model = model.model.speech_tokenizer.model.to("cpu")
    model.model.speech_tokenizer.device = "cpu"
    if model.model.speaker_encoder is not None:
        model.model.speaker_encoder = model.model.speaker_encoder.to("cpu")
    model.device = device

    print(f"2. 建立 Voice Prompt (使用大谷翔平樣本)...")
    voice_prompt = model.create_voice_clone_prompt(
        ref_audio=str(SAMPLE_WAV),
        ref_text=REF_TEXT,
    )

    print(f"3. 開始推理生成 (文字長度: {len(SCRIPT)})...")
    t0 = time.perf_counter()
    with torch.no_grad():
        wavs, sr = model.generate_voice_clone(
            text=SCRIPT,
            voice_clone_prompt=voice_prompt,
            language="Chinese",
            do_sample=False, # 穩定性優先
            repetition_penalty=1.0,
        )
    elapsed = time.perf_counter() - t0
    audio = wavs[0]
    print(f"完成！耗時: {elapsed:.2f}s, 音訊長度: {len(audio)/sr:.1f}s")

    # 4. 儲存文件
    print(f"4. 儲存至本地輸出...")
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    save_wav(audio, sr, OUT_FILE)
    
    print(f"5. 同步至 Remotion public 目錄...")
    REMOTION_PUBLIC.parent.mkdir(parents=True, exist_ok=True)
    save_wav(audio, sr, REMOTION_PUBLIC)
    
    print(f"--- 任務成功完成！ ---")

if __name__ == "__main__":
    main()
