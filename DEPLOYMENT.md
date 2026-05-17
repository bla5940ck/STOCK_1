# 部署指南

## 📋 目錄

1. [快速開始](#快速開始)
2. [系統需求](#系統需求)
3. [本地開發](#本地開發)
4. [Docker 部署](#docker-部署)
5. [生產部署](#生產部署)
6. [環境變數配置](#環境變數配置)
7. [監控和日誌](#監控和日誌)
8. [故障排除](#故障排除)

---

## 快速開始

### 5 分鐘快速啟動

```bash
# 1. 複製環境變數文件
cp .env.example .env

# 2. 編輯 .env 添加 LINE credentials
# LINE_CHANNEL_SECRET=your_secret_here
# LINE_CHANNEL_ACCESS_TOKEN=your_token_here

# 3. 使用 Docker Compose
docker-compose up -d

# 4. 驗證健康狀態
curl http://localhost:8000/health

# 5. 查看日誌
docker-compose logs -f app
```

### 訪問應用

- **Webhook URL**: `https://your-domain.com/webhook/line`
- **Health Check**: `GET http://localhost:8000/health`
- **API Docs**: `http://localhost:8000/docs` (Swagger UI)

---

## 系統需求

### 開發環境

- **Python**: 3.11+
- **pip**: 23.0+
- **Git**: 2.0+

### 生產環境

- **Docker**: 20.10+
- **Docker Compose**: 1.29+
- **PostgreSQL**: 13+
- **Memory**: 512MB 最小, 1GB 推薦
- **Disk**: 1GB 最小 (包括日誌)

### 外部服務

- **LINE Bot API**: 必需 (用於發送回覆)
- **Yahoo Finance API**: 必需 (股市數據)
- **Google News**: 必需 (新聞源)
- **Alpha Vantage**: 可選 (指數回退)

---

## 本地開發

### 1. 環境設置

```bash
# 複製項目
git clone <repo-url>
cd us-stock

# 創建虛擬環境
python -m venv venv

# 激活虛擬環境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安裝依賴
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 安裝預提交掛鉤 (可選)
pre-commit install
```

### 2. 配置環境變數

創建 `.env` 文件在項目根目錄:

```env
# LINE Bot Configuration
LINE_CHANNEL_SECRET=your_channel_secret
LINE_CHANNEL_ACCESS_TOKEN=your_channel_access_token

# Database
DATABASE_URL=sqlite:///./test.db
# 或 PostgreSQL:
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/us_stock

# API Keys
ALPHA_VANTAGE_API_KEY=your_api_key_here

# Server
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development

# Logging
LOG_LEVEL=DEBUG
LOG_FILE=logs/app.log
```

### 3. 初始化數據庫

```bash
# 創建數據庫表
python scripts/init_db.py

# 或使用 Alembic migrations (如果需要)
alembic upgrade head
```

### 4. 運行開發服務器

```bash
# 使用 Uvicorn
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 或使用 make (如果有 Makefile)
make dev
```

### 5. 運行測試

```bash
# 運行所有測試
pytest

# 運行帶覆蓋報告
pytest --cov=src --cov-report=html

# 運行特定測試文件
pytest tests/integration/test_stock_query_e2e.py -v

# 運行特定測試
pytest tests/unit/test_validators.py::test_validate_stock_code -v
```

### 6. 代碼質量檢查

```bash
# Type checking
mypy src --strict

# Code formatting
black src tests

# Linting
flake8 src tests --max-line-length=100

# All checks
make check
```

---

## Docker 部署

### Docker Compose 快速部署

#### 開發環境 (SQLite)

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/app.db
      - LINE_CHANNEL_SECRET=${LINE_CHANNEL_SECRET}
      - LINE_CHANNEL_ACCESS_TOKEN=${LINE_CHANNEL_ACCESS_TOKEN}
      - ENVIRONMENT=development
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    command: uvicorn src.main:app --host 0.0.0.0 --port 8000
```

#### 生產環境 (PostgreSQL)

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: us_stock
      POSTGRES_USER: appuser
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U appuser"]
      interval: 10s
      timeout: 5s
      retries: 5

  app:
    build:
      context: .
      dockerfile: Dockerfile.prod
    depends_on:
      db:
        condition: service_healthy
    environment:
      - DATABASE_URL=postgresql+asyncpg://appuser:${DB_PASSWORD}@db:5432/us_stock
      - LINE_CHANNEL_SECRET=${LINE_CHANNEL_SECRET}
      - LINE_CHANNEL_ACCESS_TOKEN=${LINE_CHANNEL_ACCESS_TOKEN}
      - ENVIRONMENT=production
      - WORKERS=4
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
    command: gunicorn src.main:app --workers ${WORKERS} --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

volumes:
  postgres_data:
```

### 構建和運行

```bash
# 構建鏡像
docker build -t us-stock:latest .

# 運行容器 (開發)
docker run -p 8000:8000 \
  -e LINE_CHANNEL_SECRET=your_secret \
  -e LINE_CHANNEL_ACCESS_TOKEN=your_token \
  us-stock:latest

# 使用 Compose (推薦)
docker-compose up -d

# 查看日誌
docker-compose logs -f app

# 停止應用
docker-compose down
```

---

## 生產部署

### 前置需求

1. **域名**: 配置 HTTPS 證書
2. **數據庫**: PostgreSQL 實例 (RDS/Cloud SQL/本機)
3. **負載均衡器**: Nginx/HAProxy/AWS ELB
4. **監控**: 日誌收集、度量指標、告警

### 部署架構 (推薦)

```
┌─────────────┐
│ LINE API    │
└──────┬──────┘
       │ HTTPS
┌──────▼──────────────┐
│   Reverse Proxy     │
│ (Nginx / HAProxy)   │
└──────┬──────────────┘
       │
   ┌───┴────────┐
   │            │
┌──▼─────┐  ┌──▼─────┐
│App Pod │  │App Pod │  (K8s or Docker Swarm)
│Instance│  │Instance│
└────┬───┘  └───┬────┘
     │          │
     └──────┬───┘
            │
      ┌─────▼──────┐
      │ PostgreSQL │
      │ (Primary)  │
      └────────────┘
```

### 環境變數配置 (生產)

```env
# Security
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false

# Database
DATABASE_URL=postgresql+asyncpg://user:password@db.example.com:5432/us_stock

# LINE Bot
LINE_CHANNEL_SECRET=${VAULT_LINE_CHANNEL_SECRET}
LINE_CHANNEL_ACCESS_TOKEN=${VAULT_LINE_CHANNEL_ACCESS_TOKEN}

# HTTPS
ALLOWED_HOSTS=api.example.com
CORS_ORIGINS=https://example.com

# Monitoring
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
DATADOG_API_KEY=${VAULT_DATADOG_API_KEY}

# Performance
WORKER_PROCESSES=4
DATABASE_POOL_SIZE=20
```

### 使用 Gunicorn + Uvicorn (生產級別)

```bash
# 安裝
pip install gunicorn uvicorn[standard]

# 運行 (4 workers)
gunicorn src.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
```

### Nginx 反向代理配置

```nginx
upstream app {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate /etc/ssl/certs/certificate.crt;
    ssl_certificate_key /etc/ssl/private/key.key;

    location / {
        proxy_pass http://app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 5s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://app;
        access_log off;
    }
}
```

### Kubernetes 部署 (可選)

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: us-stock-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: us-stock
  template:
    metadata:
      labels:
        app: us-stock
    spec:
      containers:
      - name: app
        image: us-stock:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        - name: LINE_CHANNEL_SECRET
          valueFrom:
            secretKeyRef:
              name: line-credentials
              key: secret
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

---

## 環境變數配置

### 必需變數

| 變數名 | 說明 | 範例 |
|--------|------|------|
| `LINE_CHANNEL_SECRET` | LINE Bot Channel Secret | `1234567890abcdef...` |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Bot Channel Access Token | `Bearer abcdef1234567890...` |
| `DATABASE_URL` | 數據庫連接字符串 | `sqlite:///./app.db` 或 `postgresql://...` |

### 可選變數

| 變數名 | 默認值 | 說明 |
|--------|--------|------|
| `ENVIRONMENT` | `development` | `development`, `staging`, `production` |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `HOST` | `0.0.0.0` | 服務器綁定地址 |
| `PORT` | `8000` | 服務器端口 |
| `ALPHA_VANTAGE_API_KEY` | `` | Alpha Vantage API Key (可選) |
| `DATABASE_POOL_SIZE` | `5` | 數據庫連接池大小 |

---

## 監控和日誌

### 日誌收集

#### 本地日誌文件

```bash
# 查看應用日誌
tail -f logs/app.log

# JSON 格式日誌便於解析
grep "ERROR" logs/app.log | jq .
```

#### ELK Stack (Elasticsearch, Logstash, Kibana)

```yaml
# logstash.conf
input {
  file {
    path => "/app/logs/app.log"
    codec => json
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "us-stock-%{+YYYY.MM.dd}"
  }
}
```

#### Datadog 集成

```python
# 在 main.py 中
from datadog import initialize, api
from ddtrace import patch_all

# 初始化 Datadog
initialize(app_key="your_app_key", api_key="your_api_key")
patch_all()
```

### 性能監控

#### Prometheus 度量指標

```python
# 在 handlers 中
from prometheus_client import Counter, Histogram

query_counter = Counter('stock_queries_total', 'Total stock queries')
query_duration = Histogram('stock_query_duration_seconds', 'Query duration in seconds')

@query_duration.time()
def handle_query():
    query_counter.inc()
    # ... 查詢邏輯
```

#### 關鍵指標

- **查詢響應時間** (目標: <2s)
- **API 錯誤率** (目標: <0.1%)
- **緩存命中率** (目標: >80%)
- **數據庫查詢時間** (目標: <100ms)
- **外部 API 調用次數** (監控速率限制)

### 告警規則 (Prometheus AlertManager)

```yaml
groups:
- name: us_stock_alerts
  rules:
  - alert: HighErrorRate
    expr: rate(requests_total{status=~"5.."}[5m]) > 0.001
    for: 5m
    annotations:
      summary: "High error rate detected"

  - alert: SlowQueryResponse
    expr: histogram_quantile(0.95, request_duration) > 2
    for: 5m
    annotations:
      summary: "Query response time is too slow"

  - alert: CacheHitRateLow
    expr: cache_hit_ratio < 0.7
    for: 10m
    annotations:
      summary: "Cache hit ratio below threshold"
```

---

## 故障排除

### 常見問題

#### 1. "Invalid signature" 錯誤

**原因**: LINE_CHANNEL_SECRET 不正確或請求體被篡改

**解決方案**:
```bash
# 檢查環境變數
echo $LINE_CHANNEL_SECRET

# 驗證是否與 LINE 控制台匹配
# https://manager.line.biz/

# 重新啟動應用
docker-compose restart app
```

#### 2. "Database connection refused"

**原因**: 數據庫未運行或連接字符串不正確

**解決方案**:
```bash
# 檢查 PostgreSQL 運行狀態
docker-compose ps

# 檢查數據庫連接
psql -U appuser -h localhost -d us_stock -c "SELECT 1"

# 查看應用日誌
docker-compose logs app
```

#### 3. "Timeout fetching data from Yahoo Finance"

**原因**: 網路問題或 API 超時

**解決方案**:
```python
# 檢查回退鏈是否工作
# 應該自動使用 Alpha Vantage

# 檢查防火牆規則
curl -I https://finance.yahoo.com/

# 增加超時時間 (src/config.py)
YAHOO_TIMEOUT = 10  # 從 5 改為 10
```

#### 4. "Out of memory"

**原因**: 連接池過大或記憶體洩漏

**解決方案**:
```bash
# 檢查記憶體使用
docker stats

# 減少連接池大小
# .env:
DATABASE_POOL_SIZE=10

# 啟用 Python 記憶體分析
pip install memory_profiler
python -m memory_profiler src/main.py
```

### 診斷命令

```bash
# 檢查服務健康狀態
curl http://localhost:8000/health

# 查看 API 文檔
curl http://localhost:8000/docs

# 檢查數據庫連接
docker-compose exec app python -c "
from src.db.database import get_db_async
import asyncio
async def test():
    async with get_db_async() as db:
        result = await db.execute('SELECT 1')
        print('DB OK')
asyncio.run(test())
"

# 查看最近的查詢日誌
sqlite3 ./data/app.db "SELECT * FROM query_logs ORDER BY created_at DESC LIMIT 10;"

# 查看應用日誌中的錯誤
grep "ERROR\|CRITICAL" logs/app.log | tail -20
```

---

## 更新和維護

### 數據庫遷移

```bash
# 生成新遷移 (使用 Alembic)
alembic revision --autogenerate -m "Add new column"

# 應用遷移
alembic upgrade head

# 回滾遷移
alembic downgrade -1
```

### 應用更新

```bash
# 構建新鏡像
docker build -t us-stock:v1.1.0 .

# 停止舊容器
docker-compose down

# 使用新鏡像啟動
docker-compose up -d
```

### 備份和恢復

```bash
# 備份 PostgreSQL
pg_dump us_stock > backup.sql

# 恢復
psql us_stock < backup.sql

# 備份 SQLite
cp data/app.db data/app.db.backup
```

---

## 安全檢查清單

- [ ] 所有密鑰存儲在 `.env` (未提交到 Git)
- [ ] HTTPS 證書已配置 (生產)
- [ ] 數據庫密碼已更改 (非默認值)
- [ ] 防火牆規則已配置
- [ ] 日誌不包含敏感信息
- [ ] 定期進行安全更新 (`pip list --outdated`)
- [ ] 已配置數據庫備份
- [ ] 已測試故障轉移程序

---

更多幫助:
- 查看 [ARCHITECTURE.md](./ARCHITECTURE.md) 瞭解系統設計
- 查看 [API_REFERENCE.md](./API_REFERENCE.md) 瞭解 API 細節
- 查看日誌文件: `logs/app.log`
