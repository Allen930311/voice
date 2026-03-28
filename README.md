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
