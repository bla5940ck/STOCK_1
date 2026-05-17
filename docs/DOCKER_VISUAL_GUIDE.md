# Docker 和部署視覺流程

## 🎯 快速決策樹

```
你想要什麼?
│
├─ 🚀 快速啟動 (5分鐘內運行)
│  └─> 使用 Docker Compose
│      $ docker-compose up -d
│      訪問 http://localhost:8000/health
│
├─ 💻 本地開發 (修改代碼)
│  └─> 不用 Docker
│      1. pip install -r requirements.txt
│      2. 編輯 .env
│      3. uvicorn src.main:app --reload
│
├─ 🌍 部署到服務器 (AWS/GCP/雲)
│  └─> Docker + docker-compose
│      1. 在服務器上安裝 Docker
│      2. git clone 項目
│      3. 編輯 .env
│      4. docker-compose up -d
│      5. 配置 Webhook URL
│
└─ 📊 使用 PostgreSQL 數據庫
   └─> 修改 docker-compose.yml
       docker-compose --profile postgres up -d
```

---

## 🐳 Docker 工作流程 (概念圖)

```
┌─────────────────────────────────────────────┐
│          你的本機/服務器                       │
└─────────────────────────────────────────────┘
              ↓
         docker-compose.yml
              ↓
    ┌─────────────────────────┐
    │   Docker Engine         │
    │ ┌─────────────────────┐ │
    │ │ 應用容器 (FastAPI) │ │
    │ │ - 端口: 8000      │ │
    │ │ - Python 3.11     │ │
    │ │ - 依賴已安裝       │ │
    │ └─────────────────────┘ │
    │ ┌─────────────────────┐ │
    │ │ PostgreSQL容器      │ │  (可選)
    │ │ - 端口: 5432       │ │
    │ │ - 數據卷持久化      │ │
    │ └─────────────────────┘ │
    └─────────────────────────┘
              ↓
    ┌─────────────────────────┐
    │   外部訪問              │
    │ - http://localhost:8000 │
    │ - LINE Bot Webhook      │
    │ - API Endpoints         │
    └─────────────────────────┘
```

---

## 📋 三種部署方式對比

### 方式 1️⃣: Docker Compose (推薦)

```
優點:
✅ 最快 (5 分鐘)
✅ 包含所有依賴
✅ 一鍵啟動/停止
✅ 易於管理多個容器
✅ 可複制到任何服務器

缺點:
❌ 需要安裝 Docker
❌ 容器鏡像較大 (~420MB)

用途:
🎯 生產部署
🎯 團隊協作
🎯 服務器部署
🎯 快速原型

命令:
$ docker-compose up -d
$ docker-compose logs -f app
$ docker-compose down
```

### 方式 2️⃣: 本地開發 (無 Docker)

```
優點:
✅ 不需要 Docker
✅ 快速修改代碼
✅ 易於調試
✅ 輕量級

缺點:
❌ 需要 Python 3.11
❌ 環境配置複雜
❌ 每臺機器要裝依賴
❌ 難以複制環境

用途:
🎯 開發和測試
🎯 修改源代碼
🎯 調試錯誤

命令:
$ pip install -r requirements.txt
$ uvicorn src.main:app --reload
```

### 方式 3️⃣: 裸機/VM 部署 (高級)

```
優點:
✅ 完全控制
✅ 可優化性能
✅ 與系統深度集成

缺點:
❌ 配置複雜
❌ 環境差異大
❌ 易出錯

用途:
🎯 大規模部署
🎯 性能優化
🎯 企業級部署

步驟:
1. 安裝 Python 3.11 + PostgreSQL
2. git clone 項目
3. pip install
4. 配置系統服務 (systemd)
5. 配置反向代理 (Nginx)
```

---

## 🚀 快速命令參考

### 使用 Docker Compose

```bash
# 初始化
docker-compose up -d

# 查看狀態
docker-compose ps

# 查看日誌 (即時)
docker-compose logs -f app

# 停止
docker-compose stop

# 重啟
docker-compose restart app

# 完全移除
docker-compose down

# 進入容器
docker-compose exec app bash

# 查看應用日誌文件
docker-compose exec app tail -f logs/app.log
```

### 使用 Docker CLI

```bash
# 構建鏡像
docker build -t us-stock:latest .

# 列出所有鏡像
docker images

# 運行容器
docker run -p 8000:8000 us-stock:latest

# 列出運行中的容器
docker ps

# 查看日誌
docker logs <container_id> -f

# 停止容器
docker stop <container_id>

# 刪除容器
docker rm <container_id>
```

---

## 📁 文件結構

```
us-stock/
├── docker-compose.yml          ← Docker 配置 (多容器)
├── Dockerfile                  ← 應用容器定義
├── .env.example                ← 環境變數模板
├── .env                        ← 實際環境變數 (不上傳)
├── requirements.txt            ← Python 依賴列表
├── src/                        ← 應用源代碼
│   ├── main.py                 ← FastAPI 主程序
│   ├── config.py               ← 配置加載
│   ├── handlers/               ← 查詢處理器
│   ├── services/               ← 業務邏輯
│   ├── integrations/           ← 外部 API 客戶端
│   ├── db/                     ← 數據庫層
│   └── utils/                  ← 工具函數
├── tests/                      ← 測試代碼
├── logs/                       ← 應用日誌 (自動創建)
└── QUICKSTART_DEPLOY.md        ← 本指南
```

---

## ⚙️ 環境變數配置

### 最小配置 (.env)

```env
# LINE Bot 配置 (必需)
LINE_CHANNEL_SECRET=your_channel_secret_from_line
LINE_CHANNEL_ACCESS_TOKEN=your_channel_access_token_from_line

# 數據庫 (可選)
DATABASE_URL=sqlite:///./app.db

# 服務器 (可選)
HOST=0.0.0.0
PORT=8000

# 日誌 (可選)
LOG_LEVEL=INFO
```

### 生產配置

```env
# LINE
LINE_CHANNEL_SECRET=xxxxxxxxxxxxxxxxxxxx
LINE_CHANNEL_ACCESS_TOKEN=xxxxxxxxxxxxxxxxxxxx

# 數據庫 (使用 PostgreSQL)
DATABASE_URL=postgresql://user:password@db.example.com:5432/us_stock

# 服務器
ENVIRONMENT=production
LOG_LEVEL=WARNING

# 可選: Alpha Vantage (用於指數回退)
ALPHA_VANTAGE_API_KEY=your_api_key
```

---

## 🔍 診斷命令

當出問題時:

```bash
# 1. 檢查容器狀態
docker-compose ps

# 2. 查看詳細錯誤
docker-compose logs app | head -50

# 3. 檢查環境變數
docker-compose exec app env | grep LINE

# 4. 測試 API
curl http://localhost:8000/health

# 5. 進入容器調試
docker-compose exec app bash
$ python -c "from src.main import app; print('OK')"
$ exit

# 6. 檢查內存使用
docker stats

# 7. 檢查磁盤使用
docker-compose exec app du -sh /app

# 8. 查看 Docker 網絡
docker network ls
docker network inspect linebot-network
```

---

## 🌐 Webhook URL 配置

部署後必須配置 LINE Bot 的 Webhook:

### 本地開發
```
Webhook URL: http://localhost:8000/webhook/line
(只能在本機測試，不能被 LINE 服務器訪問)
```

### 部署到服務器
```
Webhook URL: https://your-domain.com/webhook/line
(確保使用 HTTPS!)
```

### 配置步驟
1. 進入 https://manager.line.biz
2. 選擇 Bot
3. 進入 "Messaging API"
4. 找到 "Webhook"
5. 填入你的 URL
6. 點擊 "Verify"
7. 切換開關為 "Enable"

---

## 💾 數據備份

### SQLite 備份
```bash
# 備份 (生成 app.db.backup)
docker-compose exec app cp app.db app.db.backup

# 查看備份
docker-compose exec app ls -lh app.db*
```

### PostgreSQL 備份
```bash
# 備份數據庫
docker-compose exec postgres pg_dump -U linebot linebot_db > backup.sql

# 恢復備份
cat backup.sql | docker-compose exec -T postgres psql -U linebot linebot_db
```

---

## 📈 監控和日誌

### 實時監控
```bash
# 查看所有容器狀態
docker stats

# 查看應用日誌 (實時)
docker-compose logs -f app

# 只看最後 50 行
docker-compose logs -f app --tail 50
```

### 日誌文件位置
```bash
# 容器內日誌
docker-compose exec app cat logs/app.log

# 主機上日誌
./logs/app.log

# Docker 系統日誌
docker logs <container_id>
```

---

## 🎓 學習資源

### 推薦閱讀
- [QUICKSTART_DEPLOY.md](./QUICKSTART_DEPLOY.md) - 5分鐘快速開始
- [DEPLOYMENT.md](./DEPLOYMENT.md) - 完整部署指南
- [ARCHITECTURE.md](./ARCHITECTURE.md) - 系統架構設計
- [API_REFERENCE.md](./API_REFERENCE.md) - API 文檔

### 官方文檔
- [Docker 官方文檔](https://docs.docker.com/)
- [Docker Compose 指南](https://docs.docker.com/compose/)
- [LINE Messaging API](https://developers.line.biz/zh-hant/)

---

**祝部署順利！** 🚀

有問題？查看日誌: `docker-compose logs -f app`
