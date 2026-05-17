"""
SQLAlchemy ORM models for database persistence.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import Column, String, Numeric, DateTime, Enum as SQLEnum, ForeignKey, Integer, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


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
    YAHOO_FINANCE = "yahoo_finance"
    ALPHA_VANTAGE = "alpha_vantage"
    GOOGLE_NEWS = "google_news"


# ============================================================================
# User Query Table
# ============================================================================


class UserQuery(Base):
    """User query request history"""
    __tablename__ = "user_queries"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(255), index=True)
    query_type = Column(SQLEnum(QueryTypeEnum), index=True)
    query_text = Column(String(100))
    stock_code = Column(String(5), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(SQLEnum(QueryStatusEnum), default=QueryStatusEnum.PENDING)
    error_message = Column(String(500), nullable=True)
    response_time_ms = Column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<UserQuery(id={self.id}, user_id={self.user_id}, query_type={self.query_type})>"


# ============================================================================
# Market Data Tables
# ============================================================================


class Index(Base):
    """Stock index data"""
    __tablename__ = "indices"

    id = Column(String(10), primary_key=True)  # ^GSPC, ^IXIC, ^SOX
    zh_name = Column(String(30))
    current_price = Column(Numeric(10, 2))
    previous_close = Column(Numeric(10, 2))
    change_amount = Column(Numeric(10, 2))
    change_percent = Column(Numeric(8, 2))
    high_52w = Column(Numeric(10, 2), nullable=True)
    low_52w = Column(Numeric(10, 2), nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, index=True)
    data_source = Column(SQLEnum(DataSourceEnum))

    def __repr__(self) -> str:
        return f"<Index(id={self.id}, zh_name={self.zh_name}, price={self.current_price})>"


class Stock(Base):
    """Individual stock data"""
    __tablename__ = "stocks"

    code = Column(String(5), primary_key=True)
    company_name = Column(String(200))
    zh_name = Column(String(100), nullable=True)
    current_price = Column(Numeric(10, 2))
    previous_close = Column(Numeric(10, 2))
    change_amount = Column(Numeric(10, 2))
    change_percent = Column(Numeric(8, 2))
    market_cap_billion = Column(Numeric(10, 1), nullable=True)
    pe_ratio = Column(Numeric(10, 2), nullable=True)
    dividend_yield = Column(Numeric(8, 2), nullable=True)
    sector = Column(String(50), nullable=True)
    industry = Column(String(100), nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, index=True)
    data_source = Column(SQLEnum(DataSourceEnum))

    def __repr__(self) -> str:
        return f"<Stock(code={self.code}, price={self.current_price})>"


# ============================================================================
# News Table
# ============================================================================


class NewsArticle(Base):
    """News article data"""
    __tablename__ = "news_articles"

    id = Column(String(100), primary_key=True)
    title = Column(String(200))
    summary = Column(String(150))  # 100-150 chars Traditional Chinese
    source = Column(String(50))
    url = Column(String(500), nullable=True)
    published_at = Column(DateTime, index=True)
    category = Column(String(30), nullable=True)
    related_stocks = Column(String(50), nullable=True)  # Comma-separated codes
    relevance_score = Column(Float, nullable=True)
    fetched_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self) -> str:
        return f"<NewsArticle(id={self.id}, source={self.source})>"


# ============================================================================
# Taiwan Stock Correlation Table
# ============================================================================


class TaiwanStock(Base):
    """US-Taiwan stock correlation"""
    __tablename__ = "taiwan_stocks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    us_code = Column(String(5), index=True)
    tw_code = Column(String(4), index=True)
    tw_name = Column(String(50))
    relationship_type = Column(String(30))  # supplier, customer, competitor, etc.
    relationship_detail = Column(String(200))
    strength = Column(Float)  # 0-1 correlation strength

    def __repr__(self) -> str:
        return f"<TaiwanStock(us_code={self.us_code}, tw_code={self.tw_code})>"


# ============================================================================
# Cache Table
# ============================================================================


class APICache(Base):
    """API response cache with TTL"""
    __tablename__ = "api_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cache_key = Column(String(255), unique=True, index=True)
    cache_type = Column(String(20))  # "index", "stock", "news", "tw_stock"
    cached_data = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, index=True)

    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return datetime.utcnow() > self.expires_at

    def __repr__(self) -> str:
        return f"<APICache(key={self.cache_key}, expires_at={self.expires_at})>"


# ============================================================================
# Query Log Table
# ============================================================================


class QueryLog(Base):
    """Query execution log for auditing and analytics"""
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), index=True)
    query_text = Column(String(100))
    query_type = Column(SQLEnum(QueryTypeEnum))
    status = Column(SQLEnum(QueryStatusEnum))
    response_time_ms = Column(Integer, nullable=True)
    error_message = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self) -> str:
        return f"<QueryLog(id={self.id}, user_id={self.user_id}, status={self.status})>"


# ============================================================================
# LINE Webhook Event Table
# ============================================================================


class LineWebhookEvent(Base):
    """LINE Webhook event log"""
    __tablename__ = "line_webhook_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), index=True)
    event_type = Column(String(30))  # message, postback, etc.
    message_type = Column(String(30), nullable=True)  # text, image, etc.
    message_text = Column(String(500), nullable=True)
    raw_payload = Column(Text)  # JSON string
    processed = Column(Integer, default=0)  # 0 = unprocessed, 1 = processed
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self) -> str:
        return f"<LineWebhookEvent(id={self.id}, user_id={self.user_id}, event_type={self.event_type})>"
