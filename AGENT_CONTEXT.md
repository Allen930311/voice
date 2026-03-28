# 專案上下文 (Agent Context)：Voicebox

> **最後更新時間**：2026-03-25 23:19
> **自動生成**：由 `prepare_context.py` 產生，供 AI Agent 快速掌握專案全局

---

## 🎯 1. 專案目標 (Project Goal)
* **核心目的**：_（請手動補充，或建立 README.md）_

## 🛠️ 2. 技術棧與環境 (Tech Stack & Environment)
* _（未偵測到 package.json / pyproject.toml / requirements.txt）_

## 📂 3. 核心目錄結構 (Core Structure)
_(💡 AI 讀取守則：請依據此結構尋找對應檔案，勿盲目猜測路徑)_
```text
Voicebox/
├── AGENT_CONTEXT.md
├── Assets.car
├── clone_auto.py
├── clone_debug.py
├── debug_gen.py
├── manual_test.py
├── output
│   ├── output_test.wav
│   ├── shohei_ohtani_final.wav
│   ├── yan_cong_en.wav
│   └── 今天天氣真好.wav
├── partial.plist
├── payload.json
├── sample
│   ├── What if Germany won WW2 #shorts #4k #history #extra_320k.mp3
│   ├── __RLsnZv7q9v0_28s_normalized.mp3
│   ├── sample.wav
│   ├── shohei_ohtani_sample.wav
│   ├── shohei_ohtani_sample_10s.wav
│   └── 大谷翔平為何放棄直接挑戰大聯盟？改變大谷一生的男人_1080p.mp4
├── status.json
├── status_utf8.json
├── test_audio.py
├── uninstall.exe
├── upload_log.txt
├── upload_sample.py
├── voice_gen_tool.py
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
│   │   └── voicebox-server.spec
│   ├── biome.json
│   ├── bun.lock
│   ├── data
│   │   ├── backends
│   │   ├── cache
│   │   ├── generations
│   │   ├── profiles
│   │   └── voicebox.db
│   ├── diary
│   │   └── 2026
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
│   ├── requirements.txt
│   ├── scripts
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
│   └── web
│       ├── index.html
│       ├── package.json
│       ├── src
│       ├── tsconfig.json
│       ├── tsconfig.node.json
│       └── vite.config.ts
├── voicebox-mcp
│   ├── README.md
│   ├── server.py
│   └── start-backend.ps1
├── voicebox-server.exe
├── voicebox.exe
└── voicebox.icns
```

## 🏛️ 4. 架構與設計約定 (Architecture & Conventions)
_(來自專案 L1 快取 `.auto-skill-local.md`)_

# 🏠 專案本地經驗 (L1 Cache)

> 此檔案記錄「只對本專案有效」的經驗與設定。
> 判斷準則：「換一個新專案，這條經驗還有用嗎？」→ Yes = 寫全域 L2，No = 寫這裡。
> ⚠️ 單條經驗不超過 3 行。同一分區累積超過 8 條時，請精簡合併。

## 📋 環境與部署
<!-- Port、環境變數、啟動指令、部署平台等 -->
- Voicebox 後端 port: `17493`，啟動: `just dev-backend`（需先 `just setup-python`）
- MCP Server 位於 `voicebox-mcp/server.py`，已註冊至 `~/.claude.json`（全域 scope）
- 權限白名單 `mcp__voicebox` 已加入 `~/.claude/settings.json`

## 🐛 踩坑紀錄
<!-- 本專案特有的 Bug、怪癖、依賴衝突與解法 -->
- `settings.json` 不接受 `mcpServers` 欄位 → 用 `claude mcp add --scope user` 寫入 `~/.claude.json`
- `POST /transcribe` 處理長音訊（如 >20s MP3）易報錯 400 或超時，需預先轉為 WAV 並設 `httpx.AsyncClient(timeout=300)`
- Voicebox 上傳 sample 限制嚴格：長度務必 <30s；若報錯 "Too loud (reduce input gain)" 需以 `ffmpeg -filter:a "volume=0.5"` 降噪降音量。

## 🏗️ 架構決策
<!-- 本專案選用的技術方案、資料夾慣例、模組拆分規則 -->
- MCP Server 用 Python `mcp` SDK (FastMCP) + `httpx` 異步呼叫 localhost REST API
- 輪詢模式等待生成完成（SSE 在 stdio MCP 中不實用）
- `voicebox_clone_voice` 整合三步為一：建 Profile → Whisper 轉錄 → 上傳音訊

## ⚠️ Known Issues
<!-- 已知但暫未修復的問題與暫行解法 -->
- 尚未實際測試（後端未啟動、無模型下載），需先完成 `just setup-python` + 模型下載

## 🔧 常用指令
<!-- 本專案頻繁使用的 CLI 指令速查 -->
- 啟動後端: `cd voicebox && just dev-backend`
- 啟動腳本: `powershell -File voicebox-mcp/start-backend.ps1`
- 健康檢查: `curl http://127.0.0.1:17493/health`


## 🚦 5. 目前進度與待辦 (Current Status & TODO)
_(自動提取自最近日記 2026-03-24)_

### 🚧 待辦事項
- [x] 申請 Pexels API Key（免費，用於 B-roll 搜尋）
- [x] Whisper 整合方式確認：MCP 工具直接 spawn `whisper` CLI，省去中間層
- [ ] 重啟 Video Studio MCP server 使 studio_transcribe_video 生效

