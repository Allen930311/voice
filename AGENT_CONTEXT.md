# 專案上下文 (Agent Context)：Voicebox

> **最後更新時間**：2026-03-29 17:54
> **自動生成**：由 `prepare_context.py` 產生，供 AI Agent 快速掌握專案全局

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
├── README.md
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
│   │   └── c55e07df-c5c7-4b0b-aa48-588e525030b9
│   └── voicebox.db
├── diary
│   └── 2026
│       └── 03
├── output
│   ├── arc_bench
│   │   ├── tts_CPU_run1.wav
│   │   └── tts_CPU_run2.wav
│   ├── chatterbox_exaggeration_0.50.wav
│   ├── chatterbox_exaggeration_0.85.wav
│   ├── directml_bench
│   │   └── qwen0.6B_cpu_run1.wav
│   ├── output_sunny_day.wav
│   ├── output_sunny_day_dramatic.wav
│   ├── output_test.wav
│   ├── shohei_ohtani_final.wav
│   ├── test_dramatic.wav
│   ├── yan_cong_en.wav
│   ├── 今天天氣真好.wav
│   └── 英文解說1_dramatic.wav
├── sample
│   ├── What if Germany won WW2 #shorts #4k #history #extra_320k.mp3
│   ├── __RLsnZv7q9v0_28s_normalized.mp3
│   ├── sample.wav
│   ├── shohei_ohtani_sample.wav
│   ├── shohei_ohtani_sample_10s.wav
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
│   ├── gen_test.py
│   ├── manual_test.py
│   ├── start-voicebox-gpu.ps1
│   ├── test_audio.py
│   ├── test_intel_arc.py
│   ├── upload_sample.py
│   └── voice_gen_tool.py
├── server_err.txt
├── server_log.txt
├── status.txt
├── test_intel_arc.py
├── test_qwen_directml.py
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
└── voicebox-mcp
    ├── README.md
    ├── server.py
    └── start-backend.ps1
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
- GitHub 倉庫: `https://github.com/Allen930311/voice` (排除 `output/`, `sample/`, `bin/`, `diary/`)

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
- 根目錄組織規範：所有 `.py` 腳本存入 `scripts/`，臨時數據存入 `scripts/debug/`，執行檔與資源存入 `bin/`。

## ⚠️ Known Issues
<!-- 已知但暫未修復的問題與暫行解法 -->
- 尚未實際測試（後端未啟動、無模型下載），需先完成 `just setup-python` + 模型下載

## 🔧 常用指令
<!-- 本專案頻繁使用的 CLI 指令速查 -->
- 啟動後端 (CPU): `cd voicebox && just dev-backend`
- 啟動後端 (GPU): `powershell -File scripts/start-voicebox-gpu.ps1`
- 啟動 MCP 腳本: `powershell -File voicebox-mcp/start-backend.ps1`
- 健康檢查: `curl http://127.0.0.1:17493/health`

## 📅 工作流經驗 (Workflow)
- **日記同步協議**：專案日記（`diary/YYYY/MM/`）同步至全域日記（`note/10_Daily/YYYY/M/WXX/`）時，需手動提取「進度摘要」、「專案進度追蹤」、「改善與學習」與「跨專案待辦」四個維度，並依各週資料夾結構歸檔。


## 🚦 5. 目前進度與待辦 (Current Status & TODO)
_(自動提取自最近日記 2026-03-29)_

### 🚧 待辦事項
- [ ] 提交本次 GPU/NPU fallback 修改到 git（`ov_accelerate.py`、`pytorch_backend.py`）
- [ ] 研究 Qwen TTS + DirectML int64 問題的解決方案（`torch.cat` 替換或降階為 int32）
- [ ] 安裝 SoX 以解除音訊處理限制（`choco install sox` 或手動安裝）
- [ ] 嘗試 Qwen TTS 1.7B 模型是否能帶來更佳音質
- [ ] 評估 NPU 對 Whisper tiny 模型的加速效果（目前 tiny 強制走 CPU 以取得最低延遲）
- [ ] 增加 OpenVINO Whisper GPU 快取路徑的 fallback 清理邏輯（Export 失敗後 cleanup）

