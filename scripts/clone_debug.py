import httpx
import asyncio
from pathlib import Path

BASE_URL = "http://127.0.0.1:17493"
WAV_PATH = Path(r"c:\Users\Allen\OneDrive\Desktop\Voicebox\extra_320k_converted.wav")

async def main():
    async with httpx.AsyncClient(timeout=300) as c:
        try:
            print("Fetching profiles...")
            r = await c.get(f"{BASE_URL}/profiles")
            profiles = r.json()
            pid = next((p["id"] for p in profiles if p["name"] == "Germany WW2 Shorts"), None)
            
            if not pid:
                print("Profile not found, creating...")
                r = await c.post(f"{BASE_URL}/profiles", json={"name": "Germany WW2 Shorts", "language": "en"})
                pid = r.json()["id"]
                
            print(f"Profile ID: {pid}. Transcribing...")
            with open(WAV_PATH, "rb") as f:
                r = await c.post(
                    f"{BASE_URL}/transcribe", 
                    data={"language":"en", "model":"base"}, 
                    files={"file":("sample.wav", f, "audio/wav")}
                )
                r.raise_for_status()
                text = r.json().get("text", "")
            print(f"Text: {text}")
            
            print("Uploading Sample...")
            with open(WAV_PATH, "rb") as f:
                r = await c.post(
                    f"{BASE_URL}/profiles/{pid}/samples", 
                    data={"reference_text": text}, 
                    files={"file":("sample.wav", f, "audio/wav")}
                )
                r.raise_for_status()
            print("Sample uploaded successfully.")
            
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error: {e.response.status_code}")
            print(f"Details: {e.response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
