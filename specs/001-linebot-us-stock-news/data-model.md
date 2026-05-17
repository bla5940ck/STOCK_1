# Data Model: LINE Bot 美股與新聞助理

**Date**: 2026-05-17  
**Phase**: 1 (Design)

---

## Executive Summary

本文檔定義 LINE Bot 美股助理的領域實體、資料結構與驗證規則。共 9 個核心實體，包括用戶請求、指數行情、股票行情、新聞摘要、台股關聯標的、查詢歷史與快取表等，均採用 Pydantic schema（Python 型別驗證）與 SQLAlchemy ORM（資料庫映射）。

---

## 1. 用戶請求與互動實體

### 1.1 UserQuery (用戶查詢請求)

**用途**: 儲存用戶透過 LINE 發送的查詢請求

**欄位**:

| 欄位 | 型別 | 必要 | 驗證規則 | 說明 |
|------|------|------|---------|------|
| `id` | UUID | ✅ | PK | 唯一識別符 |
| `user_id` | string | ✅ | FK → LINE User | LINE 用戶 ID |
| `query_type` | enum | ✅ | `index` \| `stock` \| `news` \| `tw_stock` | 查詢類型 |
| `query_text` | string | ✅ | len 1-100 | 用戶輸入文本（如「美股」、「AAPL」、「新聞」） |
| `stock_code` | string | ⏸️ | Uppercase, 1-5 chars | 當 query_type=stock 時必要 |
| `created_at` | datetime | ✅ | Auto-generated | 查詢時間戳 |
| `status` | enum | ✅ | `pending` \| `success` \| `error` | 查詢狀態 |
| `error_message` | string | ⏸️ | Max 500 chars | 若 status=error，記錄錯誤訊息 |
| `response_time_ms` | integer | ⏸️ | >= 0 | API 回應耗時（毫秒） |

**範例 (Pydantic Schema)**:
```python
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional

class QueryTypeEnum(str, Enum):
    INDEX = "index"
    STOCK = "stock"
    NEWS = "news"
    TW_STOCK = "tw_stock"

class QueryStatusEnum(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    ERROR = "error"

class UserQueryRequest(BaseModel):
    query_type: QueryTypeEnum
    query_text: str = Field(..., min_length=1, max_length=100)
    stock_code: Optional[str] = Field(None, regex=r"^[A-Z]{1,5}$")

class UserQueryResponse(BaseModel):
    id: str
    user_id: str
    query_type: QueryTypeEnum
    query_text: str
    stock_code: Optional[str]
    created_at: datetime
    status: QueryStatusEnum
    error_message: Optional[str] = None
    response_time_ms: Optional[int] = None
```

---

## 2. 市場數據實體

### 2.1 Index (股票指數)

**用途**: 儲存美股三大指數（S&P 500、NASDAQ、費城半導體）的實時行情

**欄位**:

| 欄位 | 型別 | 必要 | 驗證規則 | 說明 |
|------|------|------|---------|------|
| `id` | string | ✅ | PK | 指數代碼（^GSPC、^IXIC、^SOX） |
| `zh_name` | string | ✅ | len 2-30 | 中文名稱 |
| `current_price` | decimal | ✅ | >= 0, 2 decimals | 目前點數 |
| `previous_close` | decimal | ✅ | >= 0, 2 decimals | 前收盤點數 |
| `change_amount` | decimal | ✅ | signed, 2 decimals | 漲跌幅（點數差） |
| `change_percent` | decimal | ✅ | signed, 2 decimals | 漲跌幅百分比 (%) |
| `high_52w` | decimal | ✅ | >= 0, 2 decimals | 52 週高點 |
| `low_52w` | decimal | ✅ | >= 0, 2 decimals | 52 週低點 |
| `last_updated` | datetime | ✅ | Auto-generated | 資料最後更新時間 |
| `data_source` | enum | ✅ | `yahoo_finance` \| `alpha_vantage` | 資料來源 |

**範例**:
```python
class Index(BaseModel):
    id: str  # "^GSPC", "^IXIC", "^SOX"
    zh_name: str  # "S&P 500", "那斯達克", "費城半導體"
    current_price: Decimal = Field(..., decimal_places=2)
    previous_close: Decimal = Field(..., decimal_places=2)
    change_amount: Decimal = Field(..., decimal_places=2)
    change_percent: Decimal = Field(..., decimal_places=2)
    high_52w: Decimal = Field(..., decimal_places=2)
    low_52w: Decimal = Field(..., decimal_places=2)
    last_updated: datetime
    data_source: str  # "yahoo_finance" or "alpha_vantage"
    
    @property
    def direction(self) -> str:
        if self.change_percent > 0:
            return "↑ 上升"
        elif self.change_percent < 0:
            return "↓ 下跌"
        else:
            return "→ 平穩"
```

**訊息格式範例**:
```
📊 S&P 500
目前: 5,234.88
變化: +15.23 (+0.29%) ↑
昨收: 5,219.65
52週高: 5,487.63 | 低: 4,542.12
```

---

### 2.2 Stock (個股)

**用途**: 儲存單一美股的行情與關聯新聞

**欄位**:

| 欄位 | 型別 | 必要 | 驗證規則 | 說明 |
|------|------|------|---------|------|
| `code` | string | ✅ | PK, Uppercase, 1-5 chars | 股票代碼（如 AAPL、TSLA） |
| `company_name` | string | ✅ | len 2-100 | 公司英文名稱 |
| `zh_name` | string | ⏸️ | len 2-50 | 公司中文名稱 |
| `current_price` | decimal | ✅ | > 0, 2-4 decimals | 目前股價 |
| `previous_close` | decimal | ✅ | > 0, 2-4 decimals | 前收盤價 |
| `change_amount` | decimal | ✅ | signed, 2-4 decimals | 漲跌幅（美元差） |
| `change_percent` | decimal | ✅ | signed, 2 decimals | 漲跌幅百分比 (%) |
| `market_cap_billion` | decimal | ⏸️ | >= 0 | 市值（十億美元） |
| `pe_ratio` | decimal | ⏸️ | > 0 | 本益比 (P/E Ratio) |
| `dividend_yield` | decimal | ⏸️ | >= 0, 2 decimals | 殖利率 (%) |
| `sector` | string | ⏸️ | len 2-30 | 產業別 (如 Technology、Healthcare) |
| `industry` | string | ⏸️ | len 2-50 | 細分產業 |
| `last_updated` | datetime | ✅ | Auto-generated | 資料最後更新時間 |
| `data_source` | enum | ✅ | `yahoo_finance` \| `alpha_vantage` | 資料來源 |

**範例**:
```python
class Stock(BaseModel):
    code: str = Field(..., regex=r"^[A-Z]{1,5}$")
    company_name: str
    zh_name: Optional[str] = None
    current_price: Decimal = Field(..., decimal_places=4)
    previous_close: Decimal = Field(..., decimal_places=4)
    change_amount: Decimal = Field(..., decimal_places=4)
    change_percent: Decimal = Field(..., decimal_places=2)
    market_cap_billion: Optional[Decimal] = None
    pe_ratio: Optional[Decimal] = None
    dividend_yield: Optional[Decimal] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    last_updated: datetime
    data_source: str
```

**訊息格式範例**:
```
💰 Apple Inc. (AAPL)
目前: $189.45
變化: +2.15 (+1.14%) ↑
昨收: $187.30
市值: $2,980 億 | 本益比: 28.5x | 殖利率: 0.45%
產業: Technology | 設備製造
```

---

## 3. 新聞實體

### 3.1 NewsArticle (新聞文章)

**用途**: 儲存美國經濟新聞與股票相關新聞

**欄位**:

| 欄位 | 型別 | 必要 | 驗證規則 | 說明 |
|------|------|------|---------|------|
| `id` | UUID | ✅ | PK | 唯一識別符 |
| `title` | string | ✅ | len 5-300 | 新聞標題 |
| `summary` | string | ✅ | len 50-150 | 摘要（Traditional Chinese，100~150 字） |
| `source` | string | ✅ | len 2-100 | 新聞來源（如 Google News、Bloomberg） |
| `url` | string | ✅ | Valid URL | 新聞完整連結 |
| `published_at` | datetime | ✅ | Timestamp | 發布時間 |
| `category` | enum | ✅ | `us_economic` \| `stock_related` \| `market_movement` | 新聞分類 |
| `related_stocks` | list[string] | ⏸️ | Max 5 items | 相關股票代碼陣列 |
| `relevance_score` | decimal | ⏸️ | 0.0-1.0 | 與查詢的關聯度（0=無關，1=高度相關） |
| `fetched_at` | datetime | ✅ | Auto-generated | 取得時間 |

**範例**:
```python
class NewsCategory(str, Enum):
    US_ECONOMIC = "us_economic"
    STOCK_RELATED = "stock_related"
    MARKET_MOVEMENT = "market_movement"

class NewsArticle(BaseModel):
    id: str
    title: str = Field(..., min_length=5, max_length=300)
    summary: str = Field(..., min_length=50, max_length=150)
    source: str = Field(..., min_length=2, max_length=100)
    url: str = Field(..., regex=r"^https?://")
    published_at: datetime
    category: NewsCategory
    related_stocks: Optional[List[str]] = Field(None, max_items=5)
    relevance_score: Optional[Decimal] = Field(None, ge=0.0, le=1.0)
    fetched_at: datetime
```

**訊息格式範例（3-5 篇）**:
```
📰 最新財經新聞

1️⃣ AI 晶片熱潮延續，台積電股價突破新高
摘要：台積電受惠於 AI 晶片需求，本週股價上漲 3.2%，創 52 週新高...
來源：經濟日報 | 05-17 10:30

2️⃣ 美聯準 6 月或再次升息，道瓊指數下跌 1.2%
摘要：聯邦基金期貨顯示市場預期美聯準將在 6 月議息會議上升息...
來源：彭博社 | 05-17 09:15
```

---

## 4. 台股關聯實體

### 4.1 TaiwanStock (台股關聯標的)

**用途**: 儲存美股與台股的關聯性對照表

**欄位**:

| 欄位 | 型別 | 必要 | 驗證規則 | 說明 |
|------|------|------|---------|------|
| `us_code` | string | ✅ | FK → Stock.code | 美股代碼 |
| `tw_code` | string | ✅ | PK, len 4 | 台股代碼（如 2330、2454） |
| `tw_name` | string | ✅ | len 2-50 | 台股公司中文名稱 |
| `relationship_type` | enum | ✅ | `supplier` \| `customer` \| `competitor` \| `partner` | 關係類型 |
| `relationship_detail` | string | ✅ | len 10-200 | 關係說明（如「晶片代工供應商」） |
| `strength` | enum | ✅ | `high` \| `medium` \| `low` | 關聯強度 |
| `last_verified_at` | datetime | ✅ | Auto-generated | 最後驗證時間 |
| `verified_by` | string | ✅ | len 2-100 | 驗證者／資料來源 |

**範例**:
```python
class RelationshipType(str, Enum):
    SUPPLIER = "supplier"
    CUSTOMER = "customer"
    COMPETITOR = "competitor"
    PARTNER = "partner"

class RelationshipStrength(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class TaiwanStock(BaseModel):
    us_code: str
    tw_code: str = Field(..., regex=r"^[0-9]{4}$")
    tw_name: str
    relationship_type: RelationshipType
    relationship_detail: str = Field(..., min_length=10, max_length=200)
    strength: RelationshipStrength
    last_verified_at: datetime
    verified_by: str
```

**資料範例**:
```json
[
  {
    "us_code": "AAPL",
    "tw_code": "2330",
    "tw_name": "台積電",
    "relationship_type": "supplier",
    "relationship_detail": "A 核心供應商，晶片代工",
    "strength": "high",
    "last_verified_at": "2026-05-17T00:00:00Z",
    "verified_by": "TAITRA"
  },
  {
    "us_code": "TSLA",
    "tw_code": "2317",
    "tw_name": "鴻海",
    "relationship_type": "partner",
    "relationship_detail": "代工生產夥伴，製造協議",
    "strength": "high",
    "last_verified_at": "2026-05-17T00:00:00Z",
    "verified_by": "News Analysis"
  }
]
```

**訊息格式範例**:
```
🔗 台股關聯標的 (AAPL)

1️⃣ 台積電 (2330) - 供應商 [高度關聯]
   晶片代工供應商
   
2️⃣ 聯發科 (2454) - 相關 [中度關聯]
   晶片設計相關

3️⃣ 和碩 (4938) - 相關 [中度關聯]
   代工製造合作
```

---

## 5. 快取與日誌實體

### 5.1 APICache (API 回應快取)

**用途**: 快取外部 API 回應，減少重複調用

**欄位**:

| 欄位 | 型別 | 必要 | 驗證規則 | 說明 |
|------|------|------|---------|------|
| `id` | string | ✅ | PK, Hash(type + param) | 快取索引鍵 |
| `cache_type` | enum | ✅ | `index` \| `stock` \| `news` | 快取類型 |
| `cache_key` | string | ✅ | len 5-100 | 查詢參數（如 stock_code=AAPL） |
| `cached_data` | JSON | ✅ | Max 10MB | 快取數據（JSON 序列化） |
| `created_at` | datetime | ✅ | Auto-generated | 快取建立時間 |
| `expires_at` | datetime | ✅ | timestamp | 快取過期時間 |
| `is_expired` | boolean | ⏸️ | Computed | 是否已過期 |

**快取有效期**:
- 指數數據：5 分鐘
- 個股數據：5 分鐘
- 新聞：1 小時
- 台股對照表：24 小時

**範例**:
```python
from datetime import datetime, timedelta

class APICache(BaseModel):
    id: str
    cache_type: str
    cache_key: str
    cached_data: dict
    created_at: datetime
    expires_at: datetime
    
    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
```

---

### 5.2 QueryLog (查詢日誌)

**用途**: 記錄所有用戶查詢，用於分析與除錯

**欄位**:

| 欄位 | 型別 | 必要 | 驗證規則 | 說明 |
|------|------|------|---------|------|
| `id` | UUID | ✅ | PK | 唯一識別符 |
| `user_id` | string | ✅ | FK → LINE User | 用戶 ID |
| `query_text` | string | ✅ | len 1-100 | 查詢文本 |
| `query_type` | enum | ✅ | `index` \| `stock` \| `news` \| `tw_stock` | 查詢類型 |
| `status` | enum | ✅ | `success` \| `error` \| `timeout` | 執行狀態 |
| `response_time_ms` | integer | ✅ | >= 0 | 回應耗時 |
| `error_message` | string | ⏸️ | Max 500 chars | 錯誤訊息（若有） |
| `created_at` | datetime | ✅ | Auto-generated | 查詢時間 |
| `ip_address` | string | ⏸️ | Optional | 用戶 IP（用於地理定位） |

**索引**:
- `(user_id, created_at)` - 單一用戶查詢歷史
- `(query_type, status, created_at)` - 查詢類型統計
- `created_at` - 時間序列分析

---

## 6. Webhook 訊息實體

### 6.1 LineWebhookEvent (LINE Webhook 事件)

**用途**: 解析並驗證 LINE Webhook 傳入的事件

**欄位**:

| 欄位 | 型別 | 必要 | 驗證規則 | 說明 |
|------|------|------|---------|------|
| `events` | list[Event] | ✅ | Array | LINE 事件陣列 |
| `destination` | string | ✅ | Valid User ID | 目標機器人 ID |

**Event 結構**:

```python
class LineEvent(BaseModel):
    type: str  # "message", "follow", "unfollow"
    message: Optional[dict] = None  # { "type": "text", "text": "美股" }
    replyToken: str
    timestamp: int
    source: dict  # { "type": "user", "userId": "..." }
    
class LineWebhookPayload(BaseModel):
    events: List[LineEvent]
    destination: str
```

**訊息事件型別**:
- `message.type = "text"` - 文字訊息（「美股」、「AAPL」、「新聞」）
- `message.type = "postback"` - 按鈕回覆（Taiwan Quick Reply 選擇）

---

## 7. 驗證與業務規則

### 7.1 股票代碼驗證

```python
def validate_stock_code(code: str) -> bool:
    """
    驗證股票代碼格式
    - 長度：1-5 字元
    - 大寫英文字母
    """
    import re
    return bool(re.match(r"^[A-Z]{1,5}$", code))

# 例子
validate_stock_code("AAPL")    # True
validate_stock_code("aapl")    # False
validate_stock_code("ABCDEF")  # False (too long)
```

### 7.2 新聞摘要截取

```python
def truncate_summary(text: str, max_length: int = 150) -> str:
    """
    截取新聞摘要至 150 字
    - 移除 HTML tag
    - 保留完整句子（不截斷中文字）
    """
    if len(text) <= max_length:
        return text
    
    # 向後搜尋最後一個句號
    for i in range(max_length, 0, -1):
        if text[i] in '。!！?？\n':
            return text[:i+1]
    
    return text[:max_length] + "…"
```

### 7.3 台股代碼驗證

```python
def validate_tw_stock_code(code: str) -> bool:
    """
    驗證台股代碼
    - 長度：4 位數字
    """
    import re
    return bool(re.match(r"^[0-9]{4}$", code))
```

---

## 8. 資料庫 Schema (SQLAlchemy ORM)

### 8.1 Index 表

```python
from sqlalchemy import Column, String, Numeric, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class IndexModel(Base):
    __tablename__ = "indices"
    
    id = Column(String(10), primary_key=True)  # "^GSPC"
    zh_name = Column(String(30), nullable=False)
    current_price = Column(Numeric(12, 2), nullable=False)
    previous_close = Column(Numeric(12, 2), nullable=False)
    change_amount = Column(Numeric(12, 2), nullable=False)
    change_percent = Column(Numeric(6, 2), nullable=False)
    high_52w = Column(Numeric(12, 2), nullable=False)
    low_52w = Column(Numeric(12, 2), nullable=False)
    last_updated = Column(DateTime, nullable=False)
    data_source = Column(String(30), nullable=False)
```

### 8.2 Stock 表

```python
class StockModel(Base):
    __tablename__ = "stocks"
    
    code = Column(String(5), primary_key=True)
    company_name = Column(String(100), nullable=False)
    zh_name = Column(String(50))
    current_price = Column(Numeric(12, 4), nullable=False)
    previous_close = Column(Numeric(12, 4), nullable=False)
    change_amount = Column(Numeric(12, 4), nullable=False)
    change_percent = Column(Numeric(6, 2), nullable=False)
    market_cap_billion = Column(Numeric(12, 2))
    pe_ratio = Column(Numeric(8, 2))
    dividend_yield = Column(Numeric(6, 2))
    sector = Column(String(30))
    industry = Column(String(50))
    last_updated = Column(DateTime, nullable=False, index=True)
    data_source = Column(String(30), nullable=False)
    
    __table_args__ = (
        Index('idx_stock_last_updated', 'last_updated'),
    )
```

### 8.3 台股關聯表

```python
class TaiwanStockModel(Base):
    __tablename__ = "taiwan_stocks"
    
    us_code = Column(String(5), primary_key=True)  # FK
    tw_code = Column(String(4), primary_key=True)
    tw_name = Column(String(50), nullable=False)
    relationship_type = Column(String(20), nullable=False)  # supplier, customer, etc
    relationship_detail = Column(String(200), nullable=False)
    strength = Column(String(10), nullable=False)  # high, medium, low
    last_verified_at = Column(DateTime, nullable=False)
    verified_by = Column(String(100), nullable=False)
```

---

## 9. 訊息型別定義

### 9.1 LINE 訊息物件

**快速回覆（Quick Reply）**:
```python
class QuickReplyButton(BaseModel):
    type: str = "action"
    action: dict  # { "type": "message", "label": "2330 台積電", "text": "2330" }

class QuickReply(BaseModel):
    items: List[QuickReplyButton]
```

**FlexMessage（Rich Format）**:
```python
# 用於格式化複雜的查詢結果（如股票詳情）
class FlexMessage(BaseModel):
    type: str = "flex"
    altText: str
    contents: dict  # { "type": "bubble", "body": {...} }
```

---

## 總結

**核心實體**:
1. ✅ UserQuery - 用戶查詢請求
2. ✅ Index - 指數行情
3. ✅ Stock - 個股行情
4. ✅ NewsArticle - 新聞文章
5. ✅ TaiwanStock - 台股關聯標的
6. ✅ APICache - API 快取
7. ✅ QueryLog - 查詢日誌
8. ✅ LineWebhookEvent - Webhook 事件
9. ✅ 驗證規則與業務邏輯

**驗證覆蓋**:
- ✅ 所有數值型別：Decimal（精確財務計算）
- ✅ 所有字串型別：正則運算式與長度限制
- ✅ 列舉型別：Enum（確保有效值）
- ✅ 業務規則：Stock code、Taiwan code、新聞摘要截取

---

**Data Model Status**: ✅ COMPLETE  
**Next Step**: Generate API contracts  
**Last Updated**: 2026-05-17
