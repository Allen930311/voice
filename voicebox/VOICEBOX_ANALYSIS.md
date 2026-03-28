# Voicebox 儲存庫深度分析報告

Voicebox 是一個強大的「本地優先」語音克隆與 TTS 工作室，旨在成為 ElevenLabs 的開源替代方案。

## 🚀 核心亮點

- **隱私至上：** 所有模型推理均在本機執行，無需上傳音訊或使用雲端 API。
- **多引擎架構：** 支援 5 種 TTS 引擎（Qwen3-TTS, LuxTTS, Chatterbox, HumeAI TADA），各具優勢。
- **情感與語氣：** 透過 `[laugh]`, `[sigh]` 等標籤，語音表現力極強。
- **強大後處理：** 內建 8 種專業音效處理（如藍牙耳機、廣播電台風格）。
- **開發者友善：** 提供完整 REST API，支援非同步任務隊列與 SSE 即時狀態串流。

## 🏗️ 系統架構

- **前端：** React + TypeScript (Tauri 桌面應用)。
- **後端：** Python FastAPI (預設 Port 17493)。
- **推理端：** 
  - Mac: 優化 MLX (Neural Engine) 加速。
  - Windows: 支援 CUDA (NVIDIA), DirectML (通用 GPU), CPU。
- **資料庫：** SQLite (儲存 Profile 與歷史記錄)。

## 🛠️ Claude Code 工具化潛力

Voicebox 非常適合整合為 Claude Code 的自定義工具：

1.  **整合方式：** 透過 Python 腳本直接與 localhost API 通訊。
2.  **核心控制：** 
    - 啟動伺服器：`just dev-backend`
    - 取得語音清單：`GET /profiles`
    - 生成語音：`POST /generate`
3.  **自動化場景：** 
    - 在開發腳本或影片專案時，直接調用 `voicebox_tts` 生成旁白。
    - 克隆用戶語音作為專屬助理音色。

## 📂 專案結構

- `/backend`: Python FastAPI 伺服器與 TTS 推理邏輯。
- `/app`: React 前端代碼（由 Tauri 加載）。
- `/tauri`: Rust 代碼，負責桌面應用的系統層接口。
- `/packages`: 共享組件與工具類。

---
*分析日期：2026-03-18*
*分析工具：Antigravity Agent*
