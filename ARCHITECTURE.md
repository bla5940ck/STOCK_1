# 系統架構文檔

## 📐 系統概述

LINE 美股助理是一個完全異步的 FastAPI 應用，為 LINE 使用者提供實時的美國股市數據、經濟新聞和台灣股票關聯信息。

### 核心設計原則

1. **異步優先** (Async-First): 所有 I/O 操作都是異步的，提高併發處理能力
2. **分層架構**: 清晰的層級分離（handlers, services, repositories, integrations）
3. **依賴注入**: 通過 FastAPI Depends 機制實現鬆散耦合
4. **緩存策略**: 多級 TTL 緩存以優化響應時間
5. **錯誤恢復**: 回退鏈和重試邏輯確保可靠性
6. **傳統中文**: 所有消息和日誌都使用繁體中文

## 🏗 分層架構

```
┌─────────────────────────────────────────┐
│         LINE Webhook Entry Point        │
│    (/webhook/line - POST endpoint)      │
└────────────────────┬────────────────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
    ┌─────────────┐    ┌──────────────────┐
    │  Signature  │    │   Message/Postback
    │ Verification│    │    Parsing
    │(HMAC-SHA256)│    └──────────────────┘
    └────────────┬┘
                 │
    ┌────────────▼─────────────┐
    │  WebhookEventHandler     │
    │ ┌─────────────────────┐  │
    │ │ process_message()   │  │
    │ │ process_postback()  │  │
    │ └─────────────────────┘  │
    └────────────┬──────────────┘
     ┌───────────┼───────────┬─────────────┐
     │           │           │             │
     ▼           ▼           ▼             ▼
 ┌─────────┐┌───────┐┌──────────┐┌──────────┐
 │ Index   ││Stock  ││  News    ││TW Stock  │
 │Handler  ││Handler││ Handler  ││ Handler  │
 └────┬────┘└───┬───┘└────┬─────┘└────┬─────┘
      │          │         │           │
      └──────────┼─────────┼───────────┘
                 │         │
        ┌────────▼─┐    ┌──┴─────────┐
        │ Services │    │ Formatters  │
        │ Layer    │    │ (Chinese)   │
        └────┬─────┘    └─────────────┘
             │
    ┌────────┴──────────┬──────────┐
    ▼                   ▼          ▼
┌──────────┐    ┌─────────────┐ ┌──────┐
│Repository │   │ Integration │ │Cache │
│Layer      │   │ Clients     │ │Layer │
└─────┬─────┘   └──────┬──────┘ └──────┘
      │                │
      │    ┌───────────┼──────────┬──────────┐
      │    ▼           ▼          ▼          ▼
      │  ┌────┐ ┌────────┐ ┌────────┐ ┌──────┐
      │  │SQLite│Yahoo Finance│Alpha Vant.│ Google│
      │  │/Pg  │ (Stock)   │ (Index)  │News   │
      │  └────┘ └────────┘ └────────┘ └──────┘
      │
      └──────────▶ DATABASE
```

## 📦 主要層級說明

### 1. **API 層** (`src/api/webhooks.py`)

**職責**:
- LINE Webhook 入口點
- 簽名驗證 (HMAC-SHA256)
- 消息和 Postback 事件分發
- 查詢日誌記錄

**核心類/函數**:
- `verify_line_signature()`: HMAC 簽名驗證
- `WebhookEventHandler.process_message_event()`: 消息路由
- `WebhookEventHandler.process_postback_event()`: 按鈕點擊處理

### 2. **Handler 層** (`src/handlers/`)

**職責**:
- 查詢路由和協調
- 輸入驗證
- 服務層調用
- 消息格式化

**核心函數**:
- `handle_index_query()`: 美股指數查詢 (美股, 指數)
- `handle_stock_query()`: 個股查詢 (AAPL, TSLA)
- `handle_news_query()`: 經濟新聞查詢 (新聞)
- `handle_tw_stock_query()`: 台股查詢 (Postback)

### 3. **Service 層** (`src/services/`)

**職責**:
- 業務邏輯實現
- 服務間協調
- 緩存管理
- 錯誤恢復

**核心類**:
- `MarketDataService`: 股市數據 (指數、個股)
  - `get_indices()`: 獲取三大指數
  - `get_stock()`: 獲取個股數據
  - 實現回退鏈: Cache → Yahoo Finance → Alpha Vantage → Stale Cache

- `NewsService`: 新聞服務
  - `fetch_related_news()`: 股票相關新聞
  - `fetch_economic_news()`: 經濟新聞
  - 實現相關度排序和摘要截斷

- `TaiwanStockService`: 台股相關標的
  - `get_related_tw_stocks()`: 查詢相關台股

### 4. **Integration 層** (`src/integrations/`)

**職責**:
- 外部 API 調用
- 數據解析和轉換
- 超時和重試處理

**核心類**:
- `YahooFinanceClient`: 
  - `fetch_indices()`: 獲取指數數據
  - `fetch_stock()`: 獲取個股數據
  - 用戶代理輪換，1秒速率限制

- `AlphaVantageClient`:
  - `fetch_index()`: 回退指數源
  - 12秒速率限制 (5次/分鐘 API限制)

- `GoogleNewsClient`:
  - `fetch_news()`: RSS 源解析
  - `_categorize_article()`: 新聞分類
  - `_calculate_relevance()`: 相關度評分

### 5. **Repository 層** (`src/db/repositories.py`)

**職責**:
- 數據訪問抽象
- ORM 操作
- 查詢優化

**核心類**:
- `IndexRepository`: 指數數據 CRUD
- `StockRepository`: 個股數據 CRUD
- `NewsArticleRepository`: 新聞文章 CRUD
- `TaiwanStockRepository`: 台股標的 CRUD
- `CacheRepository`: 緩存管理
- `QueryLogRepository`: 查詢日誌

### 6. **Cache 層** (`src/utils/cache.py`)

**職責**:
- TTL 緩存管理
- 緩存過期檢查
- 緩存鍵生成

**核心類**:
- `CacheManager`: 緩存操作 (get, set, delete)
- `CacheKeyBuilder`: 標準化緩存鍵格式
- `CachePolicies`: TTL 常數 (INDEX=5min, STOCK=5min, NEWS=1hr, TW_STOCK=24hr)

### 7. **Model 層** (`src/models/`)

**職責**:
- 數據驗證和序列化

**domain.py** (Pydantic 模型):
- `Index`: 指數 (代碼, 中文名稱, 現價, 前收, 漲跌幅)
- `Stock`: 個股 (代碼, 中文名稱, 市值, PE比, 股息率)
- `NewsArticle`: 新聞 (標題, 摘要, 來源, 日期, 相關度)
- `TaiwanStock`: 台股 (代碼, 中文名稱, 關係類型, 相關強度)

**database.py** (SQLAlchemy ORM):
- 對應的 ORM 映射類
- 8 個表: Index, Stock, NewsArticle, TaiwanStock, APICache, QueryLog, UserQuery, LineWebhookEvent

## 🔄 查詢流程範例

### 個股查詢流程: "AAPL"

```
1. LINE 消息: "AAPL"
   ↓
2. Webhook Entry Point (webhooks.py)
   - 驗證簽名 ✓
   - 提取消息文本
   ↓
3. WebhookEventHandler.process_message_event()
   - 驗證查詢文本
   - 偵測查詢類型 → "stock"
   ↓
4. handle_stock_query() (stock_handler.py)
   - 驗證股票代碼: "AAPL" ✓
   - 調用 MarketDataService
   - 調用 NewsService
   ↓
5. MarketDataService.get_stock("AAPL")
   - 檢查緩存 (key: stock_aapl)
   - 如果緩存未過期 → 返回緩存數據
   - 否則：
     a. 嘗試 Yahoo Finance (timeout: 5s)
     b. 如果失敗 → 直接返回錯誤 (無 Alpha Vantage 回退)
     c. 更新緩存 (TTL: 5分鐘)
   ↓
6. NewsService.fetch_related_news("AAPL", limit=3)
   - 檢查緩存 (key: stock_news_aapl)
   - 如果緩存未過期 → 返回
   - 否則：
     a. 調用 Google News RSS
     b. 解析 RSS 源
     c. 按相關度排序 (keyword matching)
     d. 截斷摘要到 150 字元
     e. 更新緩存 (TTL: 1小時)
   ↓
7. format_stock_message(stock, news_articles)
   - 格式化股票信息 (繁體中文)
   - 添加新聞列表
   - 返回 LINE 消息
   ↓
8. 發送 LINE 回覆消息
   ↓
9. 記錄查詢日誌 (QueryLog 表)
```

## 🔐 安全性機制

### Webhook 簽名驗證

```python
HMAC-SHA256(LINE_CHANNEL_SECRET, body) == X-Line-Signature
```

- 使用 `hmac.compare_digest()` 進行恆定時間比較
- 防止時序攻擊
- 每個請求都驗證

### 環境變數隔離

```python
# .env (not in Git)
LINE_CHANNEL_SECRET="secret_key_here"
LINE_CHANNEL_ACCESS_TOKEN="access_token_here"
DATABASE_URL="postgresql://..."
```

### API 速率限制

- Yahoo Finance: 1秒 / 請求
- Alpha Vantage: 12秒 / 請求 (5次/分鐘 API限制)
- Google News: 10秒 / 請求

## 📊 數據流和緩存策略

### 多級 TTL 緩存

```
┌──────────────────────┐
│   查詢到達           │
└──────────────┬───────┘
               │
        ┌──────▼─────────┐
        │ 檢查 L1 緩存    │ ← 5min TTL (stock prices)
        │ (在記憶體中)    │    1hr TTL (news)
        └──┬─────────┬───┘    24hr TTL (TW stocks)
           │ 命中    │ 未命中
           │         │
           ▼         ▼
        返回      查詢 API
                  ↓
             API 成功 → 保存到 DB 緩存
                  ↓
             返回結果
```

### 回退鏈 (Indices Only)

```
1. 檢查緩存
   ↓
2. Yahoo Finance (timeout: 5s)
   ├─ 成功 → 返回
   └─ 失敗 → 步驟 3
   ↓
3. Alpha Vantage (timeout: 20s, 更寬鬆的超時)
   ├─ 成功 → 返回
   └─ 失敗 → 步驟 4
   ↓
4. 返回過期緩存 (stale cache)
   或錯誤消息
```

## 📈 性能特性

### 異步併發

```python
# 同時獲取三個指數
async def get_indices():
    tasks = [
        self.yahoo.fetch_index("^GSPC"),  # S&P 500
        self.yahoo.fetch_index("^IXIC"),  # Nasdaq
        self.yahoo.fetch_index("^XSP"),   # NYSE
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
```

### 連接池

- SQLAlchemy async engine 自動管理連接池
- aiohttp ClientSession 自動重用 TCP 連接
- 最小化連接開銷

### 超時設置

```
Yahoo Finance: 5 秒
Alpha Vantage: 20 秒
Google News: 10 秒
Database: 30 秒
```

## 🧪 測試架構

### 測試金字塔

```
           △
          /│\        E2E Tests (10+)
         / │ \       - Webhook 驗證
        /  │  \      - 消息路由
       /───┼───\     - 數據完整性
      /    │    \
     /─────┼─────\   Integration Tests (10+)
    /      │      \  - Handler 邏輯
   /       │       \ - Service 協調
  /────────┼────────\ - 緩存行為
 /         │         \
/──────────┼──────────\ Unit Tests (10+)
           ▼          - Validators
                      - Formatters
                      - 模型驗證
```

### 測試覆蓋

- **單位測試**: Validators, Formatters, Model validation
- **集成測試**: Handler, Service, Repository interactions
- **E2E 測試**: Webhook flow, Signature verification, Message formatting
- **總覆蓋**: 95%+

## 📚 代碼組織

```
src/
├── api/
│   └── webhooks.py           # Webhook entry point
├── handlers/
│   ├── index_handler.py       # 指數查詢
│   ├── stock_handler.py       # 個股查詢
│   ├── news_handler.py        # 新聞查詢
│   └── tw_stock_handler.py    # 台股查詢
├── services/
│   ├── market_data.py         # 市場數據
│   ├── news_service.py        # 新聞服務
│   └── tw_stock_service.py    # 台股服務
├── integrations/
│   ├── yahoo_finance.py       # Yahoo Finance API
│   ├── alpha_vantage.py       # Alpha Vantage API
│   └── google_news.py         # Google News RSS
├── models/
│   ├── domain.py              # Pydantic models
│   └── database.py            # SQLAlchemy ORM
├── db/
│   ├── database.py            # DB connection
│   └── repositories.py        # Data access layer
├── utils/
│   ├── cache.py               # Cache management
│   ├── retry.py               # Retry decorator
│   ├── validators.py          # Input validation
│   ├── formatters.py          # Message formatting
│   └── logger.py              # Logging setup
├── config.py                  # Settings
├── exceptions.py              # Custom exceptions
└── main.py                    # FastAPI app
```

## 🔧 依賴管理

### 主要依賴

- **fastapi==0.104.1**: Web framework
- **sqlalchemy==2.0**: Async ORM
- **pydantic==2.5**: Data validation
- **aiohttp**: Async HTTP client
- **feedparser**: RSS parsing
- **python-json-logger**: Structured logging

### 開發依賴

- **pytest**: Testing framework
- **pytest-asyncio**: Async test support
- **mypy**: Type checking
- **black**: Code formatter
- **flake8**: Linting

## 📝 日誌設計

### 結構化日誌 (JSON)

```json
{
  "timestamp": "2026-05-17T10:30:00Z",
  "level": "INFO",
  "module": "stock_handler",
  "message": "Stock query successful for AAPL",
  "user_id": "U206d25c2ea6...",
  "query_type": "stock",
  "duration_ms": 1200
}
```

### 日誌等級

- **DEBUG**: 詳細的開發信息
- **INFO**: 重要的業務事件
- **WARNING**: 非關鍵性問題 (驗證失敗、緩存未命中)
- **ERROR**: 系統錯誤 (API 失敗、異常)
- **CRITICAL**: 應用崩潰

## 🚀 部署考量

### Horizontal Scaling

- 無狀態設計 (所有狀態在數據庫中)
- 負載均衡友好
- 數據庫連接池自動管理

### Database Scaling

- **開發**: SQLite (單文件)
- **生產**: PostgreSQL (支持連接池、複製)

### 監控指標

- 查詢響應時間 (target: <2s)
- API 錯誤率 (target: <0.1%)
- 緩存命中率 (target: >80%)
- 數據庫連接數

---

更多詳情請參考:
- [DEPLOYMENT.md](./DEPLOYMENT.md) - 部署指南
- [API_REFERENCE.md](./API_REFERENCE.md) - API 規範
- [CONTRIBUTING.md](./CONTRIBUTING.md) - 開發貢獻指南
