# Voicebox Workspace 🎙️

<p align="center">
  <strong>Local-first Voice Cloning Studio & AI Voice Ecosystem</strong><br/>
  克隆聲音、生成配音、音效處理、專案作曲 — 都在本地端完成。
</p>

---

## 🏗️ Project Structure | 專案架構

This repository is a unified workspace containing the Voicebox app, its MCP server, and automation scripts.
本儲存庫為整合工作區，包含 Voicebox 應用程式、MCP 伺服器與自動化腳本。

| Directory | Description | 描述 |
| :--- | :--- | :--- |
| **`voicebox/`** | The main desktop studio (React + Tauri + FastAPI). | Voicebox 桌面端主程式（專業配音室）。 |
| **`voicebox-mcp/`** | MCP Server for AI IDE integration (Claude/Antigravity). | 令 AI 助手（如 Claude）具備語音能力的 MCP 伺服器。 |
| **`scripts/`** | Python automation scripts for bulk cloning & testing. | 用於批量克隆、生成與測試的 Python 自動化腳本。 |

---

## ✨ Key Features | 核心功能

- **Local Voice Cloning**: Clone voices from seconds of audio with complete privacy.
- **Multi-Engine TTS**: Support for Qwen3-TTS, LuxTTS, Chatterbox, and TADA.
- **Audio Effects**: Reverb, delay, pitch shift, and more powered by Pedalboard.
- **Timeline Editor**: Compose multi-voice stories and narratives.
- **MCP Integration**: Control Voicebox directly from your AI agent/IDE.
- **API First**: Full REST API at `localhost:17493` for developers.

---

## 🚀 Quick Start | 快速開始

### Prerequisite: Setup Backend
To use the application or scripts, ensure the backend is set up:
使用應用程式或腳本前，請確保後端已安裝：

```bash
cd voicebox
just setup-python    # Install backend dependencies | 安裝後端依賴
just dev-backend     # Start the backend server   | 啟動後端伺服器 (Port 17493)
```

### Using MCP Server
To use Voicebox in your AI assistant (e.g., Claude), add the server:
在 AI 助手（如 Claude）中使用 Voicebox，請新增伺服器：

```bash
# In your IDE/Claude settings:
# 在您的 IDE/Claude 設定中加入：
claude mcp add voicebox --command "python c:/Users/Allen/OneDrive/Desktop/Voicebox/voicebox-mcp/server.py"
```

如果你之後需要重新開始生成，請執行：
powershell -File scripts/start-voicebox-gpu.ps1


這將會重新啟動後端並載入 GPU 加速引擎

在終端機中，你可以使用以下幾種方式來查看 Voicebox 的目前狀態：

1. 快速健康檢查 (Health Check)
這是最直接且建議的方式，可以查看後端是否運行中、GPU 是否可用、模型是否已載入等資訊。

PowerShell (推薦):

Invoke-RestMethod -Uri "http://127.0.0.1:17493/health" | ConvertTo-Json

cURL:

bash
curl http://127.0.0.1:17493/health

2. 查看工作任務與生成歷史 (Task History)
如果你想知道目前有沒有任務在執行（或者之前的生成是否成功），可以查看歷史紀錄：

PowerShell:

Invoke-RestMethod -Uri "http://127.0.0.1:17493/history?limit=5" | ConvertTo-Json

3. 查看即時日誌 (Real-time Logs)
如果你想看後端後台到底在跑什麼（例如編譯核心、載入模型進度），可以直接透過此專案配置的 just 指令：

just logs
或直接手動讀取日誌檔：

Get-Content backend/logs/*.log -Tail 50 -Wait
4. 查看模型下載/掛載狀態
確認哪些模型已經準備好，哪些還在下載：


Invoke-RestMethod -Uri "http://127.0.0.1:17493/models/status" | ConvertTo-Json

💡 實用小撇步
後端手動重啟：如果發現狀態卡死（例如 VRAM 溢出），專案內有一個重啟 GPU 模式的指令：
powershell
powershell -File scripts/start-voicebox-gpu.ps1
---

## 🛠️ Tech Stack | 技術棧

- **Frontend**: React, TypeScript, Tailwind CSS
- **Desktop**: Tauri (Rust)
- **Backend**: FastAPI (Python)
- **Inference**: PyTorch (CUDA/MLX/CPU)
- **Database**: SQLite

---

## 📝 License | 授權

MIT License — see [LICENSE](voicebox/LICENSE) for details.

---

<p align="center">
  Build with ❤️ by Allen (Forked from jamiepine/voicebox)
</p>
