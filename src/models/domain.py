"""
Domain models for LINE Bot US Stock application.
These are Pydantic models for type validation and serialization.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class QueryTypeEnum(str, Enum):
    """Types of user queries"""
    INDEX = "index"
    STOCK = "stock"
    NEWS = "news"
    TW_STOCK = "tw_stock"


class QueryStatusEnum(str, Enum):
    """Status of query processing"""
    PENDING = "pending"
    SUCCESS = "success"
    ERROR = "error"


class DataSourceEnum(str, Enum):
    """Data sources for financial information"""
    TWELVE_DATA = "twelve_data"
    FINNHUB = "finnhub"
    YAHOO_FINANCE = "yahoo_finance"
    ALPHA_VANTAGE = "alpha_vantage"
    GOOGLE_NEWS = "google_news"


# ============================================================================
# User Query Domain
# ============================================================================


class UserQueryRequest(BaseModel):
    """Request model for user queries"""
    query_type: QueryTypeEnum
    query_text: str = Field(..., min_length=1, max_length=100)
    stock_code: Optional[str] = Field(None, pattern=r"^[A-Z]{1,5}$")

    class Config:
        json_schema_extra = {
            "example": {
                "query_type": "stock",
                "query_text": "AAPL",
                "stock_code": "AAPL"
            }
        }


class UserQueryResponse(BaseModel):
    """Response model for queries"""
    id: str
    user_id: str
    query_type: QueryTypeEnum
    query_text: str
    stock_code: Optional[str]
    created_at: datetime
    status: QueryStatusEnum
    error_message: Optional[str] = None
    response_time_ms: Optional[int] = None


# ============================================================================
# Market Data Domain
# ============================================================================


class Index(BaseModel):
    """Stock index model"""
    id: str  # e.g., "^GSPC", "^IXIC", "^SOX"
    zh_name: str = Field(..., min_length=2, max_length=30)  # e.g., "S&P 500"
    current_price: Decimal = Field(..., ge=0)
    previous_close: Decimal = Field(..., ge=0)
    change_amount: Decimal = Field(...)
    change_percent: Decimal = Field(...)
    high_52w: Decimal = Field(..., ge=0)
    low_52w: Decimal = Field(..., ge=0)
    last_updated: datetime
    data_source: DataSourceEnum

    @property
    def direction(self) -> str:
        """Direction indicator for display"""
        if self.change_percent > 0:
            return "↑"
        elif self.change_percent < 0:
            return "↓"
        else:
            return "→"

    class Config:
        json_schema_extra = {
            "example": {
                "id": "^GSPC",
                "zh_name": "S&P 500",
                "current_price": "4500.25",
                "previous_close": "4480.00",
                "change_amount": "20.25",
                "change_percent": "0.45",
                "high_52w": "4800.00",
                "low_52w": "4000.00",
                "last_updated": "2026-05-17T16:00:00Z",
                "data_source": "yahoo_finance"
            }
        }


class Stock(BaseModel):
    """Individual stock model"""
    code: str = Field(..., pattern=r"^[A-Z]{1,5}$")
    company_name: str
    zh_name: Optional[str]
    current_price: Decimal = Field(..., ge=0)
    previous_close: Decimal = Field(..., ge=0)
    change_amount: Decimal = Field(...)
    change_percent: Decimal = Field(...)
    open_price: Optional[Decimal] = Field(None, ge=0)
    high_price: Optional[Decimal] = Field(None, ge=0)
    low_price: Optional[Decimal] = Field(None, ge=0)
    market_cap_billion: Optional[Decimal] = Field(None, ge=0)
    pe_ratio: Optional[Decimal] = Field(None, ge=0)
    dividend_yield: Optional[Decimal] = Field(None, ge=0)
    sector: Optional[str]
    industry: Optional[str]
    last_updated: datetime
    data_source: DataSourceEnum

    @property
    def direction(self) -> str:
        """Direction indicator"""
        if self.change_percent > 0:
            return "↑"
        elif self.change_percent < 0:
            return "↓"
        else:
            return "→"

    class Config:
        json_schema_extra = {
            "example": {
                "code": "AAPL",
                "company_name": "Apple Inc.",
                "zh_name": "蘋果公司",
                "current_price": "180.50",
                "previous_close": "179.25",
                "change_amount": "1.25",
                "change_percent": "0.70",
                "open_price": "179.00",
                "high_price": "181.50",
                "low_price": "178.75",
                "market_cap_billion": "2800.0",
                "pe_ratio": "28.5",
                "dividend_yield": "0.45",
                "sector": "Technology",
                "industry": "Consumer Electronics",
                "last_updated": "2026-05-17T16:00:00Z",
                "data_source": "yahoo_finance"
            }
        }


# ============================================================================
# News Domain
# ============================================================================


class NewsArticle(BaseModel):
    """News article model"""
    id: str
    title: str = Field(..., min_length=5, max_length=200)
    summary: str = Field(..., min_length=10, max_length=500)  # Allow shorter summaries from RSS feeds
    source: str = Field(..., max_length=50)
    url: Optional[str]
    published_at: datetime
    category: Optional[str]  # e.g., "economic", "earnings", "market"
    related_stocks: Optional[list[str]] = None  # Stock codes related to this news
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    fetched_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "news_001",
                "title": "Fed 宣佈升息決定",
                "summary": "美國聯邦準備委員會宣佈升息 0.5%，以控制通脹...",
                "source": "Reuters",
                "url": "https://example.com/news",
                "published_at": "2026-05-17T14:30:00Z",
                "category": "economic",
                "related_stocks": ["SPY", "QQQ"],
                "relevance_score": 0.95,
                "fetched_at": "2026-05-17T16:00:00Z"
            }
        }


# ============================================================================
# Taiwan Stock Domain
# ============================================================================


class TaiwanStock(BaseModel):
    """Taiwan stock correlation model"""
    us_code: str = Field(..., pattern=r"^[A-Z]{1,5}$")
    tw_code: str = Field(..., pattern=r"^[0-9]{4}$")
    tw_name: str
    relationship_type: str  # e.g., "supplier", "customer", "competitor", "industry_peer"
    relationship_detail: str = Field(..., max_length=200)  # Explanation of relationship
    strength: float = Field(..., ge=0.0, le=1.0)  # Strength of correlation (0-1)

    class Config:
        json_schema_extra = {
            "example": {
                "us_code": "TSLA",
                "tw_code": "2330",
                "tw_name": "台積電",
                "relationship_type": "supplier",
                "relationship_detail": "台積電是 TSLA 芯片製造商",
                "strength": 0.85
            }
        }


# ============================================================================
# Cache Domain
# ============================================================================


class CacheEntry(BaseModel):
    """Cache entry model"""
    cache_key: str
    cache_type: str  # "index", "stock", "news", "tw_stock"
    cached_data: dict
    expires_at: datetime
    created_at: datetime


# ============================================================================
# API Response Models
# ============================================================================


class IndexQueryResponse(BaseModel):
    """Response for index queries"""
    indices: list[Index] = Field(..., min_items=1, max_items=5)
    timestamp: datetime
    message: Optional[str] = None


class StockQueryResponse(BaseModel):
    """Response for stock queries"""
    stock: Stock
    news_articles: list[NewsArticle] = Field(..., min_items=0, max_items=5)
    timestamp: datetime


class NewsQueryResponse(BaseModel):
    """Response for news queries"""
    articles: list[NewsArticle] = Field(..., min_items=1, max_items=5)
    timestamp: datetime


class TaiwanStockQueryResponse(BaseModel):
    """Response for Taiwan stock queries"""
    us_code: str
    tw_stocks: list[TaiwanStock]
    timestamp: datetime


# ============================================================================
# Error Models
# ============================================================================


class ErrorResponse(BaseModel):
    """Standard error response"""
    error_code: str
    error_message: str  # Traditional Chinese
    timestamp: datetime
    request_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "E001_INVALID_CODE",
                "error_message": "無法找到該股票代碼，請確認代碼是否正確。",
                "timestamp": "2026-05-17T16:00:00Z",
                "request_id": "req_12345"
            }
        }
