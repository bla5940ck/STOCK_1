"""
Market data service with fallback logic and caching.
"""

from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.domain import Index, Stock
from src.integrations.twelve_data_client import TwelveDataClient
from src.integrations.finnhub_client import FinnhubClient
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
        self.twelve_data_client = TwelveDataClient()  # Primary source (free tier)
        self.finnhub_client = FinnhubClient()  # Fallback (more reliable)
        self.yahoo_client = YahooFinanceClient()
        self.alpha_vantage_client = AlphaVantageClient()

    async def close(self):
        """Clean up resources"""
        await self.twelve_data_client.close()
        await self.finnhub_client.close()
        await self.yahoo_client.close()
        await self.alpha_vantage_client.close()

    async def get_indices(self) -> dict:
        """
        Get major US market indices with improved fallback logic (Render-optimized).
        
        NEW Priority (Render stability optimization):
        1. Check cache (5 min TTL)
        2. Try Twelve Data (8s timeout - no crumb needed, more stable)
        3. Try Finnhub (8s timeout - backup, very reliable)
        4. Try Alpha Vantage (20s timeout - slower but reliable)
        5. Try Yahoo Finance (15s timeout - has crumb dependency, last resort)
        6. Return stale cache if available
        7. Return error
        
        Returns:
            Dict with:
            - 'success': bool
            - 'data': List[Index] (on success)
            - 'error_code': str (on failure)
            - 'error_message': str (on failure)
            - 'source': str (which API was used)
        """
        cache_key = CacheKeyBuilder.indices()
        
        # Step 1: Check cache (5 min TTL)
        cached_data = await self.cache_manager.get(cache_key)
        if cached_data:
            logger.info("✅ Cache hit for indices")
            return {
                "success": True,
                "data": [Index(**idx) for idx in cached_data["indices"]],
                "source": "cache",
            }

        # Step 2: Try Twelve Data first (most stable on Render)
        try:
            logger.info("📊 Trying Twelve Data (primary)...")
            indices = await self.twelve_data_client.fetch_indices(MAJOR_INDICES)
            
            if indices:
                result = {
                    "success": True,
                    "data": list(indices.values()),
                    "source": "twelve_data",
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
                
                logger.info(f"✅ Successfully fetched {len(indices)} indices from Twelve Data")
                return result
                
        except TimeoutException as e:
            logger.warning(f"⏱️  Twelve Data timeout: {str(e)[:100]}")
        except Exception as e:
            logger.warning(f"⚠️  Twelve Data failed: {str(e)[:100]}")

        # Step 3: Try Finnhub as secondary (very reliable)
        try:
            logger.info("📊 Trying Finnhub (secondary)...")
            indices = await self.finnhub_client.fetch_indices(MAJOR_INDICES)
            
            if indices:
                result = {
                    "success": True,
                    "data": list(indices.values()),
                    "source": "finnhub",
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
                
                logger.info(f"✅ Successfully fetched {len(indices)} indices from Finnhub")
                return result
                
        except TimeoutException as e:
            logger.warning(f"⏱️  Finnhub timeout: {str(e)[:100]}")
        except Exception as e:
            logger.warning(f"⚠️  Finnhub failed: {str(e)[:100]}")

        # Step 4: Try Alpha Vantage (stable but slower)
        try:
            logger.info("📊 Trying Alpha Vantage (tertiary)...")
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
                
                logger.info(f"✅ Successfully fetched {len(indices)} indices from Alpha Vantage")
                return result
                
        except TimeoutException as e:
            logger.error(f"⏱️  Alpha Vantage timeout: {str(e)[:100]}")
        except Exception as e:
            logger.error(f"❌ Alpha Vantage failed: {str(e)[:100]}")

        # Step 5: Try Yahoo Finance as last resort (crumb dependency)
        try:
            logger.info("📊 Trying Yahoo Finance (last resort)...")
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
                
                logger.info(f"✅ Successfully fetched {len(indices)} indices from Yahoo Finance")
                return result
                
        except TimeoutException as e:
            logger.error(f"⏱️  Yahoo Finance timeout: {str(e)[:100]}")
        except Exception as e:
            logger.error(f"❌ Yahoo Finance failed: {str(e)[:100]}")

        # Step 6: All APIs failed, try to return stale cache
        logger.warning("❌ All APIs failed, checking stale cache...")
        
        try:
            # Try to get expired cache as fallback (without TTL filter)
            all_cache = await self.cache_manager.get(cache_key, ignore_ttl=True)
            if all_cache:
                logger.warning("⚠️  Returning STALE cached data (please refresh later)")
                return {
                    "success": True,
                    "data": [Index(**idx) for idx in all_cache["indices"]],
                    "source": "stale_cache",
                    "warning": "⚠️ 數據可能已過期，請稍後重試查詢最新數據"
                }
        except Exception as e:
            logger.error(f"Failed to retrieve stale cache: {str(e)[:100]}")

        # Step 7: All options exhausted - return error
        logger.error("🚨 Unable to fetch indices from any source")
        return {
            "success": False,
            "error_code": "E003_API_ERROR",
            "error_message": "❌ 無法取得美股指數數據，所有數據源均無回應。請檢查網路連接或稍後重試。",
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
        
        Fetching order:
        1. Cache (2 min TTL)
        2. Twelve Data (most reliable free tier)
        3. Finnhub (fallback, requires API key)
        4. Yahoo Finance (if Finnhub fails)
        5. Alpha Vantage (last resort)
        
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
        
        # Step 1: Check cache first
        cached_data = await self.cache_manager.get(cache_key)
        if cached_data:
            logger.info(f"Returning {stock_code} from cache")
            return {
                "success": True,
                "data": Stock(**cached_data["stock"]),
                "source": "cache",
            }

        # Step 2: Try Twelve Data (primary source - most reliable free tier)
        try:
            logger.info(f"Fetching {stock_code} from Twelve Data")
            stock = await self.twelve_data_client.fetch_stock(stock_code)
            
            if stock:
                result = {
                    "success": True,
                    "data": stock,
                    "source": "twelve_data",
                }
                
                cache_data = {"stock": stock.dict()}
                await self.cache_manager.set(
                    cache_key,
                    cache_data,
                    "stock",
                    CachePolicies.STOCK_TTL_MINUTES,
                )
                
                logger.info(f"Successfully fetched {stock_code} from Twelve Data")
                return result
                
        except TimeoutException as e:
            logger.warning(f"Twelve Data timeout for {stock_code}: {e}")
        except APIError as e:
            logger.warning(f"Twelve Data API error for {stock_code}: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error fetching from Twelve Data {stock_code}: {e}")

        # Step 3: Try Finnhub
        try:
            logger.info(f"Falling back to Finnhub for {stock_code}")
            stock = await self.finnhub_client.fetch_stock(stock_code)
            
            if stock:
                result = {
                    "success": True,
                    "data": stock,
                    "source": "finnhub",
                }
                
                cache_data = {"stock": stock.dict()}
                await self.cache_manager.set(
                    cache_key,
                    cache_data,
                    "stock",
                    CachePolicies.STOCK_TTL_MINUTES,
                )
                
                logger.info(f"Successfully fetched {stock_code} from Finnhub")
                return result
                
        except TimeoutException as e:
            logger.warning(f"Finnhub timeout for {stock_code}: {e}")
        except APIError as e:
            logger.warning(f"Finnhub API error for {stock_code}: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error fetching from Finnhub {stock_code}: {e}")

        # Step 4: Try Yahoo Finance
        try:
            logger.info(f"Falling back to Yahoo Finance for {stock_code}")
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
                
                logger.info(f"Successfully fetched {stock_code} from Yahoo Finance")
                return result
                
        except TimeoutException as e:
            logger.warning(f"Yahoo Finance timeout for {stock_code}: {e}")
        except APIError as e:
            logger.warning(f"Yahoo Finance API error for {stock_code}: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error fetching {stock_code}: {e}")

        # Step 5: Try Alpha Vantage as last resort
        try:
            logger.info(f"Falling back to Alpha Vantage for {stock_code}")
            stock_data = await self.alpha_vantage_client.fetch_stock(stock_code)
            
            if stock_data:
                from datetime import datetime
                from src.models.domain import DataSourceEnum
                stock = Stock(
                    code=stock_data.get("code", stock_code),
                    company_name=stock_data.get("name", stock_code),
                    zh_name=stock_data.get("zh_name", None),
                    current_price=stock_data.get("current_price", 0),
                    previous_close=stock_data.get("previous_close", 0),
                    change_amount=stock_data.get("change_amount", 0),
                    change_percent=stock_data.get("change_percent", 0),
                    open_price=stock_data.get("open_price", None),
                    high_price=stock_data.get("high_price", None),
                    low_price=stock_data.get("low_price", None),
                    market_cap_billion=None,
                    pe_ratio=None,
                    dividend_yield=None,
                    sector=None,
                    industry=None,
                    last_updated=datetime.utcnow(),
                    data_source=DataSourceEnum.ALPHA_VANTAGE,
                )
                
                result = {
                    "success": True,
                    "data": stock,
                    "source": "alpha_vantage",
                }
                
                cache_data = {"stock": stock.dict()}
                await self.cache_manager.set(
                    cache_key,
                    cache_data,
                    "stock",
                    CachePolicies.STOCK_TTL_MINUTES,
                )
                
                logger.info(f"Successfully fetched {stock_code} from Alpha Vantage")
                return result
            
        except Exception as e:
            logger.warning(f"Alpha Vantage fallback failed for {stock_code}: {e}")

        # All sources failed
        logger.error(f"Failed to fetch data for stock {stock_code} from all sources")
        return {
            "success": False,
            "error_code": "E004_STOCK_NOT_FOUND",
            "error_message": f"無法找到股票 {stock_code} 的相關數據，請確認代碼是否正確。",
        }
