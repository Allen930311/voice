import httpx
import asyncio
from pathlib import Path

API_URL = "http://127.0.0.1:17493"
PROFILE_NAME = "Shohei Ohtani 10s"  # 重啟後使用 Python uvicorn 後端，profile 名稱不同
OUTPUT_DIR = "C:/Users/Allen/OneDrive/Desktop/remotion/public"
OUTPUT_FILE = Path(OUTPUT_DIR) / "narration.wav"

# ── 台灣環島解說腳本（目標 ~60 秒，約 300 字）──────────────────────
# 段落對應影片節奏（每站 10 秒）：
#  0-10s  台北    → 台北 101
# 10-20s  宜蘭    → 龜山島
# 20-30s  花蓮    → 太魯閣峽谷
# 30-40s  台東    → 三仙台
# 40-50s  高雄    → 蓮池潭
# 50-60s  台中→台北 → 彩虹眷村
SCRIPT = (
    "大家好，我是大谷翔平。"
    "今天，讓我們一起從台北出發，展開這趟難忘的台灣環島之旅。"
    "台北，是台灣的心臟。"
    "高達五百零八米的台北一零一，曾是全球最高建築，"
    "每逢跨年夜，燦爛的煙火從頂端綻放，象徵台灣人的驕傲與活力。"
    "繼續向東南飛，抵達宜蘭。"
    "太平洋上的龜山島靜靜漂浮，宛如海神的守護，神秘而壯麗。"
    "花蓮，太魯閣峽谷令人屏息。"
    "億萬年的地殼力量，在這裡雕刻出壯觀的大理石壁壘，鬼斧神工，無與倫比。"
    "台東的三仙台，傳說三位神仙曾在此停留。"
    "蜿蜒的跨海步橋，連接著神聖的岩礁，如詩如畫，令人流連忘返。"
    "高雄的蓮池潭，龍虎塔倒映在平靜的湖面上，"
    "是南台灣最具代表性的文化地標，充滿濃厚的民俗風情。"
    "台中的彩虹眷村，是老爺爺用一筆一劃繪出的繽紛奇蹟，"
    "色彩鮮豔，充滿生命力，如同台灣人樂觀開朗的精神。"
    "一圈環繞，我們回到了台北。"
    "台灣，這座美麗的寶島，每一處都充滿驚喜與感動。謝謝各位，下次見。"
)

# 語調指令（instruct，max 500 字）
INSTRUCT = "充滿熱情的旅遊紀錄片解說員語調，節奏流暢，略帶感動，聲音溫暖有力"

async def main():
    timeout = httpx.Timeout(600.0, connect=10.0)
    async with httpx.AsyncClient(base_url=API_URL, timeout=timeout) as c:
        # ── 取得已存在的 Profile ID ──────────────────────────────────
        print(f"查找 Profile: {PROFILE_NAME} ...")
        r = await c.get("/profiles")
        r.raise_for_status()
        profiles = r.json()
        profile_id = next((p["id"] for p in profiles if p["name"] == PROFILE_NAME), None)

        if not profile_id:
            print(f"[錯誤] 找不到 Profile '{PROFILE_NAME}'")
            return
        print(f"Profile ID: {profile_id}")
        print(f"腳本長度: {len(SCRIPT)} 字")

        # ── 提交生成任務（同步，直接等待）────────────────────────────
        print("提交生成任務...")
        payload = {
            "profile_id": profile_id,
            "text": SCRIPT,
            "language": "zh",
            "model_size": "1.7B",
            "instruct": INSTRUCT,
        }
        r = await c.post("/generate", json=payload)
        if r.status_code != 200:
            print(f"[錯誤] 提交失敗: {r.status_code}")
            print(r.text)
            return

        res = r.json()
        gen_id = res.get("id")
        audio_path = res.get("audio_path", "")
        print(f"任務 ID: {gen_id}")

        # ── 如果回傳時 audio_path 已填入，直接下載 ────────────────────
        if audio_path:
            print(f"同步完成，audio_path={audio_path}")
        else:
            # 非同步：輪詢 /history/{gen_id} 直到 audio_path 非空
            print("非同步模式，開始輪詢（最長等待 10 分鐘）...")
            for i in range(72):
                await asyncio.sleep(10)
                r = await c.get(f"/history/{gen_id}")
                data = r.json()
                audio_path = data.get("audio_path", "")
                duration = data.get("duration", 0)
                print(f"[{(i+1)*10}s] audio_path={'[done]' if audio_path else '[wait]'}  duration={duration:.1f}s")
                if audio_path:
                    break
            else:
                print("[超時] 超過 12 分鐘仍未完成，請檢查 Voicebox 服務狀態。")
                return

        # ── 下載音訊 ─────────────────────────────────────────────────
        print("下載音訊...")
        r_audio = await c.get(f"/audio/{gen_id}")
        if r_audio.status_code != 200:
            print(f"[錯誤] 下載失敗: {r_audio.status_code} {r_audio.text[:200]}")
            return

        Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
        OUTPUT_FILE.write_bytes(r_audio.content)
        size_kb = OUTPUT_FILE.stat().st_size // 1024
        print(f"[OK] 語音已儲存至: {OUTPUT_FILE}  ({size_kb} KB)")
        print("下一步：在 Remotion Studio 預覽 TaiwanFlyover，確認音畫同步後執行 render。")

if __name__ == "__main__":
    asyncio.run(main())
