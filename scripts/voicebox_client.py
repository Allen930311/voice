"""
Voicebox Client — 統一的 TTS 生成工具

用法:
  # 單段生成
  python voicebox_client.py generate --voice germany-ww2 --text "Hello world" --out output/test.wav

  # 從檔案讀文字
  python voicebox_client.py generate --voice narrator-zh --file script.txt --out output/narration.wav

  # Social 快捷（自動選 profile + 輸出到 remotion）
  python voicebox_client.py social --lang en --text "..." --out-name scene-01.wav

  # 批次生成（JSON 格式）
  python voicebox_client.py batch --script scenes.json --out-dir output/audio/

  # 列出所有 profile
  python voicebox_client.py profiles

scenes.json 格式:
  [
    {"voice": "germany-ww2", "text": "Scene one narration.", "out": "scene-01.wav"},
    {"voice": "germany-ww2", "text": "Scene two narration.", "out": "scene-02.wav"}
  ]
"""

import argparse
import json
import sys
import time
import io
from pathlib import Path

import httpx

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# ── 路徑設定 ──────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "profiles.json"
DEFAULT_OUTPUT_DIR = ROOT / "output"
REMOTION_PUBLIC = Path(r"C:\Users\Allen\OneDrive\Desktop\remotion\public")

POLL_INTERVAL = 5   # 秒
POLL_MAX = 120      # 最多等 10 分鐘


# ── 設定載入 ─────────────────────────────────────────────────

def load_config() -> dict:
    if not CONFIG_PATH.exists():
        sys.exit(f"[ERROR] 找不到 config: {CONFIG_PATH}")
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_profile(config: dict, key: str) -> dict:
    profiles = config.get("profiles", {})
    if key not in profiles:
        names = ", ".join(profiles.keys())
        sys.exit(f"[ERROR] 找不到 voice '{key}'。可用: {names}")
    return profiles[key]


# ── Voicebox HTTP API ─────────────────────────────────────────

def _client(base_url: str) -> httpx.Client:
    return httpx.Client(base_url=base_url, timeout=httpx.Timeout(300.0, connect=10.0))


def check_backend(base_url: str) -> bool:
    try:
        with _client(base_url) as c:
            r = c.get("/health", timeout=5.0)
            return r.status_code == 200
    except Exception:
        return False


def generate_audio(base_url: str, profile: dict, text: str, seed: int | None = None) -> str:
    payload = {
        "profile_id": profile["id"],
        "text": text,
        "language": profile["language"],
        "engine": profile["engine"],
        "model_size": profile.get("model_size", "default"),
        "normalize": True,
    }
    if seed is not None:
        payload["seed"] = seed

    with _client(base_url) as c:
        print(f"[→] 提交生成請求 (engine={profile['engine']}, voice={profile['name']})")
        r = c.post("/generate", json=payload)
        r.raise_for_status()
        gen_id = r.json()["id"]
        print(f"[→] Generation ID: {gen_id}")

        for i in range(POLL_MAX):
            time.sleep(POLL_INTERVAL)
            r2 = c.get(f"/history/{gen_id}")
            r2.raise_for_status()
            data = r2.json()
            status = data.get("status", "pending")
            dur = data.get("duration", 0)
            print(f"[{i+1:3d}] status={status} duration={dur:.1f}s", end="\r")

            if status == "failed":
                print()
                sys.exit(f"[ERROR] 生成失敗: {data.get('error', '未知')}")

            if status == "completed" and dur > 0 and data.get("audio_path"):
                print(f"\n[✓] 生成完成，時長 {dur:.1f}s")
                return gen_id

    print()
    sys.exit(f"[ERROR] 等待超時 (gen_id={gen_id})")


def download_audio(base_url: str, gen_id: str, out_path: Path) -> None:
    with _client(base_url) as c:
        r = c.get(f"/audio/{gen_id}")
        r.raise_for_status()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(r.content)
    print(f"[✓] 已儲存: {out_path} ({len(r.content)//1024} KB)")


# ── 指令處理 ─────────────────────────────────────────────────

def cmd_profiles(config: dict, _args) -> None:
    print(f"{'Key':<16} {'Name':<30} {'Lang':<6} {'Engine'}")
    print("-" * 70)
    for key, p in config["profiles"].items():
        print(f"{key:<16} {p['name']:<30} {p['language']:<6} {p['engine']}")
    defaults = config.get("social_defaults", {})
    print(f"\nSocial 預設: en→{defaults.get('en','?')}  zh→{defaults.get('zh','?')}")


def cmd_generate(config: dict, args) -> None:
    base_url = config["backend_url"]
    if not check_backend(base_url):
        sys.exit(f"[ERROR] Voicebox 後端未啟動 ({base_url})")

    profile = get_profile(config, args.voice)

    if args.file:
        text = Path(args.file).read_text(encoding="utf-8").strip()
    else:
        text = args.text

    if not text:
        sys.exit("[ERROR] 請提供 --text 或 --file")

    out_path = Path(args.out) if args.out else DEFAULT_OUTPUT_DIR / "output.wav"

    seed = int(args.seed) if args.seed is not None else None
    gen_id = generate_audio(base_url, profile, text, seed=seed)
    download_audio(base_url, gen_id, out_path)


def cmd_social(config: dict, args) -> None:
    base_url = config["backend_url"]
    if not check_backend(base_url):
        sys.exit(f"[ERROR] Voicebox 後端未啟動 ({base_url})")

    defaults = config.get("social_defaults", {})
    voice_key = defaults.get(args.lang)
    if not voice_key:
        sys.exit(f"[ERROR] social_defaults 沒有設定語言 '{args.lang}'")

    profile = get_profile(config, voice_key)

    if args.file:
        text = Path(args.file).read_text(encoding="utf-8").strip()
    else:
        text = args.text

    out_name = args.out_name or "narration.wav"
    out_path = REMOTION_PUBLIC / out_name

    seed = int(args.seed) if args.seed is not None else None
    gen_id = generate_audio(base_url, profile, text, seed=seed)
    download_audio(base_url, gen_id, out_path)
    print(f"[✓] Remotion 路徑: public/{out_name}")


def cmd_batch(config: dict, args) -> None:
    base_url = config["backend_url"]
    if not check_backend(base_url):
        sys.exit(f"[ERROR] Voicebox 後端未啟動 ({base_url})")

    script_path = Path(args.script)
    if not script_path.exists():
        sys.exit(f"[ERROR] 找不到批次腳本: {script_path}")

    scenes: list[dict] = json.loads(script_path.read_text(encoding="utf-8"))
    out_dir = Path(args.out_dir) if args.out_dir else DEFAULT_OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[→] 批次生成 {len(scenes)} 個場景 → {out_dir}")
    for i, scene in enumerate(scenes, 1):
        voice_key = scene.get("voice")
        text = scene.get("text", "")
        out_name = scene.get("out", f"scene-{i:02d}.wav")
        seed = scene.get("seed")

        print(f"\n── 場景 {i}/{len(scenes)}: {out_name} ──")
        profile = get_profile(config, voice_key)
        gen_id = generate_audio(base_url, profile, text, seed=seed)
        download_audio(base_url, gen_id, out_dir / out_name)

    print(f"\n[✓] 批次完成，{len(scenes)} 個檔案 → {out_dir}")


# ── 入口 ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Voicebox TTS 統一工具")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # profiles
    sub.add_parser("profiles", help="列出所有可用 voice profile")

    # generate
    g = sub.add_parser("generate", help="生成單段音訊")
    g.add_argument("--voice", required=True, help="Voice key（來自 config/profiles.json）")
    g.add_argument("--text", default="", help="要生成的文字")
    g.add_argument("--file", help="從文字檔讀取（與 --text 擇一）")
    g.add_argument("--out", help="輸出路徑（預設: output/output.wav）")
    g.add_argument("--seed", type=int, help="固定種子以重現結果")

    # social
    s = sub.add_parser("social", help="Social 快捷：輸出到 remotion/public/")
    s.add_argument("--lang", default="en", choices=["en", "zh"], help="語言")
    s.add_argument("--text", default="", help="旁白文字")
    s.add_argument("--file", help="從文字檔讀取")
    s.add_argument("--out-name", default="narration.wav", help="檔名（在 remotion/public/ 下）")
    s.add_argument("--seed", type=int, help="固定種子")

    # batch
    b = sub.add_parser("batch", help="批次生成多個場景")
    b.add_argument("--script", required=True, help="scenes.json 路徑")
    b.add_argument("--out-dir", help="輸出目錄（預設: output/）")

    args = parser.parse_args()
    config = load_config()

    dispatch = {
        "profiles": cmd_profiles,
        "generate": cmd_generate,
        "social": cmd_social,
        "batch": cmd_batch,
    }
    dispatch[args.cmd](config, args)


if __name__ == "__main__":
    main()
