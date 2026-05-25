"""
Market data service with fallback logic and caching.
"""

import decimal
import asyncio
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.domain import Index, Stock, DataSourceEnum
from src.integrations.twelve_data_client import TwelveDataClient
from src.integrations.finnhub_client import FinnhubClient
from src.integrations.yahoo_finance import YahooFinanceClient
from src.integrations.alpha_vantage import AlphaVantageClient
from src.integrations.iex_cloud import IEXCloudClient
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
        self.iex_cloud_client = IEXCloudClient()  # Primary source (reliable, free tier)
        self.twelve_data_client = TwelveDataClient()  # Fallback
        self.finnhub_client = FinnhubClient()  # Fallback
        self.yahoo_client = YahooFinanceClient()  # Fallback
        self.alpha_vantage_client = AlphaVantageClient()  # Fallback

    async def close(self):
        """Clean up resources"""
        await self.twelve_data_client.close()
        await self.finnhub_client.close()
        await self.yahoo_client.close()
        await self.alpha_vantage_client.close()

    async def get_indices(self) -> dict:
        """
        Get major US market indices with multiple fallbacks.
        
        Strategy:
        1. Check cache (5 min TTL)
        2. Try IEX Cloud (reliable on Render)
        3. Fall back to yfinance library
        4. Fall back to last-known data in database
        5. Return error if nothing available
        
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

        # Step 2: Try IEX Cloud (most reliable on Render)
        try:
            logger.info("📊 Fetching indices from IEX Cloud...")
            
            quotes = await self.iex_cloud_client.fetch_indices(MAJOR_INDICES)
            
            if quotes and len(quotes) >= 2:
                indices_dict = {}
                
                symbols_info = {
                    "^GSPC": "S&P 500",
                    "^IXIC": "納斯達克綜合指數",
                    "^SOX": "費城半導體指數",
                }
                
                for symbol, zh_name in symbols_info.items():
                    if symbol not in quotes:
                        continue
                    
                    try:
                        quote = quotes[symbol]
                        
                        current_price = Decimal(str(quote.get("latestPrice", 0)))
                        previous_close = Decimal(str(quote.get("previousClose", 0)))
                        high_52w = Decimal(str(quote.get("week52High", 0)))
                        low_52w = Decimal(str(quote.get("week52Low", 0)))
                        
                        if current_price <= 0 or previous_close <= 0:
                            logger.warning(f"Invalid price for {symbol}: {current_price}")
                            continue
                        
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
                            high_52w=high_52w.quantize(Decimal("0.01")),
                            low_52w=low_52w.quantize(Decimal("0.01")),
                            last_updated=datetime.utcnow(),
                            data_source=DataSourceEnum.YAHOO_FINANCE,  # Keep for compatibility
                        )
                        
                        indices_dict[symbol] = index
                        logger.info(f"✅ Fetched {symbol} from IEX: {current_price}")
                        
                    except Exception as e:
                        logger.warning(f"Failed to parse {symbol}: {str(e)[:100]}")
                        continue
                
                if len(indices_dict) >= 2:
                    indices_list = list(indices_dict.values())
                    
                    # Save to database and cache
                    try:
                        for idx in indices_list:
                            await self.index_repo.create_or_update(idx)
                        await self.db.commit()
                        logger.info("✅ Saved indices to database")
                    except Exception as e:
                        logger.warning(f"Failed to save to database: {e}")
                    
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
                    
                    logger.info(f"✅ Successfully fetched {len(indices_list)} indices from IEX Cloud")
                    return {
                        "success": True,
                        "data": indices_list,
                        "source": "iex_cloud",
                    }
        except Exception as e:
            logger.warning(f"⚠️  IEX Cloud fetch failed: {str(e)[:100]}")

        # Step 3: Fall back to yfinance
        try:
            import yfinance as yf
            logger.info("📊 Fetching indices from yfinance (fallback)...")
            
            def fetch_with_yfinance():
                """Synchronous function to fetch using yfinance"""
                indices_dict = {}
                
                symbols_info = {
                    "^GSPC": "S&P 500",
                    "^IXIC": "納斯達克綜合指數",
                    "^SOX": "費城半導體指數",
                }
                
                for symbol, zh_name in symbols_info.items():
                    try:
                        logger.info(f"   Fetching {symbol}...")
                        
                        # Create ticker object
                        ticker = yf.Ticker(symbol)
                        
                        # Get historical data (last 10 days to ensure we have data)
                        history = ticker.history(period="10d")
                        
                        if history is None or len(history) == 0:
                            logger.warning(f"No historical data for {symbol}")
                            continue
                        
                        # Get the most recent row
                        latest = history.iloc[-1]
                        previous = history.iloc[-2] if len(history) > 1 else latest
                        
                        # Extract OHLCV data
                        current_price = Decimal(str(latest['Close']))
                        previous_close = Decimal(str(previous['Close']))
                        
                        if current_price <= 0:
                            logger.warning(f"Invalid price for {symbol}: {current_price}")
                            continue
                        
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
                            high_52w=Decimal(str(history['High'].max())).quantize(Decimal("0.01")),
                            low_52w=Decimal(str(history['Low'].min())).quantize(Decimal("0.01")),
                            last_updated=datetime.utcnow(),
                            data_source=DataSourceEnum.YAHOO_FINANCE,
                        )
                        
                        indices_dict[symbol] = index
                        logger.info(f"✅ Fetched {symbol}: {current_price}")
                        
                    except Exception as e:
                        logger.warning(f"Failed to fetch {symbol}: {str(e)[:100]}")
                        continue
                
                return indices_dict
            
            # Run yfinance in thread pool
            loop = asyncio.get_event_loop()
            indices_dict = await loop.run_in_executor(None, fetch_with_yfinance)
            
            if indices_dict and len(indices_dict) >= 2:
                indices_list = list(indices_dict.values())
                
                # Save to database and cache
                try:
                    for idx in indices_list:
                        await self.index_repo.create_or_update(idx)
                    await self.db.commit()
                    logger.info("✅ Saved indices to database")
                except Exception as e:
                    logger.warning(f"Failed to save to database: {e}")
                
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
                
                logger.info(f"✅ Successfully fetched {len(indices_list)} indices from yfinance")
                return {
                    "success": True,
                    "data": indices_list,
                    "source": "yfinance",
                }
            else:
                logger.warning(f"Insufficient indices from yfinance: {len(indices_dict) if indices_dict else 0}")
                
        except Exception as e:
            logger.warning(f"⚠️  yfinance fetch failed: {str(e)[:100]}")

        # Step 4: Fall back to database - get last-known indices
        logger.warning("⚠️  Getting last-known indices from database...")
        
        try:
            db_indices = await self.index_repo.get_major_indices()
            
            if db_indices and len(db_indices) >= 2:
                logger.info(f"✅ Using {len(db_indices)} indices from database")
                
                # Convert to domain objects
                result_indices = []
                for idx in db_indices:
                    domain_idx = Index(
                        id=idx.id,
                        code=idx.code,
                        zh_name=idx.zh_name,
                        current_price=idx.current_price,
                        previous_close=idx.previous_close,
                        change_amount=idx.change_amount,
                        change_percent=idx.change_percent,
                        high_52w=idx.high_52w,
                        low_52w=idx.low_52w,
                        last_updated=idx.last_updated,
                        data_source=idx.data_source,
                    )
                    result_indices.append(domain_idx)
                
                return {
                    "success": True,
                    "data": result_indices,
                    "source": "database",
                    "warning": "⚠️ 數據來自上次成功的查詢，可能不是最新的實時數據",
                }
            else:
                logger.warning("No indices in database")
                
        except Exception as e:
            logger.error(f"Failed to get indices from database: {str(e)[:100]}")

        # Step 4: Everything failed - return error
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
