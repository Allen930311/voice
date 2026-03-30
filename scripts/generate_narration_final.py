import json
import requests
import os

# Voicebox 設置
API_URL = "http://localhost:17493"
PROFILE_NAME = "大谷翔平_解說"
SAMPLE_PATH = r"C:\Users\Allen\OneDrive\Desktop\Voicebox\sample\shohei_ohtani_sample_10s.wav"
OUTPUT_DIR = r"C:\Users\Allen\OneDrive\Desktop\remotion\public"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "narration.wav")

SCRIPT = "大家好，我是大谷翔平。現在，讓我們一起展開這段台灣環島的旅程。"

def generate():
    # 1. 檢查 Profile 是否存在
    resp = requests.get(f"{API_URL}/profiles")
    profiles = resp.json() # 直接取得 list
    profile_id = None
    
    for p in profiles:
        if p["name"] == PROFILE_NAME:
            profile_id = p["id"]
            break
            
    if not profile_id:
        print(f"建立新 Profile: {PROFILE_NAME}")
        resp = requests.post(f"{API_URL}/profiles", json={
            "name": PROFILE_NAME,
            "language": "zh",
            "description": "大谷翔平風格解說員"
        })
        profile_id = resp.json()["id"]
        
        # 上傳樣本
        print("上傳語音樣本...")
        with open(SAMPLE_PATH, "rb") as f:
            requests.post(f"{API_URL}/profiles/{profile_id}/samples", 
                         files={"audio": f},
                         data={"reference_text": "大谷翔平の野球に対する情熱は誰にも負けない。"})

    # 2. 生成配音
    print("正在生成解說配音...")
    payload = {
        "profile_id": profile_id,
        "text": SCRIPT,
        "language": "zh",
        "engine": "chatterbox"
    }
    resp = requests.post(f"{API_URL}/generate", json=payload)
    
    result = resp.json()
    if "generation_id" not in result:
        print(f"生成失敗！回應內容: {json.dumps(result, indent=2, ensure_ascii=False)}")
        return
        
    gen_id = result["generation_id"]
    
    # 3. 下載音訊
    print(f"下載音訊至: {OUTPUT_FILE}")
    resp = requests.get(f"{API_URL}/generations/{gen_id}/audio")
    with open(OUTPUT_FILE, "wb") as f:
        f.write(resp.content)
    
    print("語音生成任務完成！")

if __name__ == "__main__":
    generate()
