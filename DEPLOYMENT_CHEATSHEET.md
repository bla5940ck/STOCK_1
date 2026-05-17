# ⚡ 部署速查表 - 複製粘貼直接用

## 🎯 三種快速開始 (選一個)

### 方式 A: 最快 (Docker Compose, 推薦)
```bash
# 1. 複製環境文件
copy .env.example .env        # Windows
cp .env.example .env          # Mac/Linux

# 2. 編輯 .env (用你的 LINE 密鑰)
# LINE_CHANNEL_SECRET=your_secret_here
# LINE_CHANNEL_ACCESS_TOKEN=your_token_here

# 3. 一鍵啟動
docker-compose up -d

# 4. 驗證
curl http://localhost:8000/health

# 5. 查看日誌
docker-compose logs -f app
```

### 方式 B: 本地開發 (無 Docker)
```bash
# 1. 創建虛擬環境
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 編輯 .env

# 4. 啟動
uvicorn src.main:app --reload

# 訪問: http://localhost:8000/docs
```

### 方式 C: 服務器部署 (Ubuntu/CentOS)
```bash
# 1. 安裝 Docker
curl https://get.docker.com | sh
sudo usermod -aG docker $USER

# 2. 克隆項目
git clone <your-repo-url>
cd us-stock

# 3. 編輯 .env

# 4. 啟動
docker-compose up -d

# 5. 配置 Webhook URL
# 進入 https://manager.line.biz
# 設置 Webhook: https://your-domain.com/webhook/line
```

---

## 📝 常用 Docker 命令

```bash
# ========== 啟動 / 停止 ==========
docker-compose up -d              # 後臺啟動
docker-compose up                 # 前臺啟動 (看日誌)
docker-compose stop               # 停止
docker-compose restart app        # 重啟應用
docker-compose down               # 完全移除

# ========== 查看狀態 ==========
docker-compose ps                 # 看運行狀態
docker ps                          # 所有容器
docker stats                       # 實時資源使用

# ========== 查看日誌 ==========
docker-compose logs app           # 查看全部日誌
docker-compose logs -f app        # 實時追蹤日誌
docker-compose logs -f --tail 50 app  # 最後 50 行
docker logs <container_id> -f     # Docker 原生命令

# ========== 進入容器 ==========
docker-compose exec app bash      # 進入 bash
docker-compose exec app sh        # 進入 sh
docker exec <container_id> bash   # 原生命令

# ========== 構建 / 推送 ==========
docker build -t us-stock:latest .    # 構建鏡像
docker tag us-stock:latest myrepo/us-stock
docker push myrepo/us-stock          # 推送到倉庫
```

---

## 🔧 常見問題速解

### ❌ "docker-compose: command not found"
```bash
# 解決: 使用完整命令
docker compose up -d        # 新版 Docker (v2+)
```

### ❌ "Unable to connect to Docker daemon"
```bash
# 解決: 啟動 Docker
# Windows: 打開 Docker Desktop
# Linux: sudo systemctl start docker
```

### ❌ "Port 8000 is already allocated"
```bash
# 選項 1: 改端口 (編輯 docker-compose.yml)
ports:
  - "9000:8000"   # 改為 9000
docker-compose up -d

# 選項 2: 殺死佔用端口的進程
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

### ❌ "LINE_CHANNEL_SECRET not set"
```bash
# 解決: 編輯 .env 並重啟
nano .env
LINE_CHANNEL_SECRET=your_secret_here
docker-compose up -d
```

### ❌ "Permission denied"
```bash
# Windows: 以管理員身份運行 PowerShell/CMD

# Linux: 
sudo usermod -aG docker $USER
newgrp docker
```

### ✅ 健康檢查
```bash
# 應用是否運行
curl http://localhost:8000/health
# 期望: {"status":"healthy",...}

# 查看詳細日誌
docker-compose logs app | grep -i "error\|warning"

# 檢查數據庫連接
docker-compose exec app python -c "from src.db.database import engine; print('OK')"
```

---

## 📊 配置速查

### .env 必填項
```env
# 從 LINE 管理控台獲取
LINE_CHANNEL_SECRET=xxxxxxxxxxxxxxxxxxxxxx
LINE_CHANNEL_ACCESS_TOKEN=xxxxxxxxxxxxxxxxxxxxxx
```

### .env 可選項
```env
# 數據庫
DATABASE_URL=sqlite:///./app.db
# 或使用 PostgreSQL:
# DATABASE_URL=postgresql://user:pass@host:5432/db

# 服務器
HOST=0.0.0.0
PORT=8000

# 日誌
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Alpha Vantage (可選)
ALPHA_VANTAGE_API_KEY=your_api_key
```

### docker-compose.yml 常用修改
```yaml
# 改端口
ports:
  - "9000:8000"    # 改為 9000

# 改數據庫
environment:
  DATABASE_URL: postgresql://user:pass@postgres:5432/db

# 啟用 PostgreSQL
docker-compose --profile postgres up -d

# 修改重載
command: uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
# 改為
command: uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 🚀 部署檢查清單

```bash
# □ 環境檢查
docker --version              # 確保有 Docker
docker-compose --version      # 確保有 docker-compose
git --version                 # 確保有 Git

# □ 項目檢查
ls .env.example               # 確保有 .env.example
ls docker-compose.yml         # 確保有 docker-compose.yml
ls Dockerfile                 # 確保有 Dockerfile

# □ 配置檢查
cat .env | grep LINE_CHANNEL_SECRET  # 確保已設置

# □ 啟動檢查
docker-compose up -d          # 啟動容器
sleep 10                      # 等待啟動
docker-compose ps             # 確保容器運行中

# □ 功能檢查
curl http://localhost:8000/health        # 健康檢查
curl http://localhost:8000/docs          # 看 API 文檔
docker-compose logs app | tail -20       # 檢查日誌

# □ Webhook 配置
# 進入 https://manager.line.biz
# 設置 Webhook URL: https://your-domain.com/webhook/line
# 點擊 Verify
# 啟用 Webhook
```

---

## 🌍 部署到雲服務器

### AWS EC2
```bash
# 連接到服務器
ssh -i your-key.pem ec2-user@your-instance-ip

# 安裝 Docker
curl https://get.docker.com | sh
sudo usermod -aG docker ec2-user

# 克隆項目
git clone https://github.com/your/repo.git
cd us-stock

# 編輯 .env (使用 nano/vim)
nano .env
# LINE_CHANNEL_SECRET=your_secret
# LINE_CHANNEL_ACCESS_TOKEN=your_token
# 保存: Ctrl+X, Y, Enter

# 啟動
docker-compose up -d

# 設置域名 + HTTPS
# 使用 Nginx + Let's Encrypt
```

### DigitalOcean App Platform
```bash
# 1. 創建 GitHub 倉庫
git remote add origin https://github.com/your/repo
git push -u origin main

# 2. 在 DigitalOcean 控制面板
# - 點擊 "Apps" → "Create App"
# - 連接 GitHub 倉庫
# - 添加環境變數 (LINE_CHANNEL_*)
# - 部署

# 3. 配置 Webhook
# Webhook URL: https://your-app.ondigitalocean.app/webhook/line
```

### Docker Hub (打包鏡像)
```bash
# 登錄
docker login

# 構建並標籤
docker build -t your-username/us-stock:1.0.0 .

# 推送
docker push your-username/us-stock:1.0.0

# 其他人可以直接使用
docker run -p 8000:8000 \
  -e LINE_CHANNEL_SECRET=xxx \
  your-username/us-stock:1.0.0
```

---

## 📚 文檔映射

```
想要...                          查看...
────────────────────────────────────────────────
5 分鐘快速開始                   QUICKSTART_DEPLOY.md
完整部署指南                     DEPLOYMENT.md
Docker 概念講解                  DOCKER_VISUAL_GUIDE.md (本文件)
系統架構設計                     ARCHITECTURE.md
API 文檔和示例                   API_REFERENCE.md
開發指南和貢獻                   CONTRIBUTING.md
性能優化檢查清單                 PERFORMANCE_DEPLOYMENT_CHECKLIST.md
```

---

## 🎯 一句話快速啟動

```bash
# 最短版本 (假設 .env 已配置)
docker-compose up -d && sleep 5 && curl http://localhost:8000/health
```

## 🆘 應急命令

```bash
# 容器崩潰時
docker-compose restart app

# 卡住時
docker-compose down -v && docker-compose up -d

# 查看所有錯誤
docker-compose logs app | grep -i error

# 進入容器調試
docker-compose exec app bash
# 在容器內
python -c "from src.main import app; print('Import OK')"
python -c "import src; print('Project OK')"
exit

# 查看資源使用 (超多日誌時)
docker stats --no-stream

# 清理 Docker 垃圾
docker system prune -a  # ⚠️ 會刪除未使用的鏡像!
```

---

**🎉 就這麼簡單！**

遇到問題？查看: `docker-compose logs -f app`

需要詳細說明？查看: [QUICKSTART_DEPLOY.md](./QUICKSTART_DEPLOY.md)
