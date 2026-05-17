"""
Cache management with TTL support.
"""

import json
from datetime import datetime, timedelta
from typing import Any, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.repositories import CacheRepository
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CacheManager:
    """Manage API response caching with TTL"""

    def __init__(self, db: AsyncSession):
        self.repo = CacheRepository(db)
        self.db = db

    async def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached data.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached data or None if not found/expired
        """
        try:
            data = await self.repo.get(cache_key)
            if data:
                logger.debug(f"Cache hit for key: {cache_key}")
            return data
        except Exception as e:
            logger.warning(f"Failed to retrieve cache for {cache_key}: {e}")
            return None

    async def set(
        self,
        cache_key: str,
        data: Dict[str, Any],
        cache_type: str,
        ttl_minutes: int = 5,
    ) -> bool:
        """
        Set cached data with TTL.
        
        Args:
            cache_key: Cache key
            data: Data to cache
            cache_type: Type of cache (index, stock, news, tw_stock)
            ttl_minutes: Time to live in minutes
            
        Returns:
            True if successful
        """
        try:
            await self.repo.set(cache_key, data, cache_type, ttl_minutes)
            await self.db.commit()
            logger.debug(f"Cache set for key: {cache_key} (TTL: {ttl_minutes}min)")
            return True
        except Exception as e:
            logger.error(f"Failed to set cache for {cache_key}: {e}")
            await self.db.rollback()
            return False

    async def invalidate(self, cache_key: str) -> bool:
        """
        Invalidate cache entry.
        
        Args:
            cache_key: Cache key
            
        Returns:
            True if successful
        """
        try:
            await self.repo.delete(cache_key)
            await self.db.commit()
            logger.debug(f"Cache invalidated for key: {cache_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate cache for {cache_key}: {e}")
            await self.db.rollback()
            return False

    async def clear_expired(self) -> int:
        """
        Clear all expired cache entries.
        
        Returns:
            Number of entries cleared
        """
        try:
            count = await self.repo.clear_expired()
            await self.db.commit()
            if count > 0:
                logger.info(f"Cleared {count} expired cache entries")
            return count
        except Exception as e:
            logger.error(f"Failed to clear expired cache: {e}")
            await self.db.rollback()
            return 0


class CacheKeyBuilder:
    """Build cache keys for different data types"""

    PREFIX = "linebot"

    @staticmethod
    def index(index_id: str) -> str:
        """Build cache key for index"""
        return f"{CacheKeyBuilder.PREFIX}:index:{index_id}"

    @staticmethod
    def indices() -> str:
        """Build cache key for all major indices"""
        return f"{CacheKeyBuilder.PREFIX}:indices:major"

    @staticmethod
    def stock(code: str) -> str:
        """Build cache key for stock"""
        return f"{CacheKeyBuilder.PREFIX}:stock:{code.upper()}"

    @staticmethod
    def stock_news(code: str) -> str:
        """Build cache key for stock-related news"""
        return f"{CacheKeyBuilder.PREFIX}:news:stock:{code.upper()}"

    @staticmethod
    def economic_news() -> str:
        """Build cache key for economic news"""
        return f"{CacheKeyBuilder.PREFIX}:news:economic"

    @staticmethod
    def tw_stocks(us_code: str) -> str:
        """Build cache key for Taiwan stock correlations"""
        return f"{CacheKeyBuilder.PREFIX}:tw_stocks:{us_code.upper()}"


class CachePolicies:
    """Cache TTL policies for different data types"""

    # Index prices: 5 minutes (market data freshness critical)
    INDEX_TTL_MINUTES = 5

    # Stock prices: 5 minutes
    STOCK_TTL_MINUTES = 5

    # Stock-related news: 1 hour
    STOCK_NEWS_TTL_HOURS = 1

    # Economic news: 1 hour
    ECONOMIC_NEWS_TTL_HOURS = 1

    # Taiwan stock correlations: 24 hours (rarely changes)
    TW_STOCK_TTL_HOURS = 24

    @staticmethod
    def get_ttl_minutes(cache_type: str) -> int:
        """Get TTL in minutes for cache type"""
        ttl_map = {
            "index": CachePolicies.INDEX_TTL_MINUTES,
            "stock": CachePolicies.STOCK_TTL_MINUTES,
            "news_stock": CachePolicies.STOCK_NEWS_TTL_HOURS * 60,
            "news_economic": CachePolicies.ECONOMIC_NEWS_TTL_HOURS * 60,
            "tw_stock": CachePolicies.TW_STOCK_TTL_HOURS * 60,
        }
        return ttl_map.get(cache_type, 5)  # Default 5 minutes


class CachedResult:
    """Wrapper for cached results with metadata"""

    def __init__(self, data: Any, cache_key: str, ttl_minutes: int = 5):
        self.data = data
        self.cache_key = cache_key
        self.ttl_minutes = ttl_minutes
        self.cached_at = datetime.utcnow()

    def is_expired(self) -> bool:
        """Check if result has expired"""
        expiration_time = self.cached_at + timedelta(minutes=self.ttl_minutes)
        return datetime.utcnow() > expiration_time

    def time_remaining_minutes(self) -> float:
        """Get remaining cache time in minutes"""
        expiration_time = self.cached_at + timedelta(minutes=self.ttl_minutes)
        remaining = (expiration_time - datetime.utcnow()).total_seconds() / 60
        return max(0, remaining)
