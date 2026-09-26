import httpx
import json
import asyncio
from pathlib import Path

BASE_URL = "http://127.0.0.1:17493"
WAV_PATH = Path(r"c:\Users\Allen\OneDrive\Desktop\Voicebox\extra_15s_quiet.wav")
PID = "f9b3a288-2e86-4156-8dfd-42b70ece7283"

async def main():
    with open("c:/Users/Allen/OneDrive/Desktop/Voicebox/upload_log.txt", "w", encoding="utf-8") as log:
        async def log_print(msg):
            print(msg)
            log.write(msg + "\n")
            log.flush()

        async with httpx.AsyncClient(timeout=300) as c:
            try:
                await log_print("Transcribing...")
                with open(WAV_PATH, "rb") as f:
                    r = await c.post(
                        f"{BASE_URL}/transcribe", 
                        data={"language":"en", "model":"base"}, 
                        files={"file":("sample.wav", f, "audio/wav")}
                    )
                    r.raise_for_status()
                    text = r.json().get("text", "")
                await log_print(f"Transcribed Text: {text}")
                
                await log_print("Uploading Sample...")
                with open(WAV_PATH, "rb") as f:
                    r = await c.post(
                        f"{BASE_URL}/profiles/{PID}/samples", 
                        data={"reference_text": text}, 
                        files={"file":("sample.wav", f, "audio/wav")}
                    )
                    r.raise_for_status()
                await log_print("Sample uploaded successfully.")
                
                # verify
                r = await c.get(f"{BASE_URL}/profiles/{PID}/samples")
                r.raise_for_status()
                await log_print(f"Samples: {json.dumps(r.json(), indent=2)}")
            except httpx.HTTPStatusError as e:
                await log_print(f"HTTP Error: {e.response.status_code}")
                await log_print(f"Details: {e.response.text}")
            except Exception as e:
                await log_print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
