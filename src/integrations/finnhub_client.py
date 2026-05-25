"""
Finnhub API integration as primary US stock data source.
More reliable than Yahoo Finance for free-tier access.
"""

import aiohttp
import asyncio
from typing import Optional, Dict
from decimal import Decimal
from datetime import datetime

from src.models.domain import Stock, DataSourceEnum
from src.exceptions import APIError, TimeoutError as TimeoutException
from src.utils.logger import get_logger

logger = get_logger(__name__)


class FinnhubClient:
    """Finnhub API client for US stocks - free tier available"""

    BASE_URL = "https://finnhub.io/api/v1"
    TIMEOUT = 8.0
    
    # Chinese names for popular stocks
    STOCK_NAMES = {
        "AAPL": "蘋果公司",
        "MSFT": "微軟公司",
        "GOOGL": "字母表公司",
        "AMZN": "亞馬遜公司",
        "TSLA": "特斯拉公司",
        "META": "Meta公司",
        "NVDA": "英偉達",
        "JPM": "摩根大通",
        "V": "Visa公司",
        "WMT": "沃爾瑪",
        "PG": "寶潔公司",
        "JNJ": "強生公司",
        "MA": "萬事達卡",
        "KO": "可口可樂",
        "MCD": "麥當勞",
        "BA": "波音",
        "CAT": "卡特彼勒",
        "UNH": "聯合健康",
        "GE": "通用電氣",
        "F": "福特",
        "GM": "通用汽車",
        "IBM": "國際商業機器",
        "INTC": "英特爾",
        "AMD": "AMD公司",
        "NFLX": "奈飛",
        "UBER": "優步",
        "SPOT": "Spotify",
        "HOOD": "羅賓漢",
    }

    def __init__(self, api_key: str = "demo"):
        """
        Initialize Finnhub client.
        
        Args:
            api_key: Finnhub API key (default: 'demo' for limited free access)
                    Get free key at: https://finnhub.io/ (1000 req/month)
        """
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()

    async def fetch_stock(self, symbol: str) -> Optional[Stock]:
        """
        Fetch US stock data from Finnhub.
        
        Args:
            symbol: Stock symbol (e.g., "AAPL")
            
        Returns:
            Stock object or None if failed
            
        Raises:
            TimeoutError: If request times out
            APIError: If API returns error
        """
        session = await self._get_session()
        
        url = f"{self.BASE_URL}/quote"
        params = {
            "symbol": symbol.upper(),
            "token": self.api_key,
        }

        try:
            async with session.get(
                url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=self.TIMEOUT),
            ) as response:
                if response.status != 200:
                    logger.error(f"Finnhub API error for {symbol}: {response.status}")
                    raise APIError(
                        error_code="E003_API_ERROR",
                        message=f"Finnhub 返回錯誤狀態碼：{response.status}"
                    )

                data = await response.json()
                return self._parse_stock_response(symbol, data)

        except asyncio.TimeoutError:
            logger.error(f"Finnhub timeout for {symbol}")
            raise TimeoutException(
                error_code="E001_TIMEOUT",
                message="Finnhub API 響應超時（8 秒內無回應）"
            )
        except aiohttp.ClientError as e:
            logger.error(f"Finnhub connection error for {symbol}: {e}")
            raise APIError(
                error_code="E003_API_ERROR",
                message=f"無法連接 Finnhub：{str(e)}"
            )

    def _parse_stock_response(self, symbol: str, data: dict) -> Optional[Stock]:
        """
        Parse Finnhub stock response.
        
        Finnhub response format:
        {
            "c": current_price,
            "pc": previous_close,
            "h": high,
            "l": low,
            "o": open,
            "t": timestamp
        }
        """
        try:
            # Check for valid response
            if not data or "c" not in data:
                logger.error(f"Invalid Finnhub response for {symbol}: {data}")
                return None

            current_price = Decimal(str(data.get("c", 0)))
            previous_close = Decimal(str(data.get("pc", current_price)))

            # Skip zero prices
            if current_price <= 0:
                logger.warning(f"Zero or negative price for {symbol}")
                return None

            change_amount = current_price - previous_close
            change_percent = (
                (change_amount / previous_close * 100)
                if previous_close > 0
                else Decimal("0")
            )

            zh_name = self.STOCK_NAMES.get(symbol.upper(), symbol)

            stock = Stock(
                code=symbol.upper(),
                name=symbol,
                zh_name=zh_name,
                current_price=current_price,
                previous_close=previous_close,
                open_price=Decimal(str(data.get("o", 0))),
                high_price=Decimal(str(data.get("h", 0))),
                low_price=Decimal(str(data.get("l", 0))),
                change_amount=change_amount,
                change_percent=change_percent,
                data_source=DataSourceEnum.FINNHUB,
                currency="USD",
                timestamp=datetime.utcnow().isoformat() + "Z",
            )

            logger.info(f"Successfully parsed Finnhub data for {symbol}")
            return stock

        except (KeyError, TypeError, ValueError) as e:
            logger.error(f"Failed to parse Finnhub response for {symbol}: {e}")
            return None

    async def fetch_quote(self, symbol: str) -> Optional[Dict]:
        """
        Fetch raw quote data for any symbol (stocks or indices).
        
        Args:
            symbol: Symbol (e.g., "AAPL" or "^GSPC")
            
        Returns:
            Raw quote dict or None if failed
        """
        session = await self._get_session()
        
        url = f"{self.BASE_URL}/quote"
        params = {
            "symbol": symbol.upper(),
            "token": self.api_key,
        }

        try:
            async with session.get(
                url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=self.TIMEOUT),
            ) as response:
                if response.status != 200:
                    logger.warning(f"Finnhub API error for {symbol}: {response.status}")
                    return None

                data = await response.json()
                if data and "c" in data:
                    return data
                return None

        except Exception as e:
            logger.warning(f"Finnhub quote fetch failed for {symbol}: {str(e)[:100]}")
            return None

    async def fetch_indices(self, symbols: list[str]) -> Dict[str, Dict]:
        """
        Fetch multiple index quotes.
        
        Args:
            symbols: List of index symbols (e.g., ["^GSPC", "^IXIC", "^SOX"])
            
        Returns:
            Dict mapping symbol -> quote data
        """
        results = {}
        
        for symbol in symbols:
            quote = await self.fetch_quote(symbol)
            if quote:
                results[symbol] = quote
                logger.info(f"✅ Fetched {symbol} from Finnhub: ${quote.get('c')}")
            else:
                logger.warning(f"⚠️ Failed to fetch {symbol} from Finnhub")
        
        return results
