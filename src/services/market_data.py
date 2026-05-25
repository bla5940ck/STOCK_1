"""
Market data service with fallback logic and caching.
"""

import decimal
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
import aiohttp

from src.models.domain import Index, Stock, DataSourceEnum
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
        Get major US market indices using Finnhub API (free tier).
        
        Priority:
        1. Check cache (5 min TTL)
        2. Finnhub API (more reliable on Render than Yahoo Finance)
        3. Return error if not available
        
        Returns:
            Dict with success status and index data or error
        """
        cache_key = CacheKeyBuilder.indices()
        
        # Step 1: Check cache
        try:
            cached_data = await self.cache_manager.get(cache_key)
            if cached_data:
                logger.info("✅ Cache hit for indices")
                return {
                    "success": True,
                    "data": [Index(**idx) for idx in cached_data["indices"]],
                    "source": "cache",
                }
        except Exception as e:
            logger.warning(f"Cache check failed: {e}")

        # Step 2: Use Finnhub API (free tier supports real-time quotes)
        try:
            logger.info("📊 Fetching indices from Finnhub API...")
            
            indices_dict = {}
            
            # Index symbols and Chinese names
            index_info = {
                "^GSPC": "S&P 500",
                "^IXIC": "納斯達克綜合指數",
                "^SOX": "費城半導體指數",
            }
            
            # Get Finnhub API key from config
            import os
            api_key = os.getenv("FINNHUB_API_KEY", "demo")
            
            # Fetch each index from Finnhub
            for symbol, zh_name in index_info.items():
                try:
                    logger.info(f"   Fetching {symbol}...")
                    
                    url = "https://finnhub.io/api/v1/quote"
                    params = {
                        "symbol": symbol,
                        "token": api_key,
                    }
                    
                    session = await self.finnhub_client._get_session()
                    
                    async with session.get(
                        url,
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=8),
                    ) as response:
                        if response.status != 200:
                            logger.warning(f"Finnhub error for {symbol}: {response.status}")
                            continue
                        
                        data = await response.json()
                        
                        # Extract quote data
                        if not data or "c" not in data or data["c"] <= 0:
                            logger.warning(f"No valid quote data for {symbol}")
                            continue
                        
                        current_price = Decimal(str(data["c"]))  # current price
                        previous_close = Decimal(str(data["pc"]))  # previous close
                        
                        # Calculate change
                        change_amount = current_price - previous_close
                        change_percent = (change_amount / previous_close * 100) if previous_close > 0 else Decimal("0")
                        
                        # Create Index object
                        index = Index(
                            id=symbol,
                            code=symbol,
                            zh_name=zh_name,
                            current_price=current_price.quantize(Decimal("0.01")),
                            previous_close=previous_close.quantize(Decimal("0.01")),
                            change_amount=change_amount.quantize(Decimal("0.01")),
                            change_percent=change_percent.quantize(Decimal("0.01")),
                            high_52w=Decimal(str(data.get("h", 0))).quantize(Decimal("0.01")) if data.get("h") else Decimal("0"),
                            low_52w=Decimal(str(data.get("l", 0))).quantize(Decimal("0.01")) if data.get("l") else Decimal("0"),
                            last_updated=datetime.utcnow(),
                            data_source=DataSourceEnum.FINNHUB,
                        )
                        
                        indices_dict[symbol] = index
                        logger.info(f"✅ Fetched {symbol}: {current_price}")
                        
                except Exception as e:
                    logger.warning(f"Failed to fetch {symbol} from Finnhub: {str(e)[:100]}")
                    continue
            
            # Check if we have at least 2 indices
            if len(indices_dict) >= 2:
                indices_list = list(indices_dict.values())
                
                # Cache successful result
                try:
                    cache_data = {
                        "indices": [idx.dict() for idx in indices_list]
                    }
                    await self.cache_manager.set(
                        cache_key,
                        cache_data,
                        "index",
                        CachePolicies.INDEX_TTL_MINUTES,
                    )
                except Exception as e:
                    logger.warning(f"Failed to cache indices: {e}")
                
                logger.info(f"✅ Successfully fetched {len(indices_list)} indices from Finnhub")
                return {
                    "success": True,
                    "data": indices_list,
                    "source": "finnhub",
                }
            else:
                logger.warning(f"Insufficient indices from Finnhub: {len(indices_dict)}")
                
        except Exception as e:
            logger.error(f"❌ Finnhub API failed: {str(e)[:100]}")

        # Step 3: All options exhausted - return error
        logger.error("🚨 Unable to fetch indices from any source")
        return {
            "success": False,
            "error_code": "E003_API_ERROR",
            "error_message": "無法取得美股指數數據，請稍後重試。",
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
