# 免費雲平台部署指南

## 推薦平台對比

| 平台 | 免費額度 | 數據庫 | HTTPS | 推薦 |
|------|---------|--------|--------|------|
| **Railway** | $5/月 | PostgreSQL ✅ | ✅ 自動 | ⭐⭐⭐ 最佳 |
| **Render** | 有限 | PostgreSQL ✅ | ✅ 自動 | ⭐⭐⭐ 次佳 |
| **Fly.io** | $3/月 | SQLite | ✅ 自動 | ⭐⭐ |
| **Google Cloud Run** | 按用量 | Cloud SQL | ✅ 自動 | ⭐⭐ 複雜 |

---

## 方案一：Railway (推薦) ⭐⭐⭐

### 步驟 1：準備 GitHub 倉庫

```bash
# 初始化 Git (如果未初始化)
cd c:\Users\bla59\OneDrive\Desktop\SDD\US_STOCK
git init
git add .
git commit -m "Initial commit"
```

### 步驟 2：創建 GitHub 帳號並推送代碼

```bash
# 在 GitHub 創建新倉庫 (不包含 README)
# 然後執行:
git remote add origin https://github.com/YOUR_USERNAME/us-stock-bot.git
git branch -M main
git push -u origin main
```

### 步驟 3：部署到 Railway

1. 訪問 https://railway.app
2. 點擊 **Start New Project**
3. 選擇 **GitHub Repo** → 授權並選擇 `us-stock-bot`
4. Railway 會自動檢測 `Dockerfile` 並構建

### 步驟 4：配置環境變數

在 Railway 儀表板中設置：

```
LINE_CHANNEL_SECRET=你的_LINE_SECRET
LINE_CHANNEL_ACCESS_TOKEN=你的_LINE_TOKEN
DATABASE_URL=自動生成的 PostgreSQL URL
ENVIRONMENT=production
```

### 步驟 5：綁定 PostgreSQL 數據庫

1. **New → Database → PostgreSQL**
2. Railway 會自動設置 `DATABASE_URL`
3. 無需手動配置

### 步驟 6：獲取公網 URL

```
Railway 儀表板 → 你的應用 → Deployments → Domain
複製生成的 URL (例如: https://us-stock-bot-prod.up.railway.app)
```

### 步驟 7：配置 LINE Webhook

1. 打開 [LINE Developers Console](https://developers.line.biz/console/)
2. 選擇你的 Bot
3. **Messaging API** → **Webhook URL**
4. 輸入: `https://你的_RAILWAY_URL/webhook/line`
5. 勾選 **Use webhook**
6. 測試連接 → 應顯示 200 OK

### ✅ 部署完成！

成本：**$5/月** (Railway 免費額度包含)

---

## 方案二：Render 

### 步驟 1-2：同 Railway 一樣推送到 GitHub

### 步驟 3：連接 Render

1. 訪問 https://render.com
2. 點擊 **New +** → **Web Service**
3. 連接 GitHub 倉庫
4. 設置名稱和地區

### 步驟 4：配置部署

```
Build Command: docker build -t us-stock .
Start Command: python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### 步驟 5：添加環境變數

**Environment** 標籤:
- `LINE_CHANNEL_SECRET`
- `LINE_CHANNEL_ACCESS_TOKEN`
- `DATABASE_URL` (連接到 PostgreSQL)

### 步驟 6：連接 PostgreSQL 數據庫

1. **New +** → **PostgreSQL**
2. Render 會自動為 Web Service 設置 `DATABASE_URL`

### 步驟 7：獲取部署 URL

```
https://你的-app-name.onrender.com
```

### 配置 LINE Webhook

同 Railway 的步驟 7

### ⚠️ 注意

- **免費層會在 15 分鐘無活動後休眠**
- LINE Bot 定期檢查可避免休眠
- 付費後可移除此限制

---

## 方案三：Fly.io (對 LINE Bot 不太適合)

Fly.io 缺少免費的完全管理數據庫，建議選擇 Railway 或 Render。

---

## 部署檢查清單

### 部署前

- [ ] 代碼已提交到 GitHub
- [ ] `.env.example` 已創建（不含敏感信息）
- [ ] `Dockerfile` 已配置
- [ ] `requirements.txt` 已更新
- [ ] LINE Bot 密鑰已準備

### 部署中

- [ ] 應用構建成功
- [ ] 環境變數已設置
- [ ] 數據庫已連接
- [ ] 健康檢查通過 (`/health`)

### 部署後

- [ ] 公網 URL 可訪問
- [ ] LINE Webhook URL 已配置
- [ ] LINE 測試消息成功
- [ ] 日誌中無錯誤

---

## 常見問題

### Q1: 如何查看部署日誌？

**Railway:**
```
Deployments → Logs 標籤
```

**Render:**
```
Service → Logs 標籤
```

### Q2: 數據庫遷移如何執行？

在 Railway/Render 中添加部署前命令：

```
python src/db/init_db.py
```

### Q3: 如何更新已部署的應用？

```bash
git add .
git commit -m "Update feature"
git push origin main
```

Railway/Render 會自動重新部署。

### Q4: 成本會超過免費額度嗎？

- **Railway**: $5/月免費額度足夠小型 Bot
- **Render**: 免費層有限制，超額需付費
- 建議設置成本告警

### Q5: 如何備份數據庫？

**Railway:**
```bash
# 使用 Railway CLI
railway database backup create
```

**Render:**
```
Database → Backups 標籤
```

---

## 快速開始腳本 (Railway)

將以下內容保存為 `deploy.sh`:

```bash
#!/bin/bash

# 1. 初始化 Git
git init
git add .
git commit -m "Initial commit"

# 2. 創建遠程倉庫 (手動在 GitHub 上創建)
# git remote add origin https://github.com/YOUR_USERNAME/us-stock-bot.git
# git push -u origin main

# 3. 訪問 Railway 應用
# https://railway.app

# 4. 連接 GitHub 倉庫

# 5. 配置環境變數
echo "Set these in Railway Dashboard:"
echo "  LINE_CHANNEL_SECRET"
echo "  LINE_CHANNEL_ACCESS_TOKEN"

# 6. 添加 PostgreSQL 數據庫

# 7. 獲取部署 URL 並配置 LINE Webhook

echo "Deployment process:"
echo "1. Push code to GitHub"
echo "2. Railway auto-detects Dockerfile"
echo "3. Builds and deploys automatically"
echo "4. Update LINE Webhook URL"
```

---

## 推薦流程 (5-10 分鐘)

1. **GitHub** (2分鐘)
   - 創建帳號
   - 推送代碼

2. **Railway** (5分鐘)
   - 連接 GitHub
   - 添加 PostgreSQL
   - 設置環境變數
   - 獲取部署 URL

3. **LINE Console** (2分鐘)
   - 配置 Webhook URL
   - 測試連接

4. **測試** (1分鐘)
   - 在 LINE 中查詢股票
   - 檢查日誌無誤

**總耗時：10-15 分鐘** ✅

---

## 監控和維護

### 查看實時日誌

**Railway:**
```
應用儀表板 → Logs
```

**Render:**
```
應用頁面 → Logs
```

### 設置告警

- CPU 使用率 > 80%
- 內存使用率 > 70%
- 錯誤率 > 1%
- 數據庫連接失敗

### 定期備份

```bash
# Railway 備份
railway database backup list
railway database backup create
```

---

## 成本估算（月度）

| 服務 | 免費額度 | 超額成本 |
|------|---------|---------|
| Railway | $5 | $0.000463/秒 |
| PostgreSQL | 100 連接 | 包含在額度內 |
| HTTPS | ✅ 免費 | - |
| 頻寬 | 無限制 | 包含在額度內 |

**總成本：$0-5/月** (取決於使用量)

---

## 需要幫助？

- **Railway 文檔**: https://docs.railway.app
- **Render 文檔**: https://render.com/docs
- **LINE Bot 文檔**: https://developers.line.biz/en/

祝部署順利！🚀
