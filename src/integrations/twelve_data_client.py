"""
Twelve Data API integration - Free tier available.
More accessible than Finnhub for demonstration purposes.
"""

import aiohttp
import asyncio
from typing import Optional
from decimal import Decimal
from datetime import datetime

from src.models.domain import Stock, DataSourceEnum
from src.exceptions import APIError, TimeoutError as TimeoutException
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TwelveDataClient:
    """Twelve Data API client for US stocks - free tier available"""

    BASE_URL = "https://api.twelvedata.com"
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
    }

    def __init__(self, api_key: str = ""):
        """
        Initialize Twelve Data client.
        Uses free plan without API key (limited requests).
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
        Fetch US stock data from Twelve Data.
        
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
            "apikey": self.api_key or "demo",  # Free tier with demo key
        }

        try:
            async with session.get(
                url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=self.TIMEOUT),
                headers={"User-Agent": "Mozilla/5.0"},
            ) as response:
                if response.status != 200:
                    logger.error(f"Twelve Data API error for {symbol}: {response.status}")
                    raise APIError(
                        error_code="E003_API_ERROR",
                        message=f"Twelve Data 返回錯誤狀態碼：{response.status}"
                    )

                data = await response.json()
                return self._parse_stock_response(symbol, data)

        except asyncio.TimeoutError:
            logger.error(f"Twelve Data timeout for {symbol}")
            raise TimeoutException(
                error_code="E001_TIMEOUT",
                message="Twelve Data API 響應超時"
            )
        except aiohttp.ClientError as e:
            logger.error(f"Twelve Data connection error for {symbol}: {e}")
            raise APIError(
                error_code="E003_API_ERROR",
                message=f"無法連接 Twelve Data：{str(e)}"
            )

    def _parse_stock_response(self, symbol: str, data: dict) -> Optional[Stock]:
        """
        Parse Twelve Data stock response.
        
        Twelve Data response format:
        {
            "symbol": "AAPL",
            "name": "Apple Inc",
            "exchange": "NASDAQ",
            "mic_code": "XNMS",
            "type": "Common Stock",
            "close": 123.45,
            "open": 120.00,
            "high": 124.00,
            "low": 119.00,
            "previous_close": 121.00,
            ...
        }
        """
        try:
            # Check for error response
            if "status" in data and data["status"] != "ok":
                logger.warning(f"Twelve Data error for {symbol}: {data.get('message', 'Unknown error')}")
                return None

            if not data or "close" not in data:
                logger.warning(f"No quote data in Twelve Data response for {symbol}")
                return None

            current_price = Decimal(str(data.get("close", 0)))
            previous_close = Decimal(str(data.get("previous_close", current_price)))

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
            company_name = data.get("name", symbol)
            
            # Extract sector/industry from available data or leave empty
            sector = data.get("sector", "")
            industry = data.get("industry", "")

            stock = Stock(
                code=symbol.upper(),
                company_name=company_name,
                zh_name=zh_name,
                current_price=current_price,
                previous_close=previous_close,
                open_price=Decimal(str(data.get("open", 0))),
                high_price=Decimal(str(data.get("high", 0))),
                low_price=Decimal(str(data.get("low", 0))),
                change_amount=change_amount,
                change_percent=change_percent,
                market_cap_billion=None,
                pe_ratio=None,
                dividend_yield=None,
                sector=sector if sector else None,
                industry=industry if industry else None,
                last_updated=datetime.utcnow(),
                data_source=DataSourceEnum.TWELVE_DATA,
                currency="USD",
                timestamp=datetime.utcnow().isoformat() + "Z",
            )

            logger.info(f"Successfully parsed Twelve Data response for {symbol}")
            return stock

        except (KeyError, TypeError, ValueError) as e:
            logger.error(f"Failed to parse Twelve Data response for {symbol}: {e}")
            return None
