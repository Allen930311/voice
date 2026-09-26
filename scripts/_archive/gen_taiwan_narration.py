"""
台灣環島飛覽 — 解說配音生成腳本
Voice: 大谷翔平 (profile_id: 6eca2ef5-f809-4a8b-8677-608f97e8e3cb)
Target: ~60 seconds to match 1800 frames @ 30fps
Output: C:/Users/Allen/OneDrive/Desktop/remotion/public/narration.wav
"""

import httpx
import asyncio
import sys
import io
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE_URL = "http://127.0.0.1:17493"
PROFILE_ID = "6eca2ef5-f809-4a8b-8677-608f97e8e3cb"  # 大谷翔平
OUTPUT_PATH = Path(r"C:\Users\Allen\OneDrive\Desktop\remotion\public\narration.wav")

# 60 秒解說詞（約 222 字，配合環島 6 站節奏）
NARRATION = """台灣，孕育多元文化與自然奇景的寶島，讓我們從高空開啟這場環島之旅。

台北的地標，台北一零一高聳入雲，象徵城市無限的現代活力。

飛越山脈，宜蘭龜山島靜靜守候在太平洋的海面，如一顆明珠閃耀。

花蓮，太魯閣峽谷歷經億萬年雕鑿，展現大地最壯麗的地質奇景。

台東三仙台，礁嶼屹立蔚藍海面，靜謐神聖，充滿大自然的力量。

高雄，蓮池潭龍虎塔倒映水中，訴說南台灣深厚的人文底蘊。

台中，彩虹眷村的繽紛色彩閃耀，是歷史與創意的美麗交融。

環繞台灣一圈，這片寶島的美麗無窮，永遠值得細細品味。"""


async def generate():
    async with httpx.AsyncClient(timeout=600) as client:
        # 1. 健康確認
        r = await client.get(f"{BASE_URL}/health")
        print(f"Server: {r.json()['status']} | GPU: {r.json().get('gpu_type','N/A')}")

        # 2. 觸發生成
        print(f"\n[1/3] 觸發生成 (profile={PROFILE_ID[:8]}...)")
        r = await client.post(f"{BASE_URL}/generate", json={
            "profile_id": PROFILE_ID,
            "text": NARRATION,
            "language": "zh",
            "engine": "qwen",
            "model_size": "1.7B",
        })
        r.raise_for_status()
        gen_id = r.json()["id"]
        print(f"    Generation ID: {gen_id}")

        # 3. 輪詢等待完成
        print("[2/3] 生成中", end="", flush=True)
        for i in range(180):
            await asyncio.sleep(3)
            print(".", end="", flush=True)
            r = await client.get(f"{BASE_URL}/history/{gen_id}")
            data = r.json()
            # ⚠️ 三重驗證 — Silent Failure 會回傳 completed 但 duration:0 / audio_path:""
            if (data["status"] == "completed"
                    and data.get("duration", 0) > 0
                    and data.get("audio_path", "")):
                print(" 完成！")
                break
            elif data["status"] == "completed":
                # 靜默失敗：status=completed 但無音訊，繼續等待（server 可能正在重試）
                print("?", end="", flush=True)
                continue
            elif data["status"] == "failed":
                print(f"\n[ERROR] 生成失敗: {data.get('error')}")
                print("[HINT] 若多次失敗，請重啟 Voicebox: powershell -File scripts/start-voicebox-gpu.ps1")
                return
        else:
            print("\n[ERROR] 逾時")
            return

        # 4. 下載音訊
        print(f"[3/3] 下載至 {OUTPUT_PATH}")
        r = await client.get(f"{BASE_URL}/audio/{gen_id}")
        r.raise_for_status()
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_bytes(r.content)
        size_kb = len(r.content) / 1024
        print(f"    成功！檔案大小: {size_kb:.1f} KB")


if __name__ == "__main__":
    asyncio.run(generate())
