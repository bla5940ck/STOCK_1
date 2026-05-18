# 🚀 LINE Bot 快速啟動指南

## 3 種方式啟動

### 方式 1️⃣ **最簡單 - 雙擊啟動**（推薦）

在文件管理器中找到：
- `START.bat` - 雙擊啟動所有服務
- `STOP.bat` - 雙擊停止所有服務

✨ **優點**：最簡單，適合日常使用

---

### 方式 2️⃣ **PowerShell 命令**

```powershell
# 啟動所有服務
cd C:\Users\bla59\OneDrive\Desktop\SDD\US_STOCK
powershell -ExecutionPolicy Bypass -File start-all.ps1

# 停止所有服務
powershell -ExecutionPolicy Bypass -File stop-all.ps1
```

---

### 方式 3️⃣ **手動命令**

```powershell
# 啟動 Docker
docker-compose up -d

# 啟動 Cloudflare Tunnel（新開終端）
$env:LOCALAPPDATA\cloudflared.exe tunnel --url http://localhost:8000
```

---

## 📋 完整流程

### 1️⃣ 啟動服務

**雙擊 `START.bat`** 或執行：
```powershell
powershell -ExecutionPolicy Bypass -File start-all.ps1
```

輸出應該顯示：
```
✅ Docker ready
✅ Docker containers started
✅ App ready (http://localhost:8000)
✅ Cloudflare Tunnel started
```

### 2️⃣ 複製 Tunnel URL

從終端窗口看到的 Cloudflare Tunnel 輸出，找到：
```
Your quick Tunnel has been created! Visit it at:
https://xxxx-xxxx-xxxx.trycloudflare.com
```

### 3️⃣ 設置 LINE Webhook

1. 進入：https://developers.line.biz/
2. 選擇你的 Channel
3. 進入 **Messaging API** 設定
4. 找到 **Webhook URL** 欄位
5. 貼入：`https://xxxx-xxxx-xxxx.trycloudflare.com/webhook/line`
6. 點擊「**驗證**」按鈕
7. 確保「**Use Webhook**」已開啟

### 4️⃣ 測試

在 LINE App 傳送訊息給你的 Bot：
- 💬 `AAPL` → 回傳股票資訊
- 💬 `美股` → 回傳美股指數
- 💬 `新聞` → 回傳最新新聞

### 5️⃣ 停止服務

**雙擊 `STOP.bat`** 或執行：
```powershell
powershell -ExecutionPolicy Bypass -File stop-all.ps1
```

---

## 🔍 訪問地址

啟動後可訪問：

| 服務 | 地址 |
|------|------|
| 應用程式 | http://localhost:8000 |
| API 文檔 | http://localhost:8000/docs |
| 健康檢查 | http://localhost:8000/health |
| Webhook | https://xxxx.trycloudflare.com/webhook/line |

---

## ✨ 優點（Cloudflare vs ngrok）

| 特性 | Cloudflare | ngrok |
|------|-----------|-------|
| URL 穩定性 | ✅ 固定 | ❌ 經常改變 |
| LINE 兼容性 | ✅ 很好 | ⚠️ 有限制 |
| 免費版限制 | ✅ 無限 | ❌ 有限制 |
| 設置複雜度 | ✅ 簡單 | 🟡 中等 |

---

## ❓ 常見問題

### ❌ "Docker not running"
→ 請先啟動 **Docker Desktop**

### ❌ "Webhook verification failed"
→ 確保：
   1. ✅ Cloudflare Tunnel 正在運行
   2. ✅ Webhook URL 正確（以 `/webhook/line` 結尾）
   3. ✅ 在 LINE 開發者平台點擊了「驗證」

### ❌ LINE 仍無反應
→ 檢查日誌：
   ```powershell
   docker logs linebot-us-stock --tail 20
   ```

### ❌ 要更改 Cloudflare URL？
→ 停止後重新啟動，會生成新的 URL

---

## 🆘 需要幫助？

檢查應用程式日誌：
```powershell
docker logs linebot-us-stock -f
```

檢查 Docker 狀態：
```powershell
docker ps
docker-compose logs
```

---

## 📊 架構

```
┌─────────────────┐
│  LINE App       │
└────────┬────────┘
         │
         │ HTTPS
         │
┌────────v────────────────────────┐
│  Cloudflare Tunnel               │
│  (https://xxxx.trycloudflare.com)│
└────────┬────────────────────────┘
         │
         │ HTTP
         │
┌────────v────────────────┐
│  Docker Container        │
│  FastAPI (8000)          │
│  - Webhook Handler       │
│  - Stock/News Services   │
│  - Database              │
└──────────────────────────┘
```

---

**準備好了！開始使用吧！** 🎉
