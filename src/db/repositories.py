"""
Repository pattern for data access layer.
"""

import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from decimal import Decimal

from src.models.database import (
    Index, Stock, NewsArticle, TaiwanStock, APICache, QueryLog, UserQuery,
    QueryTypeEnum, QueryStatusEnum, DataSourceEnum
)
from src.models.domain import (
    Index as IndexDomain, Stock as StockDomain, NewsArticle as NewsArticleDomain,
    TaiwanStock as TaiwanStockDomain
)
from src.exceptions import DatabaseError, NotFoundError


class Repository:
    """Base repository class"""

    def __init__(self, session: AsyncSession):
        self.session = session


class IndexRepository(Repository):
    """Repository for Index data"""

    async def get_by_id(self, index_id: str) -> Optional[Index]:
        """Get index by ID"""
        result = await self.session.execute(
            select(Index).where(Index.id == index_id)
        )
        return result.scalars().first()

    async def get_all(self) -> List[Index]:
        """Get all indices"""
        result = await self.session.execute(select(Index))
        return result.scalars().all()

    async def get_major_indices(self) -> List[Index]:
        """Get major indices (^GSPC, ^IXIC, ^SOX)"""
        major_ids = ["^GSPC", "^IXIC", "^SOX"]
        result = await self.session.execute(
            select(Index).where(Index.id.in_(major_ids))
        )
        return result.scalars().all()

    async def create_or_update(self, index_data: IndexDomain) -> Index:
        """Create or update index"""
        existing = await self.get_by_id(index_data.id)

        if existing:
            existing.zh_name = index_data.zh_name
            existing.current_price = index_data.current_price
            existing.previous_close = index_data.previous_close
            existing.change_amount = index_data.change_amount
            existing.change_percent = index_data.change_percent
            existing.high_52w = index_data.high_52w
            existing.low_52w = index_data.low_52w
            existing.last_updated = datetime.utcnow()
            existing.data_source = index_data.data_source
            await self.session.flush()
            return existing

        index = Index(
            id=index_data.id,
            zh_name=index_data.zh_name,
            current_price=index_data.current_price,
            previous_close=index_data.previous_close,
            change_amount=index_data.change_amount,
            change_percent=index_data.change_percent,
            high_52w=index_data.high_52w,
            low_52w=index_data.low_52w,
            data_source=index_data.data_source,
        )
        self.session.add(index)
        await self.session.flush()
        return index


class StockRepository(Repository):
    """Repository for Stock data"""

    async def get_by_code(self, code: str) -> Optional[Stock]:
        """Get stock by code"""
        code_upper = code.upper()
        result = await self.session.execute(
            select(Stock).where(Stock.code == code_upper)
        )
        return result.scalars().first()

    async def create_or_update(self, stock_data: StockDomain) -> Stock:
        """Create or update stock"""
        existing = await self.get_by_code(stock_data.code)

        if existing:
            existing.company_name = stock_data.company_name
            existing.zh_name = stock_data.zh_name
            existing.current_price = stock_data.current_price
            existing.previous_close = stock_data.previous_close
            existing.change_amount = stock_data.change_amount
            existing.change_percent = stock_data.change_percent
            existing.market_cap_billion = stock_data.market_cap_billion
            existing.pe_ratio = stock_data.pe_ratio
            existing.dividend_yield = stock_data.dividend_yield
            existing.sector = stock_data.sector
            existing.industry = stock_data.industry
            existing.last_updated = datetime.utcnow()
            existing.data_source = stock_data.data_source
            await self.session.flush()
            return existing

        stock = Stock(
            code=stock_data.code,
            company_name=stock_data.company_name,
            zh_name=stock_data.zh_name,
            current_price=stock_data.current_price,
            previous_close=stock_data.previous_close,
            change_amount=stock_data.change_amount,
            change_percent=stock_data.change_percent,
            market_cap_billion=stock_data.market_cap_billion,
            pe_ratio=stock_data.pe_ratio,
            dividend_yield=stock_data.dividend_yield,
            sector=stock_data.sector,
            industry=stock_data.industry,
            data_source=stock_data.data_source,
        )
        self.session.add(stock)
        await self.session.flush()
        return stock


class NewsArticleRepository(Repository):
    """Repository for NewsArticle data"""

    async def get_by_id(self, article_id: str) -> Optional[NewsArticle]:
        """Get news article by ID"""
        result = await self.session.execute(
            select(NewsArticle).where(NewsArticle.id == article_id)
        )
        return result.scalars().first()

    async def get_recent(self, limit: int = 5, hours_back: int = 24) -> List[NewsArticle]:
        """Get recent news articles"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        result = await self.session.execute(
            select(NewsArticle)
            .where(NewsArticle.published_at >= cutoff_time)
            .order_by(desc(NewsArticle.published_at))
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_related_stock(self, stock_code: str, limit: int = 5) -> List[NewsArticle]:
        """Get articles related to a stock"""
        result = await self.session.execute(
            select(NewsArticle)
            .where(NewsArticle.related_stocks.ilike(f"%{stock_code}%"))
            .order_by(desc(NewsArticle.published_at))
            .limit(limit)
        )
        return result.scalars().all()

    async def create(self, article_data: NewsArticleDomain) -> NewsArticle:
        """Create news article"""
        article = NewsArticle(
            id=article_data.id,
            title=article_data.title,
            summary=article_data.summary,
            source=article_data.source,
            url=article_data.url,
            published_at=article_data.published_at,
            category=article_data.category,
            related_stocks=",".join(article_data.related_stocks or []),
            relevance_score=article_data.relevance_score,
        )
        self.session.add(article)
        await self.session.flush()
        return article


class TaiwanStockRepository(Repository):
    """Repository for Taiwan stock correlations"""

    async def get_by_us_code(self, us_code: str) -> List[TaiwanStock]:
        """Get Taiwan stocks related to US code"""
        us_code_upper = us_code.upper()
        result = await self.session.execute(
            select(TaiwanStock)
            .where(TaiwanStock.us_code == us_code_upper)
            .order_by(desc(TaiwanStock.strength))
        )
        return result.scalars().all()

    async def get_by_tw_code(self, tw_code: str) -> Optional[TaiwanStock]:
        """Get Taiwan stock by code"""
        result = await self.session.execute(
            select(TaiwanStock).where(TaiwanStock.tw_code == tw_code)
        )
        return result.scalars().first()

    async def create_or_update(self, tw_stock_data: TaiwanStockDomain) -> TaiwanStock:
        """Create or update Taiwan stock correlation"""
        existing = await self.session.execute(
            select(TaiwanStock).where(
                and_(
                    TaiwanStock.us_code == tw_stock_data.us_code,
                    TaiwanStock.tw_code == tw_stock_data.tw_code,
                )
            )
        )
        existing_record = existing.scalars().first()

        if existing_record:
            existing_record.tw_name = tw_stock_data.tw_name
            existing_record.relationship_type = tw_stock_data.relationship_type
            existing_record.relationship_detail = tw_stock_data.relationship_detail
            existing_record.strength = tw_stock_data.strength
            await self.session.flush()
            return existing_record

        tw_stock = TaiwanStock(
            us_code=tw_stock_data.us_code,
            tw_code=tw_stock_data.tw_code,
            tw_name=tw_stock_data.tw_name,
            relationship_type=tw_stock_data.relationship_type,
            relationship_detail=tw_stock_data.relationship_detail,
            strength=tw_stock_data.strength,
        )
        self.session.add(tw_stock)
        await self.session.flush()
        return tw_stock


class CacheRepository(Repository):
    """Repository for API cache with TTL support"""

    async def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached data if not expired"""
        result = await self.session.execute(
            select(APICache).where(APICache.cache_key == cache_key)
        )
        cache_entry = result.scalars().first()

        if not cache_entry:
            return None

        if cache_entry.is_expired():
            await self.delete(cache_key)
            return None

        return json.loads(cache_entry.cached_data)

    async def set(
        self,
        cache_key: str,
        data: Dict[str, Any],
        cache_type: str,
        ttl_minutes: int = 5,
    ) -> APICache:
        """Set cached data with TTL"""
        expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)

        # Try to update existing
        result = await self.session.execute(
            select(APICache).where(APICache.cache_key == cache_key)
        )
        existing = result.scalars().first()

        if existing:
            existing.cached_data = json.dumps(data)
            existing.expires_at = expires_at
            await self.session.flush()
            return existing

        # Create new
        cache_entry = APICache(
            cache_key=cache_key,
            cache_type=cache_type,
            cached_data=json.dumps(data),
            expires_at=expires_at,
        )
        self.session.add(cache_entry)
        await self.session.flush()
        return cache_entry

    async def delete(self, cache_key: str) -> None:
        """Delete cache entry"""
        await self.session.execute(
            select(APICache).where(APICache.cache_key == cache_key)
        )
        result = await self.session.execute(
            select(APICache).where(APICache.cache_key == cache_key)
        )
        entry = result.scalars().first()
        if entry:
            await self.session.delete(entry)
            await self.session.flush()

    async def clear_expired(self) -> int:
        """Clear all expired cache entries"""
        result = await self.session.execute(
            select(APICache).where(APICache.expires_at <= datetime.utcnow())
        )
        expired = result.scalars().all()
        for entry in expired:
            await self.session.delete(entry)
        await self.session.flush()
        return len(expired)


class QueryLogRepository(Repository):
    """Repository for query logging"""

    async def create(
        self,
        user_id: str,
        query_text: str,
        query_type: QueryTypeEnum,
        status: QueryStatusEnum,
        response_time_ms: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> QueryLog:
        """Log a query"""
        log = QueryLog(
            user_id=user_id,
            query_text=query_text,
            query_type=query_type,
            status=status,
            response_time_ms=response_time_ms,
            error_message=error_message,
        )
        self.session.add(log)
        await self.session.flush()
        return log

    async def get_user_history(
        self, user_id: str, limit: int = 10
    ) -> List[QueryLog]:
        """Get user query history"""
        result = await self.session.execute(
            select(QueryLog)
            .where(QueryLog.user_id == user_id)
            .order_by(desc(QueryLog.created_at))
            .limit(limit)
        )
        return result.scalars().all()
