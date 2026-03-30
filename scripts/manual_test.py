import requests
import time
import os

BASE_URL = "http://127.0.0.1:17493"
PROFILE_ID = "f9b3a288-2e86-4156-8dfd-42b70ece7283"
TEXT = "this is not a good deal"
OUTPUT_PATH = "output/this-is-not-a-good-deal.wav"

def generate():
    payload = {
        "profile_id": PROFILE_ID,
        "text": TEXT,
        "language": "en",
        "seed": 42
    }
    
    print(f"Triggering generation for: '{TEXT}'")
    response = requests.post(f"{BASE_URL}/generate", json=payload)
    response.raise_for_status()
    gen_data = response.json()
    gen_id = gen_data["id"]
    print(f"Generation triggered. ID: {gen_id}")
    return gen_id

def poll_and_download(gen_id):
    print(f"Polling status for ID: {gen_id}...")
    while True:
        response = requests.get(f"{BASE_URL}/history/{gen_id}")
        response.raise_for_status()
        data = response.json()
        status = data.get("status", "generating")
        print(f"Status: {status}")

        if status == "failed":
            error = data.get("error", "Unknown error")
            raise Exception(f"Generation failed: {error}")
        # Triple validation: completed + audio_path non-empty + duration>0
        if (status == "completed"
                and data.get("duration", 0) > 0
                and data.get("audio_path", "")):
            break
            
        time.sleep(2)
    
    print("Generation complete! Downloading...")
    download_url = f"{BASE_URL}/history/{gen_id}/export-audio"
    response = requests.get(download_url)
    response.raise_for_status()
    
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "wb") as f:
        f.write(response.content)
    print(f"Saved to: {OUTPUT_PATH}")

if __name__ == "__main__":
    try:
        gid = generate()
        poll_and_download(gid)
    except Exception as e:
        print(f"ERROR: {e}")
