import httpx
import json
import asyncio
from pathlib import Path

lib_path = Path(r"C:\Users\Allen\.gemini\antigravity\global_skills\voicebox-tts\voice-library.json")

async def main():
    lib = json.loads(lib_path.read_text(encoding="utf-8"))
    voice = next(v for v in lib["voices"] if v["name"] == "Germany WW2 Shorts")
    
    async with httpx.AsyncClient(timeout=60) as c:
        try:
            r = await c.post("http://127.0.0.1:17493/generate", json={
                "profile_id": voice["profile_id"],
                "text": "What if Germany had won World War Two? In this alternate history timeline, we explore the terrifying possibilities.",
                "language": "en",
                "engine": "qwen",
                "model_size": "1.7B"
            })
            r.raise_for_status()
            print("Successfully started generation!")
            print(json.dumps(r.json(), indent=2))
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error: {e.response.status_code}")
            print(f"Details: {e.response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
