"""
Voicebox MCP Server — 個人配音室工具
將本地 Voicebox TTS/語音克隆引擎暴露為 Claude Code 可調用的 MCP 工具。

啟動方式: python server.py
前置條件: Voicebox 後端需先啟動 (just dev-backend 或 python -m backend.main)
"""

import asyncio
import json
import os
import sys
import base64
from pathlib import Path
from typing import Optional

import httpx
from mcp.server.fastmcp import FastMCP

# ── 設定 ─────────────────────────────────────────────
VOICEBOX_BASE_URL = os.getenv("VOICEBOX_URL", "http://127.0.0.1:17493")
VOICEBOX_PROJECT = Path(os.getenv(
    "VOICEBOX_PROJECT",
    r"c:\Users\Allen\OneDrive\Desktop\Voicebox\voicebox"
))
TIMEOUT = httpx.Timeout(300.0, connect=10.0)  # TTS 生成可能很慢

mcp = FastMCP(
    "voicebox",
    instructions=(
        "Voicebox 個人配音室 — 本地語音克隆與 TTS 工具。"
        "可用來克隆聲音、生成配音、管理語音檔案。"
        "使用前請確保 Voicebox 後端已啟動 (port 17493)。"
    ),
)


# ── 工具函式 ─────────────────────────────────────────


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url=VOICEBOX_BASE_URL, timeout=TIMEOUT)


async def _poll_generation(
    client: httpx.AsyncClient,
    gen_id: str,
    output_path: Optional[str] = None,
) -> tuple:
    """輪詢直到生成完成，回傳 (status_data, saved_path_or_None)。"""
    status_data: dict = {}
    for _ in range(120):
        await asyncio.sleep(5)
        try:
            r = await client.get(f"/history/{gen_id}")
            r.raise_for_status()
            status_data = r.json()
            s = status_data.get("status", "pending")
            if s == "completed":
                break
            elif s == "failed":
                return status_data, None
        except httpx.HTTPStatusError:
            continue
    else:
        status_data["_timeout"] = True
        return status_data, None

    saved_path = None
    if output_path:
        r3 = await client.get(f"/audio/{gen_id}")
        r3.raise_for_status()
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(r3.content)
        saved_path = str(out)

    return status_data, saved_path


def _format_prosody(text: str, transform: str, language: str) -> str:
    """根據解說風格對文字做停頓格式化，以增強 TTS 語調起伏。"""
    import re

    if transform == "dramatic":
        if language == "zh":
            text = re.sub(r'([。！？])', r'\1...', text)
            text = re.sub(r'([，、])', r'\1 ', text)
        else:
            text = re.sub(r'([.!?])(\s+)', r'\1...\2', text)
            text = re.sub(r'([,;])(\s+)', r'\1 \2', text)

    elif transform == "measured":
        if language == "zh":
            text = re.sub(r'([。！？])', r'\1\n', text)
        else:
            text = re.sub(r'([.!?])(\s+)', r'\1\n', text)

    elif transform == "crisp":
        text = re.sub(r'\s+', ' ', text).strip()

    elif transform == "narrative":
        if language == "zh":
            text = re.sub(r'([。])', r'\1\n', text)
            text = re.sub(r'([，])', r'\1 ', text)
        else:
            text = re.sub(r'([.])(\s+)', r'\1\n', text)
            text = re.sub(r'([,])(\s+)', r'\1 \2', text)

    elif transform == "whisper":
        if language == "zh":
            text = re.sub(r'([。！？])', r'\1 ', text)
        else:
            text = re.sub(r'([.!?])(\s+)', r'\1 \2', text)

    # "natural": no change

    return text.strip()


# ─── 健康檢查 ───


@mcp.tool()
async def voicebox_status() -> str:
    """檢查 Voicebox 後端是否正在運行，回報 GPU 與模型狀態。"""
    try:
        async with _client() as c:
            r = await c.get("/health")
            r.raise_for_status()
            data = r.json()
            return json.dumps(data, ensure_ascii=False, indent=2)
    except httpx.ConnectError:
        return (
            "❌ Voicebox 後端未啟動。\n"
            f"請先在 {VOICEBOX_PROJECT} 目錄執行：\n"
            "  just dev-backend\n"
            "或：\n"
            "  python -m backend.main --port 17493"
        )
    except Exception as e:
        return f"❌ 連線錯誤：{e}"


# ─── 語音 Profile 管理 ───


@mcp.tool()
async def voicebox_list_profiles() -> str:
    """列出所有已建立的語音 Profile（聲音角色），包含名稱、語言、樣本數。"""
    async with _client() as c:
        r = await c.get("/profiles")
        r.raise_for_status()
        profiles = r.json()
        if not profiles:
            return "目前沒有任何語音 Profile。使用 voicebox_create_profile 建立一個。"
        lines = []
        for p in profiles:
            lines.append(
                f"• **{p['name']}** (id: `{p['id']}`)\n"
                f"  語言: {p['language']} | 樣本數: {p.get('sample_count', 0)} | "
                f"  生成次數: {p.get('generation_count', 0)}"
            )
        return "\n".join(lines)


@mcp.tool()
async def voicebox_create_profile(
    name: str,
    language: str = "en",
    description: str = "",
) -> str:
    """建立新的語音 Profile（聲音角色）。

    Args:
        name: 語音名稱（如 "Allen 的聲音"、"旁白女聲"）
        language: 語言代碼 (en/zh/ja/ko/de/fr/ru/pt/es/it 等)
        description: 描述此語音的特色
    """
    async with _client() as c:
        r = await c.post("/profiles", json={
            "name": name,
            "language": language,
            "description": description or None,
        })
        r.raise_for_status()
        p = r.json()
        return (
            f"✅ Profile 已建立！\n"
            f"名稱: {p['name']}\n"
            f"ID: `{p['id']}`\n"
            f"語言: {p['language']}\n\n"
            f"下一步：使用 voicebox_add_sample 上傳參考音訊來克隆此聲音。"
        )


@mcp.tool()
async def voicebox_add_sample(
    profile_id: str,
    audio_path: str,
    reference_text: str,
) -> str:
    """為 Profile 新增參考音訊樣本（用於聲音克隆）。

    Args:
        profile_id: Profile ID
        audio_path: 參考音訊檔案的絕對路徑（支援 WAV/MP3/M4A/OGG/FLAC/AAC）
        reference_text: 音訊中說的文字內容（必須與音訊匹配）
    """
    audio_file = Path(audio_path)
    if not audio_file.exists():
        return f"❌ 找不到檔案：{audio_path}"

    async with _client() as c:
        with open(audio_file, "rb") as f:
            r = await c.post(
                f"/profiles/{profile_id}/samples",
                files={"file": (audio_file.name, f, "audio/wav")},
                data={"reference_text": reference_text},
            )
        r.raise_for_status()
        sample = r.json()
        return (
            f"✅ 參考音訊已上傳！\n"
            f"樣本 ID: `{sample['id']}`\n"
            f"參考文字: {sample['reference_text']}\n\n"
            f"此聲音已可用於生成配音。"
        )


@mcp.tool()
async def voicebox_get_profile(profile_id: str) -> str:
    """取得特定 Profile 的詳細資訊，包含所有樣本。

    Args:
        profile_id: Profile ID
    """
    async with _client() as c:
        r = await c.get(f"/profiles/{profile_id}")
        r.raise_for_status()
        p = r.json()

        r2 = await c.get(f"/profiles/{profile_id}/samples")
        r2.raise_for_status()
        samples = r2.json()

        lines = [
            f"**{p['name']}** (id: `{p['id']}`)",
            f"語言: {p['language']}",
            f"描述: {p.get('description') or '無'}",
            f"樣本數: {p.get('sample_count', 0)}",
            f"生成次數: {p.get('generation_count', 0)}",
        ]
        if samples:
            lines.append("\n**參考樣本：**")
            for s in samples:
                lines.append(f"  • `{s['id']}` — \"{s['reference_text']}\"")
        return "\n".join(lines)


@mcp.tool()
async def voicebox_delete_profile(profile_id: str) -> str:
    """刪除語音 Profile 及其所有樣本。

    Args:
        profile_id: Profile ID
    """
    async with _client() as c:
        r = await c.delete(f"/profiles/{profile_id}")
        r.raise_for_status()
        return f"✅ Profile `{profile_id}` 已刪除。"


@mcp.tool()
async def voicebox_export_profile(profile_id: str, output_dir: str) -> str:
    """匯出 Profile 為 ZIP 檔（含樣本與設定），方便備份或分享。

    Args:
        profile_id: Profile ID
        output_dir: 匯出目標目錄
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    async with _client() as c:
        r = await c.get(f"/profiles/{profile_id}/export")
        r.raise_for_status()
        # 取得檔名
        cd = r.headers.get("content-disposition", "")
        fname = "profile_export.zip"
        if "filename=" in cd:
            fname = cd.split("filename=")[-1].strip('"')
        dest = out / fname
        dest.write_bytes(r.content)
        return f"✅ Profile 已匯出至：{dest}"


@mcp.tool()
async def voicebox_import_profile(zip_path: str) -> str:
    """從 ZIP 檔匯入 Profile。

    Args:
        zip_path: ZIP 檔案的絕對路徑
    """
    zp = Path(zip_path)
    if not zp.exists():
        return f"❌ 找不到檔案：{zip_path}"
    async with _client() as c:
        with open(zp, "rb") as f:
            r = await c.post(
                "/profiles/import",
                files={"file": (zp.name, f, "application/zip")},
            )
        r.raise_for_status()
        p = r.json()
        return f"✅ Profile 已匯入！名稱: {p['name']}，ID: `{p['id']}`"


# ─── TTS 語音生成 ───


@mcp.tool()
async def voicebox_generate(
    profile_id: str,
    text: str,
    language: str = "en",
    engine: str = "qwen",
    model_size: str = "1.7B",
    seed: Optional[int] = None,
    instruct: Optional[str] = None,
    output_path: Optional[str] = None,
) -> str:
    """使用指定的語音 Profile 生成配音音訊。

    Args:
        profile_id: 語音 Profile ID
        text: 要生成的文字內容
        language: 語言代碼 (en/zh/ja/ko 等)
        engine: TTS 引擎 (qwen/luxtts/chatterbox/chatterbox_turbo/tada)
        model_size: 模型大小 (0.6B/1.7B 用於 Qwen; 1B/3B 用於 TADA)
        seed: 隨機種子（固定可重現結果）
        instruct: 語音指令（僅 chatterbox_turbo 支援）
        output_path: 可選，指定輸出音訊的儲存路徑（會複製一份）
    """
    payload = {
        "profile_id": profile_id,
        "text": text,
        "language": language,
        "engine": engine,
        "model_size": model_size,
        "normalize": True,
    }
    if seed is not None:
        payload["seed"] = seed
    if instruct:
        payload["instruct"] = instruct

    async with _client() as c:
        # 1. 觸發生成
        r = await c.post("/generate", json=payload)
        r.raise_for_status()
        gen = r.json()
        gen_id = gen["id"]

        # 2. 輪詢等待完成（SSE 在 MCP 中不方便，改用輪詢）
        for _ in range(120):  # 最多等 10 分鐘
            await asyncio.sleep(5)
            try:
                r2 = await c.get(f"/history/{gen_id}")
                r2.raise_for_status()
                status_data = r2.json()
                status = status_data.get("status", "pending")
                if status == "completed":
                    break
                elif status == "failed":
                    err = status_data.get("error", "未知錯誤")
                    return f"❌ 生成失敗：{err}"
            except httpx.HTTPStatusError:
                continue
        else:
            return "⏳ 生成超時（超過 10 分鐘），請稍後用 voicebox_history 查看狀態。"

        # 3. 如果指定了 output_path，下載音訊
        audio_info = ""
        if output_path:
            r3 = await c.get(f"/audio/{gen_id}")
            r3.raise_for_status()
            out = Path(output_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(r3.content)
            audio_info = f"\n音訊已儲存至：{out}"

        duration = status_data.get("duration")
        dur_str = f"{duration:.1f} 秒" if duration else "未知"

        return (
            f"✅ 配音生成完成！\n"
            f"Generation ID: `{gen_id}`\n"
            f"引擎: {engine} ({model_size})\n"
            f"時長: {dur_str}\n"
            f"文字: {text[:100]}{'...' if len(text) > 100 else ''}"
            f"{audio_info}\n\n"
            f"使用 voicebox_download_audio 可下載音訊檔。"
        )


@mcp.tool()
async def voicebox_download_audio(
    generation_id: str,
    output_path: str,
) -> str:
    """下載已生成的配音音訊至指定路徑。

    Args:
        generation_id: Generation ID
        output_path: 輸出檔案路徑（含檔名，如 C:/output/narration.wav）
    """
    async with _client() as c:
        r = await c.get(f"/audio/{generation_id}")
        r.raise_for_status()
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(r.content)
        size_kb = len(r.content) / 1024
        return f"✅ 音訊已下載至：{out}（{size_kb:.0f} KB）"


# ─── 歷史紀錄 ───


@mcp.tool()
async def voicebox_history(
    profile_id: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 10,
) -> str:
    """查看配音生成歷史紀錄。

    Args:
        profile_id: 篩選特定 Profile 的紀錄
        search: 搜尋文字關鍵字
        limit: 回傳筆數上限（預設 10）
    """
    params = {"limit": limit, "offset": 0}
    if profile_id:
        params["profile_id"] = profile_id
    if search:
        params["search"] = search

    async with _client() as c:
        r = await c.get("/history", params=params)
        r.raise_for_status()
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("generations", []))
        if not items:
            return "沒有找到任何生成紀錄。"

        lines = []
        for g in items[:limit]:
            text_preview = (g.get("text", "")[:60] + "...") if len(g.get("text", "")) > 60 else g.get("text", "")
            dur = g.get("duration")
            dur_str = f"{dur:.1f}s" if dur else "?"
            lines.append(
                f"• `{g['id']}` [{g.get('status', '?')}] "
                f"({g.get('engine', '?')}) {dur_str}\n"
                f"  Profile: {g.get('profile_name', g.get('profile_id', '?'))}\n"
                f"  \"{text_preview}\""
            )
        return "\n\n".join(lines)


# ─── 模型管理 ───


@mcp.tool()
async def voicebox_list_models() -> str:
    """列出所有可用的 TTS 模型及其下載狀態。"""
    async with _client() as c:
        r = await c.get("/models/status")
        r.raise_for_status()
        models = r.json()
        if not models:
            return "無法取得模型資訊。"

        lines = []
        for m in models:
            status_icon = "✅" if m.get("downloaded") else "⬇️"
            size = m.get("size_mb", 0)
            size_str = f"{size}MB" if size < 1000 else f"{size/1000:.1f}GB"
            lines.append(
                f"{status_icon} **{m.get('display_name', m.get('model_name', '?'))}**\n"
                f"   引擎: {m.get('engine', '?')} | 大小: {size_str} | "
                f"   語言: {', '.join(m.get('languages', []))}"
            )
        return "\n".join(lines)


@mcp.tool()
async def voicebox_download_model(model_name: str) -> str:
    """下載指定的 TTS 模型。

    Args:
        model_name: 模型名稱（從 voicebox_list_models 取得）
    """
    async with _client() as c:
        r = await c.post("/models/download", json={"model_name": model_name})
        r.raise_for_status()
        return f"✅ 模型 `{model_name}` 開始下載。請稍候，可用 voicebox_list_models 確認狀態。"


# ─── 音效處理 ───


@mcp.tool()
async def voicebox_list_effects() -> str:
    """列出所有可用的音效處理類型及參數。"""
    async with _client() as c:
        r = await c.get("/effects/available")
        r.raise_for_status()
        effects = r.json()
        lines = []
        for e in effects:
            name = e.get("type", e.get("name", "?"))
            desc = e.get("description", "")
            lines.append(f"• **{name}** — {desc}")
            params = e.get("params", e.get("parameters", {}))
            if isinstance(params, dict):
                for k, v in params.items():
                    lines.append(f"    {k}: {v}")
        return "\n".join(lines) if lines else json.dumps(effects, indent=2)


@mcp.tool()
async def voicebox_apply_effects(
    generation_id: str,
    effects_chain: str,
    label: str = "with effects",
) -> str:
    """對已生成的音訊套用音效處理（建立新版本）。

    Args:
        generation_id: Generation ID
        effects_chain: JSON 格式的音效鏈，例如：
            [{"type": "reverb", "enabled": true, "params": {"room_size": 0.5, "wet": 0.3}}]
        label: 版本標籤
    """
    try:
        chain = json.loads(effects_chain)
    except json.JSONDecodeError:
        return "❌ effects_chain 必須是合法的 JSON 字串。"

    async with _client() as c:
        r = await c.post(
            f"/generations/{generation_id}/versions/apply-effects",
            json={"effects_chain": chain, "label": label, "set_as_default": True},
        )
        r.raise_for_status()
        v = r.json()
        return f"✅ 音效已套用！版本 ID: `{v.get('id', '?')}`，標籤: {label}"


# ─── 轉錄 (STT) ───


@mcp.tool()
async def voicebox_transcribe(
    audio_path: str,
    language: str = "en",
    model: str = "base",
) -> str:
    """將音訊檔轉錄為文字（Speech-to-Text），可用於產生參考文字。

    Args:
        audio_path: 音訊檔案的絕對路徑
        language: 語言代碼
        model: Whisper 模型 (base/small/medium/large/turbo)
    """
    ap = Path(audio_path)
    if not ap.exists():
        return f"❌ 找不到檔案：{audio_path}"

    async with _client() as c:
        with open(ap, "rb") as f:
            r = await c.post(
                "/transcribe",
                files={"file": (ap.name, f, "audio/wav")},
                data={"language": language, "model": model},
                timeout=httpx.Timeout(600.0, connect=10.0),
            )
        r.raise_for_status()
        result = r.json()
        text = result.get("text", result.get("transcription", str(result)))
        return f"📝 轉錄結果：\n\n{text}"


# ─── 快捷：一鍵克隆聲音 ───


@mcp.tool()
async def voicebox_clone_voice(
    name: str,
    audio_path: str,
    reference_text: Optional[str] = None,
    language: str = "en",
    description: str = "",
    transcribe_model: str = "base",
) -> str:
    """一鍵克隆聲音：建立 Profile + 上傳參考音訊 + 自動轉錄（如未提供參考文字）。

    Args:
        name: 聲音名稱（如 "Allen"、"旁白女聲"）
        audio_path: 參考音訊檔案的絕對路徑
        reference_text: 音訊中說的文字（若為空會自動轉錄）
        language: 語言代碼 (en/zh/ja/ko 等)
        description: 聲音描述
        transcribe_model: 自動轉錄時使用的 Whisper 模型 (base/small/medium/large/turbo)
    """
    ap = Path(audio_path)
    if not ap.exists():
        return f"❌ 找不到檔案：{audio_path}"

    async with _client() as c:
        # Step 1: 建立 Profile
        r1 = await c.post("/profiles", json={
            "name": name,
            "language": language,
            "description": description or None,
        })
        r1.raise_for_status()
        profile = r1.json()
        pid = profile["id"]

        # Step 2: 自動轉錄（如未提供參考文字）
        ref_text = reference_text
        if not ref_text:
            with open(ap, "rb") as f:
                rt = await c.post(
                    "/transcribe",
                    files={"file": (ap.name, f, "audio/wav")},
                    data={"language": language, "model": transcribe_model},
                    timeout=httpx.Timeout(600.0, connect=10.0),
                )
            rt.raise_for_status()
            result = rt.json()
            ref_text = result.get("text", result.get("transcription", ""))
            if not ref_text:
                return f"❌ 自動轉錄失敗，請手動提供 reference_text。Profile 已建立 (ID: `{pid}`)。"

        # Step 3: 上傳參考音訊
        with open(ap, "rb") as f:
            r2 = await c.post(
                f"/profiles/{pid}/samples",
                files={"file": (ap.name, f, "audio/wav")},
                data={"reference_text": ref_text},
            )
        r2.raise_for_status()
        sample = r2.json()

        return (
            f"✅ 聲音克隆完成！\n\n"
            f"**Profile:** {name}\n"
            f"**ID:** `{pid}`\n"
            f"**語言:** {language}\n"
            f"**參考文字:** {ref_text[:100]}{'...' if len(ref_text) > 100 else ''}\n"
            f"**樣本 ID:** `{sample['id']}`\n\n"
            f"現在可以使用 voicebox_generate(profile_id=\"{pid}\", text=\"你的文字\") 來生成配音了！"
        )


# ─── Stories（多段配音排序）───


@mcp.tool()
async def voicebox_create_story(name: str, description: str = "") -> str:
    """建立一個 Story（配音專案），用於將多段配音排列組合。

    Args:
        name: Story 名稱
        description: 描述
    """
    async with _client() as c:
        r = await c.post("/stories", json={"name": name, "description": description or None})
        r.raise_for_status()
        s = r.json()
        return f"✅ Story 已建立！ID: `{s['id']}`，名稱: {s['name']}"


@mcp.tool()
async def voicebox_add_to_story(story_id: str, generation_id: str) -> str:
    """將已生成的配音加入 Story。

    Args:
        story_id: Story ID
        generation_id: Generation ID
    """
    async with _client() as c:
        r = await c.post(f"/stories/{story_id}/items", json={"generation_id": generation_id})
        r.raise_for_status()
        return f"✅ 配音 `{generation_id}` 已加入 Story `{story_id}`。"


# ─── 唱歌模式（實驗性）───


@mcp.tool()
async def voicebox_sing(
    profile_id: str,
    lyrics: str,
    style: str = "ballad",
    language: str = "en",
    pitch_shift: float = 0.0,
    add_reverb: bool = True,
    seed: Optional[int] = None,
    output_path: Optional[str] = None,
) -> str:
    """🎵 實驗性唱歌模式：用語音克隆嘗試模擬唱歌效果。

    透過以下技術模擬歌唱感：
    • Chatterbox Turbo 的副語言標籤（[breath] 換氣聲，英文限定）
    • 旋律性停頓格式（♪...♪ 包裹每句歌詞）
    • 混響 + 合唱 + 壓縮效果（強化歌唱氛圍）

    注意：TTS 模型並非專為唱歌設計，效果為實驗性近似模擬。
    英文（chatterbox_turbo）效果最佳，中文使用 chatterbox。

    Args:
        profile_id: 語音 Profile ID
        lyrics: 歌詞文字（每行一句，自動格式化）
        style: 風格 — ballad（抒情）/ pop（流行）/ opera（戲劇）
        language: 語言代碼（en 效果最佳）
        pitch_shift: 音調偏移半音（-12~12，0=不變，正=升調，負=降調）
        add_reverb: 是否套用混響效果
        seed: 隨機種子（固定可重現結果）
        output_path: 輸出音訊儲存路徑
    """
    lines = [l.strip() for l in lyrics.strip().split("\n") if l.strip()]
    if not lines:
        return "❌ 歌詞不可為空。"

    STYLE_MAP = {
        "ballad": {
            "separator": " [breath] ",
            "wrap": ("♪ ", " ♪"),
            "engine": "chatterbox_turbo",
            "reverb": {"room_size": 0.65, "damping": 0.4, "wet_level": 0.38, "dry_level": 0.7, "width": 1.0},
            "chorus": None,
        },
        "pop": {
            "separator": " [breath] ",
            "wrap": ("♪ ", " ♪"),
            "engine": "chatterbox_turbo",
            "reverb": {"room_size": 0.4, "damping": 0.5, "wet_level": 0.25, "dry_level": 0.8, "width": 0.9},
            "chorus": {"rate_hz": 1.2, "depth": 0.35, "feedback": 0.0, "centre_delay_ms": 12.0, "mix": 0.25},
        },
        "opera": {
            "separator": "... ",
            "wrap": ("～ ", " ～"),
            "engine": "chatterbox",
            "reverb": {"room_size": 0.9, "damping": 0.2, "wet_level": 0.5, "dry_level": 0.6, "width": 1.0},
            "chorus": {"rate_hz": 0.8, "depth": 0.45, "feedback": 0.1, "centre_delay_ms": 15.0, "mix": 0.3},
        },
    }

    cfg = STYLE_MAP.get(style, STYLE_MAP["ballad"])
    engine = cfg["engine"] if language == "en" else "chatterbox"
    separator = cfg["separator"] if engine == "chatterbox_turbo" else "... "
    wp, ws = cfg["wrap"]
    formatted_text = separator.join(f"{wp}{line}{ws}" for line in lines)

    effects_chain = []
    if add_reverb and cfg.get("reverb"):
        effects_chain.append({"type": "reverb", "enabled": True, "params": cfg["reverb"]})
    if cfg.get("chorus"):
        effects_chain.append({"type": "chorus", "enabled": True, "params": cfg["chorus"]})
    if pitch_shift != 0.0:
        semitones = max(-12.0, min(12.0, pitch_shift))
        effects_chain.append({"type": "pitch_shift", "enabled": True, "params": {"semitones": semitones}})
    effects_chain.append({
        "type": "compressor", "enabled": True,
        "params": {"threshold_db": -18.0, "ratio": 3.0, "attack_ms": 8.0, "release_ms": 120.0},
    })

    payload: dict = {
        "profile_id": profile_id,
        "text": formatted_text,
        "language": language,
        "engine": engine,
        "normalize": True,
        "effects_chain": effects_chain,
    }
    if seed is not None:
        payload["seed"] = seed

    async with _client() as c:
        r = await c.post("/generate", json=payload)
        r.raise_for_status()
        gen_id = r.json()["id"]
        status_data, saved_path = await _poll_generation(c, gen_id, output_path)

    if status_data.get("_timeout"):
        return "⏳ 生成超時，請稍後用 voicebox_history 查看。"
    if status_data.get("status") == "failed":
        return f"❌ 生成失敗：{status_data.get('error', '未知錯誤')}"

    dur = status_data.get("duration")
    dur_str = f"{dur:.1f} 秒" if dur else "未知"
    pitch_str = f" | 音調: {pitch_shift:+.1f} 半音" if pitch_shift != 0.0 else ""
    audio_info = f"\n🎵 音訊已儲存至：{saved_path}" if saved_path else ""

    return (
        f"🎵 唱歌模式完成！（實驗性）\n"
        f"Generation ID: `{gen_id}`\n"
        f"風格: {style} | 引擎: {engine}{pitch_str} | 時長: {dur_str}\n\n"
        f"📝 格式化歌詞：\n{formatted_text[:300]}{'...' if len(formatted_text) > 300 else ''}"
        f"{audio_info}\n\n"
        f"💡 調音技巧：\n"
        f"  • pitch_shift=2 升調兩個半音（偏高音）\n"
        f"  • pitch_shift=-3 降調（偏低沉）\n"
        f"  • style=opera 最戲劇化（搭配大混響）\n"
        f"  • 事後可用 voicebox_apply_effects 微調效果"
    )


# ─── 解說昱揚頓挫（Expressive Narration）───


@mcp.tool()
async def voicebox_narrate(
    profile_id: str,
    text: str,
    style: str = "storytelling",
    language: str = "zh",
    engine: str = "chatterbox",
    seed: Optional[int] = None,
    output_path: Optional[str] = None,
) -> str:
    """🎙️ 昱揚頓挫解說模式：以指定風格生成富有語調起伏的旁白配音。

    使用智慧文字格式化 + 針對性音效，讓 TTS 產生更有節奏感的解說語調：
    • 在自然斷點插入停頓標記
    • 套用風格對應的後製音效（壓縮、混響、濾波等）

    可用風格：
      dramatic    — 戲劇性（大停頓，適合史詩旁白/預告片）
      documentary — 紀錄片（沉穩有力，適合科普/歷史解說）
      news        — 新聞播報（清晰俐落，適合正式公告）
      storytelling— 說書人（溫暖起伏，適合故事朗讀）
      podcast     — 播客（自然親切，適合口語分享）
      whisper     — 輕語（低沉親密，適合 ASMR 或懸疑感）

    Args:
        profile_id: 語音 Profile ID
        text: 要生成的解說文字
        style: 解說風格（見上方清單）
        language: 語言代碼 (zh/en 等)
        engine: TTS 引擎 (chatterbox/qwen/tada)
        seed: 隨機種子
        output_path: 輸出音訊儲存路徑
    """
    STYLE_PRESETS = {
        "dramatic": {
            "desc": "戲劇性旁白",
            "effects": [
                {"type": "reverb", "enabled": True, "params": {
                    "room_size": 0.55, "damping": 0.35, "wet_level": 0.3, "dry_level": 0.85, "width": 0.9,
                }},
                {"type": "compressor", "enabled": True, "params": {
                    "threshold_db": -20.0, "ratio": 4.0, "attack_ms": 5.0, "release_ms": 100.0,
                }},
            ],
            "transform": "dramatic",
        },
        "documentary": {
            "desc": "紀錄片解說",
            "effects": [
                {"type": "reverb", "enabled": True, "params": {
                    "room_size": 0.3, "damping": 0.6, "wet_level": 0.18, "dry_level": 0.9, "width": 0.7,
                }},
                {"type": "compressor", "enabled": True, "params": {
                    "threshold_db": -22.0, "ratio": 3.5, "attack_ms": 8.0, "release_ms": 120.0,
                }},
            ],
            "transform": "measured",
        },
        "news": {
            "desc": "新聞播報",
            "effects": [
                {"type": "highpass", "enabled": True, "params": {"cutoff_frequency_hz": 120.0}},
                {"type": "compressor", "enabled": True, "params": {
                    "threshold_db": -18.0, "ratio": 5.0, "attack_ms": 3.0, "release_ms": 60.0,
                }},
                {"type": "gain", "enabled": True, "params": {"gain_db": 2.0}},
            ],
            "transform": "crisp",
        },
        "storytelling": {
            "desc": "說書人風格",
            "effects": [
                {"type": "reverb", "enabled": True, "params": {
                    "room_size": 0.35, "damping": 0.5, "wet_level": 0.2, "dry_level": 0.92, "width": 0.8,
                }},
                {"type": "compressor", "enabled": True, "params": {
                    "threshold_db": -24.0, "ratio": 3.0, "attack_ms": 12.0, "release_ms": 150.0,
                }},
            ],
            "transform": "narrative",
        },
        "podcast": {
            "desc": "播客風格",
            "effects": [
                {"type": "compressor", "enabled": True, "params": {
                    "threshold_db": -20.0, "ratio": 3.5, "attack_ms": 10.0, "release_ms": 100.0,
                }},
                {"type": "gain", "enabled": True, "params": {"gain_db": 1.0}},
            ],
            "transform": "natural",
        },
        "whisper": {
            "desc": "輕語 / ASMR",
            "effects": [
                {"type": "lowpass", "enabled": True, "params": {"cutoff_frequency_hz": 7000.0}},
                {"type": "compressor", "enabled": True, "params": {
                    "threshold_db": -28.0, "ratio": 5.0, "attack_ms": 5.0, "release_ms": 80.0,
                }},
                {"type": "reverb", "enabled": True, "params": {
                    "room_size": 0.2, "damping": 0.7, "wet_level": 0.12, "dry_level": 0.95, "width": 0.6,
                }},
            ],
            "transform": "whisper",
        },
    }

    if style not in STYLE_PRESETS:
        return (
            f"❌ 未知風格 '{style}'。\n"
            f"可用風格：{', '.join(STYLE_PRESETS.keys())}"
        )

    preset = STYLE_PRESETS[style]
    formatted_text = _format_prosody(text, preset["transform"], language)

    payload: dict = {
        "profile_id": profile_id,
        "text": formatted_text,
        "language": language,
        "engine": engine,
        "model_size": "1.7B" if engine == "qwen" else "default",
        "normalize": True,
        "effects_chain": preset["effects"],
    }
    if seed is not None:
        payload["seed"] = seed

    async with _client() as c:
        r = await c.post("/generate", json=payload)
        r.raise_for_status()
        gen_id = r.json()["id"]
        status_data, saved_path = await _poll_generation(c, gen_id, output_path)

    if status_data.get("_timeout"):
        return "⏳ 生成超時，請稍後用 voicebox_history 查看。"
    if status_data.get("status") == "failed":
        return f"❌ 生成失敗：{status_data.get('error', '未知錯誤')}"

    dur = status_data.get("duration")
    dur_str = f"{dur:.1f} 秒" if dur else "未知"
    audio_info = f"\n🎙️ 音訊已儲存至：{saved_path}" if saved_path else ""

    return (
        f"🎙️ {preset['desc']}配音完成！\n"
        f"Generation ID: `{gen_id}`\n"
        f"風格: {style} | 引擎: {engine} | 語言: {language} | 時長: {dur_str}\n\n"
        f"📝 格式化後文字：\n{formatted_text[:400]}{'...' if len(formatted_text) > 400 else ''}"
        f"{audio_info}\n\n"
        f"💡 風格建議：\n"
        f"  • dramatic — 史詩預告片旁白首選\n"
        f"  • documentary — 搭配 tada 引擎更自然\n"
        f"  • storytelling — 中文說書人效果佳\n"
        f"  • 加 seed=42 可固定音色方便比較不同風格"
    )


# ─── 聲音變形武器庫 ───


@mcp.tool()
async def voicebox_voice_morph(
    generation_id: str,
    preset: str,
    custom_chain: Optional[str] = None,
) -> str:
    """🎭 聲音變形武器庫：對已生成音訊套用戲劇性音效預設，快速賦予角色個性。

    內建預設：
      villain   — 反派（低沉 -3 半音 + 金屬感合唱 + 混響）
      hero      — 英雄（微降調 + 厚實混響）
      ethereal  — 空靈仙氣（升調 +3 + 大混響 + 合唱）
      ancient   — 古老神秘（降調 -4 + 大混響 + 低通濾波）
      announcer — 廣播播報員（清晰有力 + 壓縮 + 增益）
      deep      — 低沉渾厚（降調 -3 + 低通 + 壓縮）
      high      — 高亢清亮（升調 +3 + 壓縮）
      echo      — 空曠回音（大混響 + 延遲）

    Args:
        generation_id: 要套用效果的 Generation ID
        preset: 預設名稱（見上方清單）
        custom_chain: 自訂 JSON 音效鏈（提供時忽略 preset）
                      格式：[{"type": "reverb", "enabled": true, "params": {...}}]
    """
    MORPHS: dict = {
        "villain": [
            {"type": "pitch_shift", "enabled": True, "params": {"semitones": -3.0}},
            {"type": "chorus", "enabled": True, "params": {
                "rate_hz": 0.2, "depth": 1.0, "feedback": 0.35, "centre_delay_ms": 7.0, "mix": 0.45,
            }},
            {"type": "reverb", "enabled": True, "params": {
                "room_size": 0.6, "damping": 0.3, "wet_level": 0.35, "dry_level": 0.75, "width": 1.0,
            }},
            {"type": "compressor", "enabled": True, "params": {
                "threshold_db": -16.0, "ratio": 5.0, "attack_ms": 5.0, "release_ms": 80.0,
            }},
        ],
        "hero": [
            {"type": "pitch_shift", "enabled": True, "params": {"semitones": -1.5}},
            {"type": "reverb", "enabled": True, "params": {
                "room_size": 0.5, "damping": 0.4, "wet_level": 0.25, "dry_level": 0.85, "width": 0.9,
            }},
            {"type": "compressor", "enabled": True, "params": {
                "threshold_db": -18.0, "ratio": 3.5, "attack_ms": 8.0, "release_ms": 100.0,
            }},
        ],
        "ethereal": [
            {"type": "pitch_shift", "enabled": True, "params": {"semitones": 3.0}},
            {"type": "reverb", "enabled": True, "params": {
                "room_size": 0.9, "damping": 0.2, "wet_level": 0.55, "dry_level": 0.6, "width": 1.0,
            }},
            {"type": "chorus", "enabled": True, "params": {
                "rate_hz": 0.8, "depth": 0.6, "feedback": 0.1, "centre_delay_ms": 18.0, "mix": 0.35,
            }},
        ],
        "ancient": [
            {"type": "pitch_shift", "enabled": True, "params": {"semitones": -4.0}},
            {"type": "reverb", "enabled": True, "params": {
                "room_size": 0.8, "damping": 0.25, "wet_level": 0.45, "dry_level": 0.65, "width": 0.85,
            }},
            {"type": "lowpass", "enabled": True, "params": {"cutoff_frequency_hz": 5500.0}},
        ],
        "announcer": [
            {"type": "highpass", "enabled": True, "params": {"cutoff_frequency_hz": 100.0}},
            {"type": "compressor", "enabled": True, "params": {
                "threshold_db": -15.0, "ratio": 6.0, "attack_ms": 3.0, "release_ms": 50.0,
            }},
            {"type": "gain", "enabled": True, "params": {"gain_db": 4.0}},
        ],
        "deep": [
            {"type": "pitch_shift", "enabled": True, "params": {"semitones": -3.0}},
            {"type": "lowpass", "enabled": True, "params": {"cutoff_frequency_hz": 6000.0}},
            {"type": "compressor", "enabled": True, "params": {
                "threshold_db": -18.0, "ratio": 3.0, "attack_ms": 10.0, "release_ms": 150.0,
            }},
        ],
        "high": [
            {"type": "pitch_shift", "enabled": True, "params": {"semitones": 3.0}},
            {"type": "compressor", "enabled": True, "params": {
                "threshold_db": -20.0, "ratio": 3.0, "attack_ms": 8.0, "release_ms": 100.0,
            }},
        ],
        "echo": [
            {"type": "reverb", "enabled": True, "params": {
                "room_size": 0.85, "damping": 0.3, "wet_level": 0.45, "dry_level": 0.55, "width": 1.0,
            }},
            {"type": "delay", "enabled": True, "params": {
                "delay_seconds": 0.25, "feedback": 0.3, "mix": 0.2,
            }},
        ],
    }

    PRESET_DESC = {
        "villain": "反派（低沉 + 金屬感）",
        "hero": "英雄（微降調 + 厚實混響）",
        "ethereal": "空靈仙氣（升調 + 大混響）",
        "ancient": "古老神秘（降調 + 混響）",
        "announcer": "廣播播報員（清晰有力）",
        "deep": "低沉渾厚",
        "high": "高亢清亮",
        "echo": "空曠回音",
    }

    if custom_chain:
        try:
            chain = json.loads(custom_chain)
        except json.JSONDecodeError:
            return "❌ custom_chain 必須是合法的 JSON 字串。"
        label = "custom-morph"
        desc = "自訂"
    elif preset in MORPHS:
        chain = MORPHS[preset]
        label = f"morph-{preset}"
        desc = PRESET_DESC[preset]
    else:
        presets_list = "\n".join(f"  • {k} — {v}" for k, v in PRESET_DESC.items())
        return f"❌ 未知預設 '{preset}'。\n可用預設：\n{presets_list}"

    async with _client() as c:
        r = await c.post(
            f"/generations/{generation_id}/versions/apply-effects",
            json={"effects_chain": chain, "label": label, "set_as_default": True},
        )
        r.raise_for_status()
        v = r.json()

    return (
        f"🎭 聲音變形完成！\n"
        f"Generation ID: `{generation_id}`\n"
        f"版本 ID: `{v.get('id', '?')}`\n"
        f"預設: {preset} — {desc}\n\n"
        f"使用 voicebox_download_audio 下載，或 voicebox_voice_morph 疊加更多效果。"
    )


# ─── 入口 ───


if __name__ == "__main__":
    mcp.run(transport="stdio")
