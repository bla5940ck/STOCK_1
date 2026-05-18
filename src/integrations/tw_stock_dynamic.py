"""
Taiwan stock integration - Dynamic fetching from multiple sources.
Supports fetching all Taiwan stocks and searching by code or name.
"""

import aiohttp
import asyncio
import json
from typing import Dict, Optional, List, Tuple
from decimal import Decimal
from datetime import datetime
import re

from src.models.domain import Stock, DataSourceEnum
from src.exceptions import APIError, TimeoutError as TimeoutException
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DynamicTaiwanStockClient:
    """
    Dynamic Taiwan stock client that fetches stock list from multiple sources.
    Supports:
    - Fetching all Taiwan stocks (2000+) dynamically
    - Searching by code or Chinese name
    - Real-time price fetching
    """

    # Alternative data sources for Taiwan stocks
    SOURCES = {
        "finmind": "https://api.finmindtrade.com/api/v4/data",
        "tpex": "https://www.tpex.org.tw/web/stock/aftertrading/daily_trading_info/st43_result.php",
    }
    
    TIMEOUT = 10.0
    
    _all_stocks_cache = None
    _cache_timestamp = None
    CACHE_TTL = 3600 * 24  # 24 hours
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()

    async def get_all_tw_stocks(self) -> List[Dict]:
        """
        Get all Taiwan stocks from cache or fetch dynamically.
        
        Returns:
            List of stock dicts with: code, zh_name, market, type
        """
        # Check cache
        if self._all_stocks_cache and (datetime.now().timestamp() - self._cache_timestamp) < self.CACHE_TTL:
            logger.info(f"Returning {len(self._all_stocks_cache)} cached Taiwan stocks")
            return self._all_stocks_cache

        # Try fetching from FinMind API (most complete source)
        try:
            stocks = await self._fetch_from_finmind()
            if stocks:
                self._all_stocks_cache = stocks
                self._cache_timestamp = datetime.now().timestamp()
                logger.info(f"Fetched {len(stocks)} Taiwan stocks from FinMind")
                return stocks
        except Exception as e:
            logger.warning(f"FinMind fetch failed: {e}")

        # Fallback: Try TPEX API for OTC stocks
        try:
            stocks = await self._fetch_from_tpex()
            if stocks:
                self._all_stocks_cache = stocks
                self._cache_timestamp = datetime.now().timestamp()
                logger.info(f"Fetched {len(stocks)} Taiwan stocks from TPEX")
                return stocks
        except Exception as e:
            logger.warning(f"TPEX fetch failed: {e}")

        # Last resort: Local fallback
        logger.warning("All dynamic sources failed, using local fallback")
        return await self._get_local_fallback()

    async def _fetch_from_finmind(self) -> Optional[List[Dict]]:
        """
        Fetch all Taiwan stocks from FinMind API.
        This is the most reliable source for all 2000+ stocks.
        
        API: https://api.finmindtrade.com/api/v4/data
        Dataset: TaiwanStockInfo - contains all listed companies
        """
        session = await self._get_session()
        
        params = {
            "dataset": "TaiwanStockInfo",
        }
        
        try:
            async with session.get(
                self.SOURCES["finmind"],
                params=params,
                timeout=aiohttp.ClientTimeout(total=self.TIMEOUT),
            ) as response:
                if response.status != 200:
                    logger.error(f"FinMind API error: {response.status}")
                    return None

                data = await response.json()
                
                if "data" not in data:
                    logger.error("Unexpected FinMind response structure")
                    return None

                stocks = []
                for item in data["data"]:
                    try:
                        stock = {
                            "code": str(item.get("stock_id", "")).strip(),
                            "zh_name": item.get("stock_name", "").strip(),
                            "market": item.get("market_type", "TSE").strip(),  # TSE or OTC
                            "type": item.get("industry_category", "").strip(),
                        }
                        
                        # Filter invalid entries
                        if stock["code"] and stock["zh_name"]:
                            stocks.append(stock)
                    except (KeyError, TypeError) as e:
                        logger.warning(f"Failed to parse stock item: {e}")
                        continue

                logger.info(f"Successfully parsed {len(stocks)} stocks from FinMind")
                return stocks

        except asyncio.TimeoutError:
            logger.error("FinMind request timeout")
            raise TimeoutException(
                error_code="E001_TIMEOUT",
                message="台股列表 API 響應超時"
            )
        except aiohttp.ClientError as e:
            logger.error(f"FinMind connection error: {e}")
            raise APIError(
                error_code="E003_API_ERROR",
                message=f"無法連接台股 API：{str(e)}"
            )

    async def _fetch_from_tpex(self) -> Optional[List[Dict]]:
        """
        Fetch OTC (櫃買中心) stocks from TPEX.
        Fallback source if FinMind fails.
        """
        session = await self._get_session()
        
        try:
            async with session.get(
                self.SOURCES["tpex"],
                timeout=aiohttp.ClientTimeout(total=self.TIMEOUT),
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            ) as response:
                if response.status != 200:
                    return None

                # Parse HTML table (TPEX returns HTML, not JSON)
                text = await response.text()
                
                # Extract stock data from HTML using regex
                # This is a simplified parser - adjust based on actual HTML structure
                stocks = []
                
                # Pattern: stock code, stock name in Chinese
                pattern = r'(\d{4})\s+([一-龥a-zA-Z0-9&\-]+)'
                matches = re.findall(pattern, text)
                
                for code, name in matches:
                    stocks.append({
                        "code": code,
                        "zh_name": name.strip(),
                        "market": "OTC",
                        "type": "",
                    })

                logger.info(f"Parsed {len(stocks)} OTC stocks from TPEX")
                return stocks if stocks else None

        except Exception as e:
            logger.error(f"TPEX fetch error: {e}")
            return None

    async def _get_local_fallback(self) -> List[Dict]:
        """
        Get local fallback stock list from JSON file.
        Used when all dynamic sources fail.
        """
        try:
            import json
            with open("src/data/tw_stocks.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                stocks = data.get("stocks", [])
                logger.info(f"Loaded {len(stocks)} stocks from local fallback")
                return stocks
        except Exception as e:
            logger.error(f"Local fallback failed: {e}")
            return []

    async def search_stock(self, query: str) -> Optional[Dict]:
        """
        Search for a Taiwan stock by code or Chinese name.
        
        Args:
            query: Stock code (e.g., "2330") or Chinese name (e.g., "健策")
            
        Returns:
            Stock dict or None if not found
        """
        all_stocks = await self.get_all_tw_stocks()
        
        # Clean query
        query = query.strip().upper()
        
        # Search by code first (exact match)
        for stock in all_stocks:
            if stock["code"].upper() == query:
                logger.info(f"Found stock by code: {query}")
                return stock
        
        # Search by Chinese name (fuzzy match)
        query_lower = query.lower()
        for stock in all_stocks:
            zh_name = stock.get("zh_name", "").lower()
            if query_lower in zh_name or zh_name.startswith(query_lower):
                logger.info(f"Found stock by name: {query} -> {stock['zh_name']}")
                return stock
        
        # Partial match for Chinese names
        for stock in all_stocks:
            zh_name = stock.get("zh_name", "")
            # Chinese character comparison
            if any(char in zh_name for char in query):
                logger.info(f"Found stock by partial match: {query} -> {zh_name}")
                return stock
        
        logger.warning(f"Stock not found: {query}")
        return None

    async def fetch_stock_price(self, code: str) -> Optional[Decimal]:
        """
        Fetch real-time stock price for Taiwan stock.
        
        Args:
            code: Stock code (e.g., "2330")
            
        Returns:
            Current price or None if failed
        """
        session = await self._get_session()
        
        # Try TWSE API for current market data
        url = "https://mis.twse.com.tw/stock/api/getStockInfo.jsp"
        params = {
            "ex_ch": f"tse_{code}.tw|otc_{code}.tw",
            "json": "1",
            "delay": "5",
        }
        
        try:
            async with session.get(
                url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=5),
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                }
            ) as response:
                if response.status != 200:
                    return None

                data = await response.json()
                
                if "msgArray" in data and data["msgArray"]:
                    msg = data["msgArray"][0]
                    price_str = msg.get("z", "")  # Current price
                    
                    if price_str:
                        try:
                            return Decimal(price_str)
                        except:
                            return None
                
                return None

        except Exception as e:
            logger.warning(f"Failed to fetch price for {code}: {e}")
            return None


# Global instance
_client = None


async def get_taiwan_stock_client() -> DynamicTaiwanStockClient:
    """Get or create global Taiwan stock client"""
    global _client
    if _client is None:
        _client = DynamicTaiwanStockClient()
    return _client
