import httpx
import os
import asyncio
from pathlib import Path

BASE_URL = "http://127.0.0.1:17493"
AUDIO_PATH = r"c:\Users\Allen\OneDrive\Desktop\Voicebox\sample.wav"

async def test_flow():
    async with httpx.AsyncClient(timeout=600) as client:
        # 1. Transcribe
        print("Transcribing...")
        with open(AUDIO_PATH, "rb") as f:
            try:
                r = await client.post(f"{BASE_URL}/transcribe", files={"file": ("sample.wav", f, "audio/wav")}, data={"language": "zh", "model": "base"})
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                print(f"Error: {e.response.status_code}")
                print(f"Detail: {e.response.text}")
                return
        ref_text = r.json().get("text", "")
        print(f"Transcription: {ref_text}")

        # 2. Create Profile
        print("Creating Profile...")
        try:
            r = await client.post(f"{BASE_URL}/profiles", json={"name": "CloneTest_01", "language": "zh", "description": "Manual Test"})
            r.raise_for_status()
            profile_id = r.json()["id"]
            print(f"Profile ID: {profile_id}")
        except httpx.HTTPStatusError as e:
            print(f"Profile Creation Error: {e.response.status_code}")
            print(f"Detail: {e.response.text}")
            return

        # 3. Add Sample
        print("Adding Sample...")
        try:
            with open(AUDIO_PATH, "rb") as f:
                r = await client.post(f"{BASE_URL}/profiles/{profile_id}/samples", files={"file": ("sample.wav", f, "audio/wav")}, data={"reference_text": ref_text})
                r.raise_for_status()
            print("Sample Added.")
        except httpx.HTTPStatusError as e:
            print(f"Add Sample Error: {e.response.status_code}")
            print(f"Detail: {e.response.text}")
            return

        # 4. Generate Speech
        print("Generating Speech...")
        gen_text = "這是一個聲音克隆測試，Voicebox 啟動成功！"
        try:
            r = await client.post(f"{BASE_URL}/generate", json={
                "profile_id": profile_id,
                "text": gen_text,
                "language": "zh",
                "engine": "qwen",
                "model_size": "1.7B"
            })
            r.raise_for_status()
            gen_id = r.json()["id"]
            print(f"Generation ID: {gen_id}")
        except httpx.HTTPStatusError as e:
            print(f"Generation Error: {e.response.status_code}")
            print(f"Detail: {e.response.text}")
            return

        # 5. Poll for completion
        print("Waiting for generation...")
        for _ in range(60):
            await asyncio.sleep(5)
            r = await client.get(f"{BASE_URL}/history/{gen_id}")
            status = r.json().get("status")
            if status == "completed":
                print("Generation Completed.")
                break
            elif status == "failed":
                print("Generation Failed.")
                return
        
        # 6. Download
        output_path = r"c:\Users\Allen\OneDrive\Desktop\Voicebox\test_output.wav"
        r = await client.get(f"{BASE_URL}/audio/{gen_id}")
        with open(output_path, "wb") as f:
            f.write(r.content)
        print(f"Output saved to: {output_path}")

if __name__ == "__main__":
    asyncio.run(test_flow())
