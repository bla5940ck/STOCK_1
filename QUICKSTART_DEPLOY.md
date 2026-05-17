# 部署快速開始指南 (5分鐘)

## 🚀 最快開始方式

### 0. 前置條件
```bash
# 需要安裝
✓ Docker
✓ Docker Compose
✓ Git
```

**檢查是否已安裝:**
```powershell
docker --version
docker-compose --version
```

---

## ⚡ 方式 1: 使用 Docker Compose (推薦 - 最簡單)

### 第 1 步: 複製環境變數
```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

### 第 2 步: 編輯 `.env` 文件
打開 `.env`，填入 LINE Bot 的密鑰:

```env
# 必需項 - 從 LINE 管理控台獲取
LINE_CHANNEL_SECRET=your_channel_secret_here
LINE_CHANNEL_ACCESS_TOKEN=your_channel_access_token_here

# 可選項 (默認值足夠)
DATABASE_URL=sqlite:///./app.db
ENVIRONMENT=development
LOG_LEVEL=INFO
```

**如何獲取 LINE 密鑰:**
1. 進入 https://manager.line.biz/
2. 選擇你的 Bot
3. 進入 "Basic Settings"
4. 複製 "Channel Secret" 和 "Channel Access Token"

### 第 3 步: 啟動應用
```bash
# 啟動 (會自動下載鏡像、構建、運行)
docker-compose up -d

# 查看日誌
docker-compose logs -f app

# 停止
docker-compose down
```

### 第 4 步: 驗證運行
```bash
# 檢查狀態
docker-compose ps

# 測試 API
curl http://localhost:8000/health
# 應該返回: {"status": "healthy", ...}
```

✅ **完成！** 應用運行於 `http://localhost:8000`

---

## 📝 方式 2: 本地開發 (不用 Docker)

### 安裝 Python 依賴
```bash
# 創建虛擬環境
python -m venv venv

# 激活 (Windows)
venv\Scripts\activate

# 激活 (macOS/Linux)
source venv/bin/activate

# 安裝依賴
pip install -r requirements.txt
```

### 運行應用
```bash
# 設置環境變數 (Windows)
set LINE_CHANNEL_SECRET=your_secret_here
set LINE_CHANNEL_ACCESS_TOKEN=your_token_here

# 或編輯 .env 文件

# 啟動服務器
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 訪問
# API Docs: http://localhost:8000/docs
# Health: http://localhost:8000/health
```

---

## 🐳 Docker 常用命令

### 基本命令

```bash
# 構建鏡像
docker build -t us-stock:latest .

# 運行容器 (開發)
docker run -p 8000:8000 \
  -e LINE_CHANNEL_SECRET=your_secret \
  -e LINE_CHANNEL_ACCESS_TOKEN=your_token \
  us-stock:latest

# 查看運行中的容器
docker ps

# 查看所有容器 (包括已停止)
docker ps -a

# 停止容器
docker stop <container_id>

# 刪除容器
docker rm <container_id>

# 查看日誌
docker logs <container_id>
docker logs -f <container_id>  # 即時追蹤
```

### 使用 Docker Compose

```bash
# 啟動所有服務 (後台)
docker-compose up -d

# 啟動服務 (前台，看日誌)
docker-compose up

# 查看服務狀態
docker-compose ps

# 查看服務日誌
docker-compose logs -f app        # 應用日誌
docker-compose logs -f postgres   # 數據庫日誌

# 停止服務
docker-compose stop

# 完全移除 (包括數據卷)
docker-compose down -v

# 重啟服務
docker-compose restart app

# 查看執行統計
docker stats
```

---

## 📊 配置說明

### docker-compose.yml 結構

```yaml
services:
  app:
    # FastAPI 應用容器
    build: .                          # 從本地 Dockerfile 構建
    ports:
      - "8000:8000"                   # 映射端口
    environment:                      # 環境變數
      - DATABASE_URL=sqlite:///./app.db
    volumes:
      - ./src:/app/src                # 開發時自動重載
      - ./logs:/app/logs              # 持久化日誌
    command: uvicorn src.main:app ... # 啟動命令

  postgres:
    # 可選: PostgreSQL 數據庫
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: linebot
      POSTGRES_PASSWORD: password     # ⚠️ 改為安全密碼
      POSTGRES_DB: linebot_db
    ports:
      - "5432:5432"
    profiles:
      - postgres                      # 默認不啟動
```

### 啟用 PostgreSQL

```bash
# 使用 postgres profile 啟動
docker-compose --profile postgres up -d

# 編輯 .env
DATABASE_URL=postgresql://linebot:password@postgres:5432/linebot_db

# 重啟應用
docker-compose restart app
```

---

## 🔧 常見問題

### Q1: 如何修改端口?

編輯 `docker-compose.yml`:
```yaml
services:
  app:
    ports:
      - "9000:8000"  # 改為 9000
```

然後重啟:
```bash
docker-compose up -d
# 訪問 http://localhost:9000
```

### Q2: 如何查看日誌?

```bash
# 最後 100 行
docker-compose logs app

# 即時追蹤
docker-compose logs -f app

# 查看應用日誌文件
docker-compose exec app cat /app/logs/app.log
```

### Q3: 容器無法啟動？

```bash
# 查看詳細錯誤
docker-compose logs app

# 通常原因:
# 1. 環境變數缺失 (.env 文件未配置)
# 2. 端口已被佔用 (8000 被其他應用用了)
# 3. Docker daemon 未運行

# 解決:
# 確保 .env 存在且有 LINE_CHANNEL_SECRET
# 改變端口: docker-compose.yml - ports
# 重啟 Docker Desktop
```

### Q4: 如何檢查數據庫連接?

```bash
# 進入容器
docker-compose exec app bash

# 在容器內測試
python -c "from src.db.database import engine; print('DB OK')"

# 退出
exit
```

### Q5: 如何保存數據?

```bash
# Docker 卷自動保存
# 數據位置:
# - SQLite: ./app.db (主機映射)
# - PostgreSQL: docker 卷 (自動管理)

# 備份 SQLite
docker-compose exec app cp app.db app.db.backup

# 查看卷
docker volume ls
```

---

## 🌐 部署到生產環境

### 使用雲平臺

**AWS EC2 / Lightsail:**
```bash
# 1. 連接到 VM
ssh -i key.pem ec2-user@your-ip

# 2. 安裝 Docker
curl https://get.docker.com | sh

# 3. 克隆項目
git clone <your-repo>
cd us-stock

# 4. 配置 .env
nano .env
# 填入: LINE_CHANNEL_SECRET, LINE_CHANNEL_ACCESS_TOKEN

# 5. 啟動
docker-compose up -d

# 6. 配置域名和 HTTPS
# 使用 Nginx 或 CloudFlare
```

**Heroku (已棄用，但參考):**
```bash
# 使用 heroku.yml 部署
git push heroku main
```

**Google Cloud Run:**
```bash
# 推送到 Container Registry
docker build -t gcr.io/YOUR-PROJECT/us-stock:latest .
docker push gcr.io/YOUR-PROJECT/us-stock:latest

# 在 Cloud Run 部署
gcloud run deploy us-stock \
  --image gcr.io/YOUR-PROJECT/us-stock:latest \
  --platform managed \
  --region us-central1 \
  --set-env-vars LINE_CHANNEL_SECRET=xxx
```

### 配置 Webhook URL

**LINE 管理控台:**
1. 進入 https://manager.line.biz/
2. 選擇你的 Bot
3. 進入 "Messaging API" → "Webhook"
4. 填入 Webhook URL:
   ```
   https://your-domain.com/webhook/line
   ```
5. 啟用 "Use Webhook"

---

## ✅ 驗證部署

### 檢查清單

```bash
# 1. 應用運行
curl http://localhost:8000/health
# Expected: {"status": "healthy", ...}

# 2. API 文檔
open http://localhost:8000/docs
# 應看到 Swagger UI

# 3. 日誌輸出
docker-compose logs app
# 應看到啟動消息，無 ERROR

# 4. 測試查詢 (可選)
# 在 LINE App 中發送消息:
# - 輸入: "美股"
# - 期望: 收到指數回覆

# 5. 數據庫
docker-compose exec app ls -la app.db
# 應看到數據庫文件
```

---

## 📞 需要幫助?

查看詳細文檔:
- **DEPLOYMENT.md** - 完整部署指南
- **ARCHITECTURE.md** - 系統設計和架構
- **API_REFERENCE.md** - API 文檔
- **logs/app.log** - 應用日誌文件

常見命令速查表:
```bash
# 啟動應用
docker-compose up -d

# 查看日誌
docker-compose logs -f app

# 停止應用
docker-compose down

# 重啟應用
docker-compose restart app

# 進入容器
docker-compose exec app bash

# 查看狀態
docker-compose ps
```

---

**祝部署順利！** 🎉

如有問題，查看 `docker-compose logs app` 的錯誤信息。
