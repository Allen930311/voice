# Voicebox Workspace 🎙️

<p align="center">
  <strong>Local-first Voice Cloning Studio & AI Voice Ecosystem</strong><br/>
  克隆聲音、生成配音、音效處理、專案作曲 — 都在本地端完成。
</p>

---

## 🏗️ Project Structure | 專案架構

This repository is a unified workspace containing the Voicebox app, its MCP server, and automation scripts.
本儲存庫為整合工作區，包含 Voicebox 應用程式、MCP 伺服器與自動化腳本。

| Directory / File | Description | 描述 |
| :--- | :--- | :--- |
| **`voicebox/`** | The main desktop studio (React + Tauri + FastAPI). | Voicebox 桌面端主程式（專業配音室）。 |
| **`voicebox-mcp/`** | MCP Server for AI IDE integration (Claude/Antigravity). | 令 AI 助手（如 Claude）具備語音能力的 MCP 伺服器。 |
| **`scripts/`** | Python automation scripts for bulk cloning & testing. | 用於批量克隆、生成與測試的 Python 自動化腳本。 |
| **`VOICE_PROFILES.md`** | **Source of Truth** for Voice IDs & Metadata. | 語音 ID 與元數據的**唯一真理來源**。 |
| **`AGENT_CONTEXT.md`** | AI Agent project context for rapid alignment. | AI 助手專用的專案上下文對齊文件。 |

---

## 🛡️ Reliability Protocol | 可靠性協議

### Atomic Sequential Processing (原子序列處理)
為了應對大規模生成任務（如 TOEIC 題庫），專案導入了 **Atomic Sequential** 處理模式：
- **Stop Batching**: 放棄不可控的批量提交，改採「單點提交、序列執行」。
- **Self-Polling**: 主動輪詢生成狀態，確保 100% 寫入成功後才進行下載。
- **Auto-Health Check**: 自動檢測 GPU VRAM 狀態，防止溢出。

---

## 🎓 Use Cases | 應用案例

- **TOEIC Learning Hub**: Daily quiz generation pipeline with automated narration.
  - **每日多益測驗自動化**：包含考題生成、多語音配音標註與同步下載。
- **Taiwan Flyover Video**: Automated narration for city flyover footage (MapTiler + 101 3D sync).
  - **台灣空拍解說**：結合 3D 建築與 AI 旁白，實現音影同步自動化。

---

## 🚀 Quick Start | 快速開始

### 1. Setup Backend | 初始化後端
```bash
cd voicebox
just setup-python    # Install dependencies | 安裝後端依賴
```

### 2. Run Server | 啟動伺服器
- **CPU Mode (Basic)**:
  `just dev-backend`
- **GPU Mode (Recommended for Intel Arc/NVIDIA)**:
  `powershell -File scripts/start-voicebox-gpu.ps1`

### 3. Setup MCP (for Claude/Antigravity)
```bash
claude mcp add voicebox --command "python c:/Users/Allen/OneDrive/Desktop/Voicebox/voicebox-mcp/server.py"
```

---

## 🚥 Diagnostics & Monitoring | 診斷與監控

使用以下方式查看連線與生成狀態：

- **Health Check (健康檢查)**:
  `Invoke-RestMethod -Uri "http://127.0.0.1:17493/health" | ConvertTo-Json`
  *確認後端運行、GPU 可用性與已載入模型。*

- **Task History (任務歷史)**:
  `Invoke-RestMethod -Uri "http://127.0.0.1:17493/history?limit=5" | ConvertTo-Json`
  *追蹤近期生成的成功/失敗狀態。*

- **Real-time Logs (即時日誌)**:
  `just logs` 或 `Get-Content backend/logs/*.log -Tail 50 -Wait`

---

## 🛠️ Tech Stack | 技術棧

- **Frontend**: React, TypeScript, Tailwind CSS
- **Desktop**: Tauri (Rust)
- **Backend**: FastAPI (Python)
- **Inference**: PyTorch (CUDA/Intel DirectML/CPU)
- **Audio Logic**: Pedalboard & FFmpeg
- **Database**: SQLite

---

## 📝 License | 授權

MIT License — see [LICENSE](voicebox/LICENSE) for details.

---

<p align="center">
  Build with ❤️ by Allen (Forked from jamiepine/voicebox)
</p>

