# 專案上下文 (Agent Context)：voicebox

> **最後更新時間**：2026-03-18 14:45
> **自動生成**：由 `prepare_context.py` 產生，供 AI Agent 快速掌握專案全局

---

## 🎯 1. 專案目標 (Project Goal)
* **核心目的**：<p align="center"> <img src=".github/assets/icon-dark.webp" alt="Voicebox" width="120" height="120" /> </p>
* _完整說明見 [README.md](README.md)_

## 🛠️ 2. 技術棧與環境 (Tech Stack & Environment)
* **核心套件**：loaders.css, react-loaders
* **開發套件**：@biomejs/biome, @types/node, tailwindcss, typescript
* **可用指令**：dev, dev:web, dev:landing, dev:server, setup:dev, build, build:web, build:landing, build:release, generate:api, generate:keys, build:server, update:icons, convert:assets, lint, lint:fix, format, format:check, check, check:fix, ci
* **Python 套件**：uvicorn, fastapi, sqlalchemy, torch, torchvision, soundfile, librosa, python-multipart, huggingface_hub

### 原始設定檔

<details><summary>package.json</summary>

```json
{
  "name": "voicebox",
  "version": "0.3.1",
  "private": true,
  "workspaces": [
    "app",
    "tauri",
    "web",
    "landing"
  ],
  "scripts": {
    "dev": "bun run setup:dev && cd tauri && bun run tauri dev",
    "dev:web": "cd web && bun run dev",
    "dev:landing": "cd landing && bun run dev",
    "dev:server": "uvicorn backend.main:app --reload --port 17493",
    "setup:dev": "bun run scripts/setup-dev-sidecar.js",
    "build": "./scripts/build-server.sh && cd tauri && bun run tauri build",
    "build:web": "cd web && bun run build",
    "build:landing": "cd landing && bun run build",
    "build:release": "./scripts/prepare-release.sh",
    "generate:api": "./scripts/generate-api.sh",
    "generate:keys": "cd tauri && bun tauri signer generate -w ~/.tauri/voicebox.key",
    "build:server": "./scripts/build-server.sh",
    "update:icons": "./scripts/update-icons.sh",
    "convert:assets": "./scripts/convert-assets.sh",
    "lint": "biome lint .",
    "lint:fix": "biome lint --write .",
    "format": "biome format --write .",
    "format:check": "biome format .",
    "check": "biome check .",
    "check:fix": "biome check --write .",
    "ci": "biome ci ."
  },
  "devDependencies": {
    "@biomejs/biome": "2.3.12",
    "@types/node": "^20.0.0",
    "tailwindcss": "^4.1.18",
    "typescript": "^5.6.0"
  },
  "engines": {
    "bun": ">=1.0.0"
  },
  "packageManager": "bun@1.3.8",
  "dependencies": {
    "loaders.css": "^0.1.2",
    "react-loaders": "^3.0.1"
  }
}

```
</details>

<details><summary>requirements.txt</summary>

```text
uvicorn
fastapi
sqlalchemy
torch
torchvision
soundfile
librosa
python-multipart
huggingface_hub

```
</details>

## 📂 3. 核心目錄結構 (Core Structure)
_(💡 AI 讀取守則：請依據此結構尋找對應檔案，勿盲目猜測路徑)_
```text
voicebox/
├── AGENT_CONTEXT.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── Dockerfile
├── LICENSE
├── README.md
├── SECURITY.md
├── VOICEBOX_ANALYSIS.md
├── app
│   ├── components.json
│   ├── index.html
│   ├── package.json
│   ├── plugins
│   │   └── changelog.ts
│   ├── src
│   │   ├── App.tsx
│   │   ├── assets
│   │   ├── components
│   │   ├── global.d.ts
│   │   ├── hooks
│   │   ├── index.css
│   │   ├── lib
│   │   ├── main.tsx
│   │   ├── platform
│   │   ├── router.tsx
│   │   ├── stores
│   │   └── types
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   └── vite.config.ts
├── backend
│   ├── README.md
│   ├── STYLE_GUIDE.md
│   ├── __init__.py
│   ├── app.py
│   ├── backends
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── chatterbox_backend.py
│   │   ├── chatterbox_turbo_backend.py
│   │   ├── hume_backend.py
│   │   ├── luxtts_backend.py
│   │   ├── mlx_backend.py
│   │   └── pytorch_backend.py
│   ├── config.py
│   ├── database
│   │   ├── __init__.py
│   │   ├── migrations.py
│   │   ├── models.py
│   │   ├── seed.py
│   │   └── session.py
│   ├── main.py
│   ├── models.py
│   ├── pyproject.toml
│   ├── requirements-mlx.txt
│   ├── requirements.txt
│   ├── routes
│   │   ├── __init__.py
│   │   ├── audio.py
│   │   ├── channels.py
│   │   ├── cuda.py
│   │   ├── effects.py
│   │   ├── generations.py
│   │   ├── health.py
│   │   ├── history.py
│   │   ├── models.py
│   │   ├── profiles.py
│   │   ├── stories.py
│   │   ├── tasks.py
│   │   └── transcription.py
│   ├── server.py
│   ├── services
│   │   ├── __init__.py
│   │   ├── channels.py
│   │   ├── cuda.py
│   │   ├── effects.py
│   │   ├── export_import.py
│   │   ├── generation.py
│   │   ├── history.py
│   │   ├── profiles.py
│   │   ├── stories.py
│   │   ├── task_queue.py
│   │   ├── transcribe.py
│   │   ├── tts.py
│   │   └── versions.py
│   ├── tests
│   │   ├── README.md
│   │   ├── __init__.py
│   │   ├── test_cors.py
│   │   ├── test_generation_download.py
│   │   ├── test_profile_duplicate_names.py
│   │   ├── test_progress.py
│   │   ├── test_qwen_download.py
│   │   └── test_whisper_download.py
│   ├── utils
│   │   ├── __init__.py
│   │   ├── audio.py
│   │   ├── cache.py
│   │   ├── chunked_tts.py
│   │   ├── dac_shim.py
│   │   ├── effects.py
│   │   ├── hf_offline_patch.py
│   │   ├── hf_progress.py
│   │   ├── images.py
│   │   ├── platform_detect.py
│   │   ├── progress.py
│   │   └── tasks.py
│   └── voicebox-server.spec
├── biome.json
├── bun.lock
├── data
│   └── cache
├── diary
│   └── 2026
│       └── 03
├── docker-compose.yml
├── docs
│   ├── README.md
│   ├── app
│   │   ├── [[...slug]]
│   │   ├── api
│   │   ├── global.css
│   │   ├── layout.tsx
│   │   ├── llms-full.txt
│   │   ├── llms.mdx
│   │   └── og
│   ├── bun.lock
│   ├── cli.json
│   ├── components
│   │   ├── ai
│   │   ├── api-page.client.tsx
│   │   ├── api-page.tsx
│   │   └── ui
│   ├── content
│   │   └── docs
│   ├── lib
│   │   ├── cn.ts
│   │   ├── layout.shared.tsx
│   │   ├── openapi.ts
│   │   └── source.ts
│   ├── mdx-components.tsx
│   ├── next.config.mjs
│   ├── notes
│   │   ├── BACKEND_CODE_REVIEW.md
│   │   ├── MIGRATION.md
│   │   ├── PROJECT_STATUS.md
│   │   ├── RELEASE_v0.2.0.md
│   │   └── issue-pain-points.md
│   ├── openapi.json
│   ├── package.json
│   ├── plans
│   │   ├── CUDA_LIBS_ADDON.md
│   │   ├── DOCKER_DEPLOYMENT.md
│   │   └── OPENAI_SUPPORT.md
│   ├── postcss.config.mjs
│   ├── public
│   │   ├── images
│   │   └── logo
│   ├── scripts
│   │   └── generate-openapi.ts
│   ├── source.config.ts
│   └── tsconfig.json
├── justfile
├── landing
│   ├── README.md
│   ├── components.json
│   ├── next.config.js
│   ├── nixpacks.toml
│   ├── package.json
│   ├── postcss.config.js
│   ├── public
│   │   ├── App.png
│   │   ├── VoiceBoxAppScreenshot.webp
│   │   ├── apple-touch-icon.png
│   │   ├── assets
│   │   ├── audio
│   │   ├── favicon.ico
│   │   ├── favicon.png
│   │   ├── og.webp
│   │   ├── voicebox-demo.webm
│   │   ├── voicebox-logo-2.png
│   │   ├── voicebox-logo-app.webp
│   │   └── voicebox-logo.png
│   ├── src
│   │   ├── app
│   │   ├── components
│   │   └── lib
│   ├── tailwind.config.js
│   └── tsconfig.json
├── package.json
├── requirements.txt
├── scripts
│   ├── convert-assets.sh
│   ├── generate-api.sh
│   ├── package_cuda.py
│   ├── prepare-release.sh
│   ├── setup-dev-sidecar.js
│   ├── test_download_progress.py
│   └── update-icons.sh
├── tauri
│   ├── assets
│   │   ├── Voicebox_Microphone.png
│   │   ├── voicebox.icon
│   │   └── voicebox_exports
│   ├── index.html
│   ├── package.json
│   ├── src
│   │   ├── main.tsx
│   │   └── platform
│   ├── src-tauri
│   │   ├── Cargo.lock
│   │   ├── Cargo.toml
│   │   ├── Entitlements.plist
│   │   ├── Info.plist
│   │   ├── capabilities
│   │   ├── gen
│   │   ├── icons
│   │   ├── src
│   │   ├── tauri.conf.json
│   │   └── tests
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   └── vite.config.ts
└── web
    ├── index.html
    ├── package.json
    ├── src
    │   ├── main.tsx
    │   └── platform
    ├── tsconfig.json
    ├── tsconfig.node.json
    └── vite.config.ts
```

## 🏛️ 4. 架構與設計約定 (Architecture & Conventions)
* _（尚無 `.auto-skill-local.md`，專案踩坑經驗將在開發過程中自動累積）_

## 🚦 5. 目前進度與待辦 (Current Status & TODO)
_(自動提取自最近日記 2026-03-18)_

### 🚧 待辦事項
- [ ] 執行 `just setup` 安裝 Python 與 JS 依賴。
- [ ] 啟動 backend 並測試 `/health` 與 `/profiles` API。
- [ ] 開發初版的 `voicebox_tts` Claude Code 技能腳本。

