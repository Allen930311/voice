# 專案上下文 (Agent Context)：Voicebox

> **最後更新時間**：2026-04-01 22:03（`prepare_context.py` 自動觸發已隨 auto-skill 系統於 2026-09-26 停用，本檔為最後一次生成的靜態快照，不再自動更新）
> **狀態**：原由 `prepare_context.py` 產生；§4 內容已完整承接原 `.auto-skill-local.md`（該檔已於 2026-09-26 確認無資訊遺失後刪除）

---

## 🎯 1. 專案目標 (Project Goal)
* **核心目的**：<p align="center"> <strong>Local-first Voice Cloning Studio & AI Voice Ecosystem</strong><br/> 克隆聲音、生成配音、音效處理、專案作曲 — 都在本地端完成。 </p>
* _完整說明見 [README.md](README.md)_

## 🛠️ 2. 技術棧與環境 (Tech Stack & Environment)
* _（未偵測到 package.json / pyproject.toml / requirements.txt）_

## 📂 3. 核心目錄結構 (Core Structure)
_(💡 AI 讀取守則：請依據此結構尋找對應檔案，勿盲目猜測路徑)_
```text
Voicebox/
├── AGENT_CONTEXT.md
├── Assets.car
├── README.md
├── VOICE_PROFILES.md
├── bin
│   ├── Assets.car
│   ├── partial.plist
│   ├── uninstall.exe
│   ├── voicebox-server.exe
│   ├── voicebox.exe
│   └── voicebox.icns
├── data
│   ├── backends
│   │   └── cuda
│   ├── cache
│   │   └── 20271302341b7ed378cb2825ed11649e.prompt
│   ├── profiles
│   │   ├── c55e07df-c5c7-4b0b-aa48-588e525030b9
│   │   └── profile-germany-ww2-shorts.voicebox.zip
│   └── voicebox.db
├── diary
│   └── 2026
│       ├── 03
│       └── 04
├── generate_audio.py
├── generate_narration_direct.py
├── id.txt
├── latest.json
├── output
│   ├── Adam_test_verification.wav
│   ├── chatterbox_exaggeration_0.50.wav
│   ├── chatterbox_exaggeration_0.85.wav
│   ├── i_am_a_women.wav
│   ├── intro_clonetest_01.wav
│   ├── intro_germany_ww2.wav
│   ├── intro_narrator_male.wav
│   ├── intro_ohtani_10s.wav
│   ├── intro_ohtani_full.wav
│   ├── mine_en_female.wav
│   ├── mine_ww2_narrator.wav
│   ├── output_sunny_day.wav
│   ├── output_sunny_day_dramatic.wav
│   ├── output_test.wav
│   ├── shohei_gpu_test.wav
│   ├── shohei_ohtani_final.wav
│   ├── test_automation_flow.wav
│   ├── test_dramatic.wav
│   ├── test_en_female.wav
│   ├── yan_cong_en.wav
│   ├── 今天天氣真好.wav
│   └── 英文解說1_dramatic.wav
├── partial.plist
├── sample
│   ├── ElevenLabs_2026-01-21T17_23_18_Adam - Dominant, Firm_pre_sp97_s60_sb68_se0_b_m2.mp3
│   ├── ElevenLabs_Adam_reference.wav
│   ├── Listen and Repeat_ Speak with me in English_128k.mp3
│   ├── What if Germany won WW2 #shorts #4k #history #extra_320k.mp3
│   ├── __RLsnZv7q9v0_28s_normalized.mp3
│   ├── adam_normalized.wav
│   ├── adam_ref.wav
│   ├── sample.wav
│   ├── segment_10s.mp3
│   ├── segment_clear_10s.mp3
│   ├── shohei_ohtani_sample.wav
│   ├── shohei_ohtani_sample_10s.wav
│   ├── temp_short_segment.mp3
│   ├── ww2_narrator_28s.wav
│   ├── ww2_narrator_28s_norm.wav
│   └── 大谷翔平為何放棄直接挑戰大聯盟？改變大谷一生的男人_1080p.mp4
├── scripts
│   ├── clone_auto.py
│   ├── clone_debug.py
│   ├── debug
│   │   ├── payload.json
│   │   ├── status.json
│   │   ├── status_utf8.json
│   │   └── upload_log.txt
│   ├── debug_gen.py
│   ├── gen_taiwan_narration.py
│   ├── gen_test.py
│   ├── generate_narration_async.py
│   ├── generate_narration_final.py
│   ├── manual_test.py
│   ├── start-voicebox-gpu.ps1
│   ├── test_audio.py
│   ├── test_intel_arc.py
│   ├── upload_sample.py
│   └── voice_gen_tool.py
├── server_err.txt
├── server_log.txt
├── status.txt
├── temp.json
├── test_intel_arc.py
├── test_qwen_directml.py
├── text.txt
├── voicebox
│   ├── AGENT_CONTEXT.md
│   ├── CHANGELOG.md
│   ├── CONTRIBUTING.md
│   ├── Dockerfile
│   ├── LICENSE
│   ├── README.md
│   ├── SECURITY.md
│   ├── VOICEBOX_ANALYSIS.md
│   ├── app
│   │   ├── components.json
│   │   ├── index.html
│   │   ├── package.json
│   │   ├── plugins
│   │   ├── src
│   │   ├── tsconfig.json
│   │   ├── tsconfig.node.json
│   │   └── vite.config.ts
│   ├── backend
│   │   ├── README.md
│   │   ├── STYLE_GUIDE.md
│   │   ├── __init__.py
│   │   ├── app.py
│   │   ├── backends
│   │   ├── config.py
│   │   ├── database
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── pyproject.toml
│   │   ├── requirements-mlx.txt
│   │   ├── requirements.txt
│   │   ├── routes
│   │   ├── server.py
│   │   ├── services
│   │   ├── tests
│   │   ├── utils
│   │   ├── voicebox-server.spec
│   │   └── voicebox.db
│   ├── biome.json
│   ├── bun.lock
│   ├── data
│   │   ├── backends
│   │   ├── cache
│   │   ├── generations
│   │   ├── profiles
│   │   └── voicebox.db
│   ├── docker-compose.yml
│   ├── docs
│   │   ├── README.md
│   │   ├── app
│   │   ├── bun.lock
│   │   ├── cli.json
│   │   ├── components
│   │   ├── content
│   │   ├── lib
│   │   ├── mdx-components.tsx
│   │   ├── next.config.mjs
│   │   ├── notes
│   │   ├── openapi.json
│   │   ├── package.json
│   │   ├── plans
│   │   ├── postcss.config.mjs
│   │   ├── public
│   │   ├── scripts
│   │   ├── source.config.ts
│   │   └── tsconfig.json
│   ├── justfile
│   ├── landing
│   │   ├── README.md
│   │   ├── components.json
│   │   ├── next.config.js
│   │   ├── nixpacks.toml
│   │   ├── package.json
│   │   ├── postcss.config.js
│   │   ├── public
│   │   ├── src
│   │   ├── tailwind.config.js
│   │   └── tsconfig.json
│   ├── package.json
│   ├── reports
│   │   └── whisper_benchmark_report.md
│   ├── requirements.txt
│   ├── scripts
│   │   ├── bench_whisper_ov.py
│   │   ├── convert-assets.sh
│   │   ├── generate-api.sh
│   │   ├── package_cuda.py
│   │   ├── prepare-release.sh
│   │   ├── setup-dev-sidecar.js
│   │   ├── test_download_progress.py
│   │   └── update-icons.sh
│   ├── tauri
│   │   ├── assets
│   │   ├── index.html
│   │   ├── package.json
│   │   ├── src
│   │   ├── src-tauri
│   │   ├── tsconfig.json
│   │   ├── tsconfig.node.json
│   │   └── vite.config.ts
│   ├── web
│   │   ├── index.html
│   │   ├── package.json
│   │   ├── src
│   │   ├── tsconfig.json
│   │   ├── tsconfig.node.json
│   │   └── vite.config.ts
│   ├── whisper_bench_output.log
│   ├── whisper_bench_output_utf8.log
│   ├── whisper_bench_results.csv
│   ├── whisper_bench_results.txt
│   └── whisper_bench_v2.log
├── voicebox-mcp
│   ├── README.md
│   ├── server.py
│   └── start-backend.ps1
├── voicebox-server.exe
├── voicebox.db
├── voicebox.exe
└── voicebox.icns
```

## 🏛️ 4. 架構與設計約定 (Architecture & Conventions)
_(原內容來自專案 L1 快取 `.auto-skill-local.md`；該檔已於 2026-09-26 刪除，本節現為唯一副本)_

# 🏠 專案本地經驗 (L1 Cache)

> 此檔案記錄「只對本專案有效」的經驗與設定。
> 判斷準則：「換一個新專案，這條經驗還有用嗎？」→ Yes = 寫全域 L2，No = 寫這裡。
> ⚠️ 單條經驗不超過 3 行。同一分區累積超過 8 條時，請精簡合併。

## 📋 環境與部署
<!-- Port、環境變數、啟動指令、部署平台等 -->
- Voicebox 後端 port: `17493`，啟動: `just dev-backend`（需先 `just setup-python`）
- MCP Server 位於 `voicebox-mcp/server.py`，已註冊至 `~/.claude.json`（全域 scope）
- 權限白名單 `mcp__voicebox` 已加入 `~/.claude/settings.json`
- GitHub 倉庫: `https://github.com/Allen930311/voice` (排除 `output/`, `sample/`, `bin/`, `diary/`)

## 🐛 踩坑紀錄
<!-- 本專案特有的 Bug、怪癖、依賴衝突與解法 -->
- `settings.json` 不接受 `mcpServers` 欄位 → 用 `claude mcp add --scope user` 寫入 `~/.claude.json`
- Voicebox 上傳 sample 限制嚴格：長度務必 <30s；若報錯 "Too loud (reduce input gain)" 需以 `ffmpeg -filter:a "volume=0.5"` 降噪降音量。
- **422 Error (Parameter Mismatch)**: `seed` 必須 `>= 0`；Qwen 模型限制為 `1.7B` 或 `0.6B`。
- **500 Error (Download Lag)**: 生成後文件寫入可能延遲，建議等待 5-10 秒再下載。
- **Stalled Queue**: 生成任務卡死時，執行 `powershell -File scripts/start-voicebox-gpu.ps1` 進行硬重啟。

## 🏗️ 架構決策
<!-- 本專案選用的技術方案、資料夾慣例、模組拆分規則 -->
- MCP Server 用 Python `mcp` SDK (FastMCP) + `httpx` 異步呼叫 localhost REST API
- 輪詢模式等待生成完成（SSE 在 stdio MCP 中不實用）
- `voicebox_clone_voice` 整合三步為一：建 Profile → Whisper 轉錄 → 上傳音訊
- 根目錄組織規範：所有 `.py` 腳本存入 `scripts/`，臨時數據存入 `scripts/debug/`，執行檔與資源存入 `bin/`。

## 🎬 Social-v3-lean 串聯 Golden Path
<!-- Remotion 影片流水線的標準配音流程 -->
- **Social 專用工具**：直接呼叫 `voicebox_generate_for_social`，不要手動帶 profile_id 或 output_path
- **Social 預設 Profile**：`Germany WW2 Shorts` → ID `f9b3a288-2e86-4156-8dfd-42b70ece7283`（英文旁白首選，32 次驗證）
- **Social 輸出路徑**：`C:/Users/Allen/OneDrive/Desktop/remotion/public/narration.wav`（Remotion 固定讀取此路徑）
- **中文旁白 Profile**：`解說男聲` → ID `27883698-73ed-484f-965d-899b89ae99af`
- **標準引擎**：`qwen 1.7B`（英文），`chatterbox`（中文需要克隆感）
- **一次完整流程**：`voicebox_generate_for_social(text="...", language="en")` → 音訊自動存入 Remotion public/

## ⚠️ Known Issues
<!-- 已知但暫未修復的問題與暫行解法 -->
- ✅ 完整自動化流程已驗證（2026-03-30）：start_backend → generate → poll → download 穩定
- **`voicebox_generate` MCP Error ≠ 失敗**：任務已提交後台，直接 poll `voicebox_history` 即可，**絕對不要重試**，重試會生成重複音檔浪費時間
- 冷啟動路徑（後端完全未運行）尚未實際觸發測試

## 🔧 常用指令
<!-- 本專案頻繁使用的 CLI 指令速查 -->
- 啟動後端 (CPU): `cd voicebox && just dev-backend`
- 啟動後端 (GPU): `powershell -File scripts/start-voicebox-gpu.ps1`
- 啟動 MCP 腳本: `powershell -File voicebox-mcp/start-backend.ps1`
- 健康檢查: `curl http://127.0.0.1:17493/health`

## 📂 常用檔案
- `VOICE_PROFILES.md`: **ID 定義基準 (Source of Truth)**。批次生成時務必以此文件的 UUID 為準。
- `AGENT_CONTEXT.md`: 專案上下文總結，供 Agent 快速對齊當前進度。


## 🚦 5. 目前進度與待辦 (Current Status & TODO)
_(自動提取自最近日記 2026-04-01)_

### 🚧 待辦事項
- [ ] 觀察 MCP 在更新後的使用穩定度。
- [ ] 考慮將 generate_audio.py 的邏輯整合入更穩定的工具鏈。
- [ ] 測試長文本生成的效能表現。

