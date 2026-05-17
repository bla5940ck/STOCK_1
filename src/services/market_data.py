"""
Market data service with fallback logic and caching.
"""

from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.domain import Index, Stock
from src.integrations.yahoo_finance import YahooFinanceClient
from src.integrations.alpha_vantage import AlphaVantageClient
from src.utils.cache import CacheManager, CacheKeyBuilder, CachePolicies
from src.utils.logger import get_logger
from src.exceptions import APIError, TimeoutError as TimeoutException
from src.db.repositories import IndexRepository

logger = get_logger(__name__)

MAJOR_INDICES = ["^GSPC", "^IXIC", "^SOX"]


class MarketDataService:
    """Service for fetching market data with caching and fallback logic"""

    def __init__(self, db: AsyncSession):
        """
        Initialize market data service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.cache_manager = CacheManager(db)
        self.index_repo = IndexRepository(db)
        self.yahoo_client = YahooFinanceClient()
        self.alpha_vantage_client = AlphaVantageClient()

    async def close(self):
        """Clean up resources"""
        await self.yahoo_client.close()
        await self.alpha_vantage_client.close()

    async def get_indices(self) -> dict:
        """
        Get major US market indices with fallback logic.
        
        Logic:
        1. Check cache (5 min TTL)
        2. Try Yahoo Finance (5s timeout)
        3. If Yahoo fails, try Alpha Vantage (20s timeout)
        4. If both fail, return error
        
        Returns:
            Dict with:
            - 'success': bool
            - 'data': List[Index] (on success)
            - 'error_code': str (on failure)
            - 'error_message': str (on failure)
        """
        cache_key = CacheKeyBuilder.indices()
        
        # Step 1: Check cache
        cached_data = await self.cache_manager.get(cache_key)
        if cached_data:
            logger.info("Returning indices from cache")
            return {
                "success": True,
                "data": [Index(**idx) for idx in cached_data["indices"]],
                "source": "cache",
            }

        # Step 2: Try Yahoo Finance first
        try:
            logger.info("Fetching indices from Yahoo Finance")
            indices = await self.yahoo_client.fetch_indices(MAJOR_INDICES)
            
            if indices:
                result = {
                    "success": True,
                    "data": list(indices.values()),
                    "source": "yahoo_finance",
                }
                
                # Cache successful result
                cache_data = {
                    "indices": [idx.dict() for idx in indices.values()]
                }
                await self.cache_manager.set(
                    cache_key,
                    cache_data,
                    "index",
                    CachePolicies.INDEX_TTL_MINUTES,
                )
                
                logger.info(f"Successfully fetched {len(indices)} indices from Yahoo Finance")
                return result
                
        except TimeoutException as e:
            logger.warning(f"Yahoo Finance timeout: {e}")
        except APIError as e:
            logger.warning(f"Yahoo Finance API error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error from Yahoo Finance: {e}")

        # Step 3: Try Alpha Vantage as fallback
        try:
            logger.info("Falling back to Alpha Vantage")
            indices = await self.alpha_vantage_client.fetch_indices(MAJOR_INDICES)
            
            if indices:
                result = {
                    "success": True,
                    "data": list(indices.values()),
                    "source": "alpha_vantage",
                }
                
                # Cache successful result
                cache_data = {
                    "indices": [idx.dict() for idx in indices.values()]
                }
                await self.cache_manager.set(
                    cache_key,
                    cache_data,
                    "index",
                    CachePolicies.INDEX_TTL_MINUTES,
                )
                
                logger.info(f"Successfully fetched {len(indices)} indices from Alpha Vantage")
                return result
                
        except TimeoutException as e:
            logger.error(f"Alpha Vantage timeout: {e}")
        except Exception as e:
            logger.error(f"Unexpected error from Alpha Vantage: {e}")

        # Step 4: Both failed, try to return stale cache
        logger.warning("Both Yahoo Finance and Alpha Vantage failed")
        
        try:
            # Try to get expired cache as fallback
            all_cache = await self.cache_manager.get(cache_key)
            if all_cache:
                logger.info("Returning stale cached data")
                return {
                    "success": True,
                    "data": [Index(**idx) for idx in all_cache["indices"]],
                    "source": "stale_cache",
                    "warning": "數據可能已過期，請稍後重試"
                }
        except Exception as e:
            logger.warning(f"Failed to retrieve stale cache: {e}")

        # All options exhausted
        return {
            "success": False,
            "error_code": "E003_API_ERROR",
            "error_message": "無法從 Yahoo Finance 與 Alpha Vantage 取得指數數據，請稍後重試。",
        }

    async def get_index(self, symbol: str) -> dict:
        """
        Get single index with fallback logic.
        
        Args:
            symbol: Index symbol (e.g., "^GSPC")
            
        Returns:
            Dict with success status and index data or error
        """
        cache_key = CacheKeyBuilder.index(symbol)
        
        # Check cache first
        cached_data = await self.cache_manager.get(cache_key)
        if cached_data:
            logger.info(f"Returning {symbol} from cache")
            return {
                "success": True,
                "data": Index(**cached_data["index"]),
                "source": "cache",
            }

        # Try Yahoo Finance
        try:
            index = await self.yahoo_client.fetch_index(symbol)
            if index:
                result = {
                    "success": True,
                    "data": index,
                    "source": "yahoo_finance",
                }
                
                cache_data = {"index": index.dict()}
                await self.cache_manager.set(
                    cache_key,
                    cache_data,
                    "index",
                    CachePolicies.INDEX_TTL_MINUTES,
                )
                
                return result
                
        except (TimeoutException, APIError) as e:
            logger.warning(f"Yahoo Finance failed for {symbol}: {e}")

        # Try Alpha Vantage
        try:
            index = await self.alpha_vantage_client.fetch_index(symbol)
            if index:
                result = {
                    "success": True,
                    "data": index,
                    "source": "alpha_vantage",
                }
                
                cache_data = {"index": index.dict()}
                await self.cache_manager.set(
                    cache_key,
                    cache_data,
                    "index",
                    CachePolicies.INDEX_TTL_MINUTES,
                )
                
                return result
                
        except (TimeoutException, APIError) as e:
            logger.warning(f"Alpha Vantage failed for {symbol}: {e}")

        # Both failed
        return {
            "success": False,
            "error_code": "E003_API_ERROR",
            "error_message": f"無法取得 {symbol} 指數數據，請稍後重試。",
        }

    async def get_stock(self, stock_code: str) -> dict:
        """
        Get stock data with fallback logic.
        
        Args:
            stock_code: Stock code (e.g., "AAPL")
            
        Returns:
            Dict with success status and stock data or error
        """
        # Validate stock code format
        if not stock_code or len(stock_code) > 5:
            return {
                "success": False,
                "error_code": "E007_VALIDATION_ERROR",
                "error_message": f"無效的股票代碼：{stock_code}",
            }

        cache_key = CacheKeyBuilder.stock(stock_code)
        
        # Check cache first
        cached_data = await self.cache_manager.get(cache_key)
        if cached_data:
            logger.info(f"Returning {stock_code} from cache")
            return {
                "success": True,
                "data": Stock(**cached_data["stock"]),
                "source": "cache",
            }

        # Try Yahoo Finance
        try:
            logger.info(f"Fetching {stock_code} from Yahoo Finance")
            stock = await self.yahoo_client.fetch_stock(stock_code)
            
            if stock:
                result = {
                    "success": True,
                    "data": stock,
                    "source": "yahoo_finance",
                }
                
                cache_data = {"stock": stock.dict()}
                await self.cache_manager.set(
                    cache_key,
                    cache_data,
                    "stock",
                    CachePolicies.STOCK_TTL_MINUTES,
                )
                
                logger.info(f"Successfully fetched {stock_code}")
                return result
                
        except TimeoutException as e:
            logger.warning(f"Yahoo Finance timeout for {stock_code}: {e}")
        except APIError as e:
            logger.warning(f"Yahoo Finance API error for {stock_code}: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error fetching {stock_code}: {e}")

        # Try Alpha Vantage as fallback
        try:
            logger.info(f"Falling back to Alpha Vantage for {stock_code}")
            # Alpha Vantage doesn't have detailed stock data, so we skip it
            # and go directly to error
            
        except Exception as e:
            logger.warning(f"Fallback failed for {stock_code}: {e}")

        # Both failed
        return {
            "success": False,
            "error_code": "E004_STOCK_NOT_FOUND",
            "error_message": f"無法找到股票 {stock_code} 的相關數據，請確認代碼是否正確。",
        }
