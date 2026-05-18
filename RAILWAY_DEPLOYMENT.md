# 🚀 部署到 Railway 完整指南

## 📋 前置要求
- ✅ GitHub 帳號（用來部署）
- ✅ 這個代碼在 GitHub 上（private 或 public）
- ✅ LINE Channel Secret 和 Access Token

## 🎯 部署步驟（15 分鐘）

### **第 1 步：準備 GitHub 倉庫**

#### A. 如果還沒上傳到 GitHub：
```powershell
cd C:\Users\bla59\OneDrive\Desktop\SDD\US_STOCK

# 初始化 Git（如果還沒的話）
git init

# 添加所有檔案
git add .

# 提交
git commit -m "Initial commit: LINE Stock Bot"

# 連接遠程倉庫（用你自己的倉庫 URL）
git remote add origin https://github.com/YOUR_USERNAME/linebot-us-stock.git

# 推送到 GitHub
git branch -M main
git push -u origin main
```

#### B. 如果已經在 GitHub：
只需確保最新代碼已推送：
```powershell
git push
```

---

### **第 2 步：連接 Railway**

1. **去 https://railway.app/**
2. 點 **"Login with GitHub"** 或 **"Sign Up"**
3. 授權 Railway 存取你的 GitHub
4. 點 **"Create a new Project"**
5. 選 **"Deploy from GitHub repo"**
6. 選你的倉庫：`YOUR_USERNAME/linebot-us-stock`
7. Railway 會自動偵測到 `Dockerfile`，點 **"Deploy"**

---

### **第 3 步：配置環境變數**

部署開始後，進入 **"Variables"** 分頁，添加：

```
LINE_CHANNEL_SECRET=966320d380a1845e004061caf51fe757
LINE_CHANNEL_ACCESS_TOKEN=你的_access_token
TWELVE_DATA_API_KEY=demo
PORT=8000
ENVIRONMENT=production
```

**怎麼找 Access Token：**
1. 去 https://developers.line.biz/
2. 選你的 Bot
3. 進 **"Messaging API"** 分頁
4. 找 **"Channel Access Token"** → 複製

---

### **第 4 步：取得 Railway 公開 URL**

部署完後：
1. 進入 Railway 專案
2. 進入 **"Deployments"** 分頁
3. 找 **"View Logs"** 中的公開 URL，看起來像：
```
https://linebot-us-stock-production-abcd.up.railway.app
```

4. 你的 Webhook URL 是：
```
https://linebot-us-stock-production-abcd.up.railway.app/webhook/line
```

---

### **第 5 步：更新 LINE 設置**

1. 去 https://developers.line.biz/
2. 進 **"Messaging API"** 分頁
3. 找 **"Webhook Settings"**
4. 更新 **"Webhook URL"** 為 Railway 的 URL：
```
https://linebot-us-stock-production-abcd.up.railway.app/webhook/line
```
5. 點 **"Verify"** → 應該顯示 ✅ Success
6. 勾選 **"Use webhook"**

---

### **第 6 步：測試**

在 LINE Bot 中發送：
- `2330` → 應該返回台積電股票數據
- `AAPL` → 應該返回 Apple 股票數據
- `健策` → 應該返回健策股票數據

---

## 🆘 常見問題

### **Q: 部署失敗？**
進入 Railway 的 **"Logs"** 分頁查看錯誤訊息

### **Q: 如何查看實時日誌？**
在 Railway 專案中，點 **"View Logs"**

### **Q: 如何更新代碼？**
直接 `git push` 到 GitHub，Railway 會自動重新部署

### **Q: 如何添加 API Keys？**
1. 進入 Railway 專案
2. 進入 **"Variables"** 分頁
3. 添加或更新環境變數
4. Railway 會自動重新部署

---

## 📊 架構圖

```
GitHub → Railway (自動部署)
         ↓
    Docker Container
         ↓
    FastAPI Server (port 8000)
         ↓
    LINE Messaging API ← 你的 Bot
```

---

## 💡 下一步（可選）

- 添加 Finnhub / Alpha Vantage API Keys 提升查詢準確度
- 配置 PostgreSQL 數據庫（而不是 SQLite）
- 設置告警功能（股票價格達到目標時通知）

---

需要幫助嗎？告訴我！
