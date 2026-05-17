# LINE Bot 美股與新聞助理

一個即時的財務查詢 LINE Bot，提供美股三大指數、個股行情、經濟新聞以及台股相關標的查詢。

## 功能

### User Story 1: 取得三大指數摘要 (P1)
輸入「美股」，獲得 S&P 500、那斯達克、費城半導體的昨晚漲跌幅

### User Story 2: 以代碼查詢個股與相關新聞 (P1)
輸入股票代碼（如 AAPL、TSLA），獲得該股前晚漲跌幅與最新相關新聞

### User Story 3: 取得美國重要經濟新聞 (P2)
輸入「新聞」，獲得最新美國經濟新聞摘要

### User Story 4: 延伸查詢台股關聯標的 (P2)
在查詢美股代碼後，可選擇查詢相關台股個股

## 快速開始

### 系統需求

- Python 3.11+
- Git
- Docker (optional)

### 本地開發設置

1. **Clone 倉庫**
   ```bash
   git clone <repository-url>
   cd linebot-us-stock
   ```

2. **建立虛擬環境**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **安裝依賴**
   ```bash
   pip install -r requirements.txt
   ```

4. **設置環境變量**
   ```bash
   cp .env.example .env
   # 編輯 .env，填入您的 LINE Channel Access Token 和 Secret
   ```

5. **初始化數據庫**
   ```bash
   python -m src.db.init
   ```

6. **啟動應用**
   ```bash
   uvicorn src.main:app --reload
   ```

應用將在 `http://localhost:8000` 啟動。訪問 `http://localhost:8000/docs` 查看 Swagger API 文檔。

### Docker 運行

```bash
# 使用 docker-compose
docker-compose up -d

# 應用運行在 http://localhost:8000
```

## LINE Bot 設置

1. 前往 [LINE Developers Console](https://developers.line.biz/)
2. 創建新的 Messaging API Channel
3. 獲取 Channel Access Token 和 Channel Secret
4. 設置 Webhook URL 為 `https://your-domain.com/webhook/line`
5. 將 Token 和 Secret 填入 `.env` 文件

## 開發

### 運行測試

```bash
# 所有測試
pytest

# 帶覆蓋率
pytest --cov=src

# 特定測試套件
pytest tests/unit
pytest tests/integration
```

### 代碼格式化

```bash
black src tests
ruff check src tests
mypy src
```

### 項目結構

```
linebot-us-stock/
├── src/
│   ├── api/              # API 路由和 Webhook 處理
│   ├── handlers/         # 業務邏輯分流器
│   ├── services/         # 業務服務層
│   ├── models/           # 資料模型 (Pydantic + SQLAlchemy)
│   ├── integrations/     # 外部 API 客戶端
│   ├── utils/            # 工具函數 (驗證、格式化、日誌)
│   ├── db/               # 資料庫訪問層
│   └── main.py           # FastAPI 應用入口
├── tests/                # 測試套件
├── docs/                 # 文檔
├── requirements.txt      # Python 依賴
├── pyproject.toml        # 項目配置
└── README.md            # 本文件
```

## API 端點

### Webhook
- **POST** `/webhook/line` - LINE Messaging API Webhook

### 健康檢查
- **GET** `/health` - 應用健康狀態

## 配置

所有配置通過環境變量管理，見 `.env.example`

### 重要配置項

- `LINE_CHANNEL_ACCESS_TOKEN`: LINE Channel Access Token
- `LINE_CHANNEL_SECRET`: LINE Channel Secret
- `DATABASE_URL`: 資料庫連接字符串
- `API_TIMEOUT`: 外部 API 超時時間（秒）
- `LOG_LEVEL`: 日誌級別 (INFO, DEBUG, etc.)

## 技術棧

- **Framework**: FastAPI + Uvicorn
- **Database**: SQLAlchemy + PostgreSQL/SQLite
- **Testing**: pytest + pytest-asyncio
- **Code Quality**: Black, Ruff, MyPy
- **External APIs**: 
  - Yahoo Finance (股票數據)
  - Alpha Vantage (備選股票數據)
  - Google News RSS (新聞數據)

## 錯誤處理

所有錯誤情境（API 超時、無效代碼、數據缺失）都提供清晰的繁體中文錯誤訊息，建議用戶稍後重試。

## 性能目標

- 指數查詢: <300ms (90th percentile)
- 個股+新聞查詢: <2 秒
- LINE Webhook ACK: <500ms
- 並發處理: ≥100 req/s

## 貢獻

1. Fork 倉庫
2. 建立特性分支 (`git checkout -b feature/amazing-feature`)
3. Commit 更改 (`git commit -m 'Add amazing feature'`)
4. Push 到分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

## 許可證

MIT License - 詳見 LICENSE 文件

## 聯絡方式

問題或建議，請提交 Issue 或聯絡開發團隊。

---

**技術文檔**: 見 [ARCHITECTURE.md](docs/ARCHITECTURE.md) 和 [DEPLOYMENT.md](docs/DEPLOYMENT.md)
