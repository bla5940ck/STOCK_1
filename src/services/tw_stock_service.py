"""
Taiwan stock service for fetching related Taiwan stocks.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.models.domain import TaiwanStock
from src.utils.cache import CacheManager, CacheKeyBuilder, CachePolicies
from src.utils.logger import get_logger
from src.db.repositories import TaiwanStockRepository

logger = get_logger(__name__)


class TaiwanStockService:
    """Service for Taiwan stock correlation lookups"""

    def __init__(self, db: AsyncSession):
        """Initialize service with database session"""
        self.db = db
        self.repo = TaiwanStockRepository(db)
        self.cache_manager = CacheManager(db)

    async def get_related_tw_stocks(
        self, us_code: str, limit: int = 10
    ) -> dict:
        """
        Get Taiwan stocks related to a US stock code.
        
        Args:
            us_code: US stock code (e.g., "AAPL")
            limit: Maximum number of stocks to return (default 10)
            
        Returns:
            Dict with:
            - 'success': bool
            - 'data': List[TaiwanStock] (sorted by strength, high to low)
            - 'source': str ('cache' or 'database')
            - 'count': int
        """
        cache_key = CacheKeyBuilder.tw_stocks(us_code)

        try:
            # Check cache first (24 hour TTL)
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result:
                logger.info(f"Taiwan stock cache hit for {us_code}")
                return {
                    "success": True,
                    "data": cached_result,
                    "source": "cache",
                    "count": len(cached_result),
                }

            # Query database
            logger.info(f"Querying database for Taiwan stocks related to {us_code}")
            tw_stocks = await self.repo.get_by_us_code(us_code)

            if not tw_stocks:
                logger.info(f"No Taiwan stocks found for {us_code}")
                return {
                    "success": True,
                    "data": [],
                    "source": "database",
                    "count": 0,
                }

            # Convert ORM objects to domain models
            from src.models.domain import TaiwanStock as TaiwanStockDomain
            
            tw_stock_domains = [
                TaiwanStockDomain(
                    us_code=stock.us_code,
                    tw_code=stock.tw_code,
                    tw_name=stock.tw_name,
                    relationship_type=stock.relationship_type,
                    relationship_detail=stock.relationship_detail,
                    strength=stock.strength,
                )
                for stock in tw_stocks[:limit]
            ]

            # Cache the result (24 hour TTL)
            await self.cache_manager.set(
                cache_key,
                tw_stock_domains,
                cache_type="tw_stock",
                ttl_minutes=CachePolicies.TW_STOCK_TTL_HOURS * 60,
            )

            logger.info(
                f"Taiwan stock query successful for {us_code}, "
                f"returned {len(tw_stock_domains)} stocks"
            )

            return {
                "success": True,
                "data": tw_stock_domains,
                "source": "database",
                "count": len(tw_stock_domains),
            }

        except Exception as e:
            logger.error(f"Error fetching Taiwan stocks for {us_code}: {e}")
            return {
                "success": False,
                "error_code": "E005_TW_STOCK_FETCH_ERROR",
                "error_message": f"無法取得台股相關標的：{str(e)}",
                "data": [],
                "count": 0,
            }

    async def close(self):
        """Close service resources"""
        # No specific cleanup needed for now
        pass
