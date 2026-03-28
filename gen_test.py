"""Test dramatic narration generation."""
import httpx
import asyncio
from pathlib import Path

PROFILE_ID = "27883698-73ed-484f-965d-899b89ae99af"
OUT = r"C:\Users\Allen\OneDrive\Desktop\Voicebox\output\test_dramatic.wav"

async def main():
    payload = {
        "profile_id": PROFILE_ID,
        "text": "在那風雲變幻的年代，... 一個男人，站在命運的十字路口。... 他的選擇，... 將改變整個世界的走向。...",
        "language": "zh",
        "engine": "qwen",
        "model_size": "0.6B",
        "normalize": True,
        "effects_chain": [
            {"type": "reverb", "enabled": True, "params": {
                "room_size": 0.55, "damping": 0.35, "wet_level": 0.3, "dry_level": 0.85, "width": 0.9
            }},
            {"type": "compressor", "enabled": True, "params": {
                "threshold_db": -20.0, "ratio": 4.0, "attack_ms": 5.0, "release_ms": 100.0
            }}
        ]
    }

    timeout = httpx.Timeout(600.0, connect=10.0)
    async with httpx.AsyncClient(base_url="http://127.0.0.1:17493", timeout=timeout) as c:
        r = await c.post("/generate", json=payload)
        print("POST:", r.status_code, r.text[:200])
        if r.status_code != 200:
            return
        gen_id = r.json().get("id")
        print("gen_id:", gen_id)

        for i in range(80):
            await asyncio.sleep(10)
            r2 = await c.get(f"/history/{gen_id}")
            d = r2.json()
            s = d.get("status")
            ap = str(d.get("audio_path", ""))[:80]
            dur = d.get("duration")
            print(f"[{(i+1)*10}s] status={s} dur={dur} audio={ap}")
            if s == "completed" and d.get("audio_path"):
                r3 = await c.get(f"/audio/{gen_id}")
                Path(OUT).parent.mkdir(exist_ok=True)
                Path(OUT).write_bytes(r3.content)
                print(f"Saved! {len(r3.content)//1024} KB -> {OUT}")
                return
            elif s == "failed":
                print("FAILED:", d.get("error"))
                return

asyncio.run(main())
