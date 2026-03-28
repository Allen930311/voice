import httpx
import asyncio
import json
import sys
import argparse
from pathlib import Path

# Configuration
BASE_URL = "http://127.0.0.1:17493"
VOICE_LIBRARY_PATH = Path(r"C:\Users\Allen\.gemini\antigravity\global_skills\voicebox-tts\voice-library.json")
DEFAULT_OUTPUT_DIR = Path(r"c:\Users\Allen\OneDrive\Desktop\Voicebox\output")

# Ensure stdout uses UTF-8
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def load_voice_library():
    if not VOICE_LIBRARY_PATH.exists():
        print(f"Error: Voice library not found at {VOICE_LIBRARY_PATH}")
        return None
    with open(VOICE_LIBRARY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_profile_by_name(library, name):
    for voice in library.get("voices", []):
        if name.lower() in voice["name"].lower():
            return voice
    return None

async def generate_speech(profile, text, output_path):
    async with httpx.AsyncClient(timeout=600) as client:
        print(f"Connecting to Voicebox at {BASE_URL}...")
        print(f"Using Voice: {profile['name']} (ID: {profile['profile_id']})")
        print(f"Text: {text}")

        try:
            # 1. Trigger Generation
            r = await client.post(f"{BASE_URL}/generate", json={
                "profile_id": profile["profile_id"],
                "text": text,
                "language": profile.get("language", "zh"),
                "engine": profile.get("engine", "qwen"),
                "model_size": "1.7B"
            })
            r.raise_for_status()
            gen_id = r.json()["id"]
            print(f"Generation started. ID: {gen_id}")

            # 2. Polling
            print("Processing...", end="", flush=True)
            for _ in range(120):
                await asyncio.sleep(3)
                print(".", end="", flush=True)
                r = await client.get(f"{BASE_URL}/history/{gen_id}")
                status_data = r.json()
                if status_data["status"] == "completed":
                    print("\nDone!")
                    break
                elif status_data["status"] == "failed":
                    print(f"\nError: {status_data.get('error', 'Unknown error')}")
                    return False
            else:
                print("\nTimeout.")
                return False

            # 3. Download
            print(f"Saving to: {output_path}")
            r = await client.get(f"{BASE_URL}/audio/{gen_id}")
            r.raise_for_status()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(r.content)
            print("Success!")
            return True

        except Exception as e:
            print(f"\nFailed: {e}")
            return False

async def main():
    parser = argparse.ArgumentParser(description="Voicebox simple CLI generator")
    parser.add_argument("text", help="Text to speak")
    parser.add_argument("--voice", default="解說男聲", help="Voice name keyword (default: 解說男聲)")
    parser.add_argument("--out", help="Output file path")
    
    args = parser.parse_args()

    library = load_voice_library()
    if not library: return

    profile = get_profile_by_name(library, args.voice)
    if not profile:
        print(f"Error: Voice '{args.voice}' not found in library.")
        print("Available voices:")
        for v in library.get("voices", []):
            print(f"- {v['name']}")
        return

    ext = ".wav"
    filename = f"output_{Path(profile['name']).stem}_{asyncio.get_event_loop().time()}.wav"
    output_path = Path(args.out) if args.out else DEFAULT_OUTPUT_DIR / filename

    await generate_speech(profile, args.text, output_path)

if __name__ == "__main__":
    asyncio.run(main())
