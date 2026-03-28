# Voicebox MCP — 個人配音室

將本地 Voicebox TTS/語音克隆引擎暴露為 Claude Code 可直接調用的 MCP 工具。

## 前置條件

1. **Voicebox 後端已設置**：在 `voicebox/` 目錄執行過 `just setup-python`
2. **Python 依賴**：`pip install "mcp[cli]" httpx`

## 啟動方式

### Step 1: 啟動 Voicebox 後端
```powershell
cd c:\Users\Allen\OneDrive\Desktop\Voicebox\voicebox
just dev-backend
# 或
powershell -File ..\voicebox-mcp\start-backend.ps1
```

### Step 2: MCP Server 自動啟動
MCP server 已註冊為 Claude Code 全域工具，會在 Claude Code 啟動時自動運行。

## 可用工具

| 工具 | 說明 |
|------|------|
| `voicebox_status` | 檢查後端是否運行 |
| `voicebox_clone_voice` | **一鍵克隆聲音**（建 Profile + 上傳音訊 + 自動轉錄） |
| `voicebox_generate` | 用克隆的聲音生成配音 |
| `voicebox_download_audio` | 下載生成的音訊檔 |
| `voicebox_list_profiles` | 列出所有語音 Profile |
| `voicebox_get_profile` | 查看 Profile 詳情 |
| `voicebox_create_profile` | 建立空白 Profile |
| `voicebox_add_sample` | 為 Profile 新增參考音訊 |
| `voicebox_delete_profile` | 刪除 Profile |
| `voicebox_export_profile` | 匯出 Profile (ZIP) |
| `voicebox_import_profile` | 匯入 Profile (ZIP) |
| `voicebox_history` | 查看生成歷史 |
| `voicebox_list_models` | 列出模型下載狀態 |
| `voicebox_download_model` | 下載 TTS 模型 |
| `voicebox_list_effects` | 列出可用音效 |
| `voicebox_apply_effects` | 對音訊套用音效 |
| `voicebox_transcribe` | 語音轉文字 (STT) |
| `voicebox_create_story` | 建立配音專案 (Story) |
| `voicebox_add_to_story` | 將配音加入 Story |

## 典型使用流程

### 克隆聲音
```
「幫我克隆這個聲音：C:\voices\my_voice.wav，名稱叫 Allen」
→ Claude 自動呼叫 voicebox_clone_voice
```

### 生成配音
```
「用 Allen 的聲音唸這段：歡迎來到我們的頻道」
→ Claude 查找 Profile → 呼叫 voicebox_generate
```

### 影片配音工作流
```
「這是我的影片腳本，幫我用 Allen 的聲音生成所有旁白，存到 C:\project\audio\」
→ Claude 逐段生成 → 下載到指定目錄
```

## 支援的 TTS 引擎

| 引擎 | 語言 | 特色 |
|------|------|------|
| Qwen TTS | 13 語言 | 高品質、快速 |
| LuxTTS | 英文 | 極快速 |
| Chatterbox | 23 語言 | 自然度高 |
| Chatterbox Turbo | 英文 | 支援語音指令 |
| TADA | 10 語言 | 最高品質 |

## 檔案結構

```
voicebox-mcp/
├── server.py           # MCP server 主程式
├── start-backend.ps1   # 後端啟動腳本
└── README.md           # 本文件
```
