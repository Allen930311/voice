import httpx
import json
import asyncio
from pathlib import Path

BASE_URL = "http://127.0.0.1:17493"
WAV_PATH = Path(r"c:\Users\Allen\OneDrive\Desktop\Voicebox\extra_320k_converted.wav")
PROFILE_NAME = "Germany WW2 Shorts"

async def main():
    async with httpx.AsyncClient(timeout=300) as c:
        # Create Profile
        print("1. Creating Profile...")
        r = await c.post(f"{BASE_URL}/profiles", json={"name": PROFILE_NAME, "language": "en"})
        r.raise_for_status()
        pid = r.json()["id"]
        print(f"Profile ID: {pid}")

        # Transcribe
        print("2. Transcribing...")
        with open(WAV_PATH, "rb") as f:
            r = await c.post(
                f"{BASE_URL}/transcribe", 
                data={"language":"en", "model":"base"}, 
                files={"file":("sample.wav", f, "audio/wav")}
            )
            r.raise_for_status()
            text = r.json().get("text", "")
        print(f"Transcribed Text: {text}")

        # Add Sample
        print("3. Uploading Sample...")
        with open(WAV_PATH, "rb") as f:
            r = await c.post(
                f"{BASE_URL}/profiles/{pid}/samples", 
                data={"reference_text": text}, 
                files={"file":("sample.wav", f, "audio/wav")}
            )
            r.raise_for_status()
        print("Done! Cloned successfully.")

        # output result
        result = {
            "profile_id": pid,
            "text": text
        }
        with open("c:\\Users\\Allen\\OneDrive\\Desktop\\Voicebox\\clone_result.json", "w", encoding="utf-8") as rf:
            json.dump(result, rf)

if __name__ == "__main__":
    asyncio.run(main())
