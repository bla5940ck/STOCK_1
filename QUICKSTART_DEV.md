# 🚀 LINE Bot 快速啟動指南

## 最快方式：一鍵啟動腳本

### 首次使用（3 步）

#### 1️⃣ 設置 ngrok Auth Token（只需一次）
```powershell
&"$env:LOCALAPPDATA\ngrok\ngrok.exe" config add-authtoken YOUR_TOKEN
```

#### 2️⃣ 執行啟動腳本
```powershell
cd C:\Users\bla59\OneDrive\Desktop\SDD\US_STOCK
powershell -ExecutionPolicy Bypass -File start-dev.ps1
```

#### 3️⃣ 設置 LINE Webhook URL
- 進入：https://developers.line.biz/
- 複製腳本輸出的 Webhook URL（格式：`https://xxxx.ngrok-free.dev/webhook/line`）
- 在 Messaging API 設定中貼入

---

## 常用命令

### ⏱️ 啟動所有服務（Docker + ngrok）
```powershell
powershell -ExecutionPolicy Bypass -File start-dev.ps1
```

### ⏱️ 只啟動 Docker（跳過 ngrok）
```powershell
powershell -ExecutionPolicy Bypass -File start-dev.ps1 -NoNgrok
```

### 🛑 停止所有服務
```powershell
powershell -ExecutionPolicy Bypass -File start-dev.ps1 -StopOnly
```

### 🧹 完全清理（停止 + 刪除容器和鏡像）
```powershell
powershell -ExecutionPolicy Bypass -File start-dev.ps1 -CleanUp
```

---

## 訪問地址

啟動後可訪問：

| 服務 | 地址 | 說明 |
|------|------|------|
| 應用程式 | `http://localhost:8000` | 本地開發 |
| API 文檔 | `http://localhost:8000/docs` | Swagger UI |
| 健康檢查 | `http://localhost:8000/health` | 檢查服務狀態 |
| ngrok 控制板 | `http://127.0.0.1:4040` | ngrok 隧道監控 |
| Webhook URL | `https://xxx.ngrok-free.dev/webhook/line` | LINE Webhook |

---

## 速度對比

| 方式 | 時間 | 複雜度 |
|------|------|--------|
| **一鍵腳本**（推薦） | ⚡ 5-10 秒 | 🟢 簡單 |
| 手動 Docker + ngrok | 30-60 秒 | 🟡 複雜 |
| 手動 + 手動設置 Webhook | 3-5 分鐘 | 🔴 很複雜 |

---

## 常見問題

### ❌ 腳本執行報錯："不允許運行腳本"

```powershell
# 解決：改變執行策略
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### ❌ ngrok 連接失敗

1. 檢查 Token 是否正確：`&"$env:LOCALAPPDATA\ngrok\ngrok.exe" config get-authtoken`
2. 重新設置 Token：`&"$env:LOCALAPPDATA\ngrok\ngrok.exe" config add-authtoken YOUR_NEW_TOKEN`

### ❌ Docker 容器啟動失敗

```powershell
# 檢查 Docker 狀態
docker ps

# 查看容器日誌
docker logs linebot-us-stock

# 重建容器
docker-compose up --build
```

### ❌ LINE 沒有反應

1. ✅ 確認 ngrok 正在運行（腳本會自動啟動）
2. ✅ 確認 Webhook URL 在 LINE 開發者平台已設置
3. ✅ 確認 Webhook URL 以 `/webhook/line` 結尾
4. ✅ 在 LINE 開發者平台點擊「驗證」按鈕

---

## 進階用法

### 使用 Make 命令

```bash
# 查看所有命令
make help

# 運行 Docker
make docker-up

# 運行測試
make test

# 檢查代碼質量
make lint
```

### 監控應用日誌

```powershell
# 實時查看 Docker 日誌
docker logs -f linebot-us-stock
```

### 訪問 Docker 容器

```powershell
# 進入容器 shell
docker exec -it linebot-us-stock bash

# 運行 Python 命令
docker exec linebot-us-stock python -m pytest
```

---

## 下次啟動

只需執行：
```powershell
powershell -ExecutionPolicy Bypass -File start-dev.ps1
```

一切會自動設置！ 🎉
