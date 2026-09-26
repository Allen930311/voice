import httpx
import time
import sys
from pathlib import Path

BASE_URL = "http://127.0.0.1:17493"
PROFILE_ID = "4cab8f9d-8e67-4dae-9c30-ff0a770823c5"
TEXT = "i am a women"
OUTPUT_PATH = r"C:\Users\Allen\OneDrive\Desktop\Voicebox\output\i_am_a_women.wav"

def generate():
    with httpx.Client(timeout=300.0) as client:
        # 1. Trigger generation
        payload = {
            "profile_id": PROFILE_ID,
            "text": TEXT,
            "language": "en",
            "engine": "qwen",
            "normalize": True
        }
        print(f"Triggering generation for: {TEXT}")
        r = client.post(f"{BASE_URL}/generate", json=payload)
        r.raise_for_status()
        gen = r.json()
        gen_id = gen["id"]
        print(f"Generation started. ID: {gen_id}")

        # 2. Poll status
        for _ in range(120):
            time.sleep(5)
            r2 = client.get(f"{BASE_URL}/history/{gen_id}")
            r2.raise_for_status()
            status_data = r2.json()
            status = status_data.get("status", "pending")
            print(f"Status: {status} (duration: {status_data.get('duration', 0):.1f}s)")
            
            if status == "failed":
                print(f"Error: {status_data.get('error')}")
                return
            
            if (status == "completed" 
                and status_data.get("duration", 0) > 0 
                and status_data.get("audio_path", "")):
                print("Generation completed successfully.")
                break
        else:
            print("Timeout waiting for generation.")
            return

        # 3. Download
        print(f"Downloading to: {OUTPUT_PATH}")
        r3 = client.get(f"{BASE_URL}/audio/{gen_id}")
        r3.raise_for_status()
        out = Path(OUTPUT_PATH)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(r3.content)
        print("Success!")

if __name__ == "__main__":
    generate()
