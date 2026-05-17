"""
Alpha Vantage API integration as fallback for market data.
"""

import aiohttp
import asyncio
from typing import Dict, Optional
from decimal import Decimal
from datetime import datetime

from src.models.domain import Index, DataSourceEnum
from src.exceptions import APIError, TimeoutError
from src.utils.logger import get_logger
from src.config import get_settings

logger = get_logger(__name__)

# Major US market indices mapping
INDICES = {
    "^GSPC": "S&P 500",
    "^IXIC": "納斯達克綜合指數",
    "^SOX": "費城半導體指數",
}


class AlphaVantageClient:
    """Alpha Vantage API client as backup for Yahoo Finance"""

    BASE_URL = "https://www.alphavantage.co"
    TIMEOUT = 20.0  # 20 second timeout (more lenient than Yahoo)
    RATE_LIMIT_DELAY = 12.0  # Rate limit: 5 calls/min = 1 call per 12 seconds
    MAX_RETRIES = 1  # Minimal retries due to rate limiting

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Alpha Vantage client.
        
        Args:
            api_key: API key (defaults to environment variable)
        """
        if api_key is None:
            settings = get_settings()
            api_key = settings.ALPHA_VANTAGE_API_KEY
        
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def fetch_index(self, symbol: str) -> Optional[Index]:
        """
        Fetch index data from Alpha Vantage.
        
        Args:
            symbol: Index symbol (e.g., "^GSPC")
            
        Returns:
            Index object or None if failed
            
        Raises:
            TimeoutError: If request times out
        """
        session = await self._get_session()
        
        # Alpha Vantage uses different symbol format (without ^)
        av_symbol = symbol.lstrip("^") if symbol.startswith("^") else symbol
        
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,  # Keep original symbol format
            "apikey": self.api_key,
        }

        try:
            async with session.get(
                f"{self.BASE_URL}/query",
                params=params,
                timeout=aiohttp.ClientTimeout(total=self.TIMEOUT),
            ) as response:
                if response.status != 200:
                    logger.warning(f"Alpha Vantage API error for {symbol}: {response.status}")
                    return None

                data = await response.json()
                return self._parse_index_response(symbol, data)

        except asyncio.TimeoutError:
            logger.warning(f"Alpha Vantage timeout for {symbol}")
            raise TimeoutError(
                error_code="E001_TIMEOUT",
                message="Alpha Vantage API 響應超時（20 秒內無回應）"
            )
        except aiohttp.ClientError as e:
            logger.warning(f"Alpha Vantage connection error for {symbol}: {e}")
            return None

    async def fetch_indices(self, symbols: list[str]) -> Dict[str, Index]:
        """
        Fetch multiple indices with rate limiting.
        
        Args:
            symbols: List of index symbols
            
        Returns:
            Dict mapping symbol to Index object
        """
        results = {}
        
        for symbol in symbols:
            try:
                index = await self.fetch_index(symbol)
                if index:
                    results[symbol] = index
                    logger.info(f"Fetched index {symbol} from Alpha Vantage: {index.current_price}")
                    
                # Rate limiting: 12 seconds delay between calls (5 calls/min limit)
                if symbol != symbols[-1]:  # Don't sleep after last call
                    await asyncio.sleep(self.RATE_LIMIT_DELAY)
                    
            except TimeoutError:
                logger.warning(f"Timeout fetching {symbol} from Alpha Vantage")
                continue

        return results

    def _parse_index_response(self, symbol: str, data: dict) -> Optional[Index]:
        """
        Parse Alpha Vantage API response.
        
        Args:
            symbol: Index symbol
            data: JSON response from Alpha Vantage
            
        Returns:
            Index object or None if parsing fails
        """
        try:
            # Check for API rate limit error
            if "Note" in data or "Information" in data:
                logger.warning(f"Alpha Vantage rate limit exceeded for {symbol}")
                return None

            # Check for error in response
            if "Error Message" in data:
                logger.warning(f"Alpha Vantage error for {symbol}: {data['Error Message']}")
                return None

            quote = data.get("Global Quote", {})
            
            if not quote:
                logger.warning(f"No quote data in Alpha Vantage response for {symbol}")
                return None

            # Extract fields
            price = quote.get("05. price")
            previous_close = quote.get("08. previous close")
            high_52w = quote.get("04. high")
            low_52w = quote.get("05. low")

            if not price or not previous_close:
                logger.warning(f"Missing required fields for {symbol}")
                return None

            current_price = Decimal(str(price))
            prev_close = Decimal(str(previous_close))
            
            change_amount = current_price - prev_close
            change_percent = (change_amount / prev_close * 100) if prev_close > 0 else Decimal("0")

            return Index(
                id=symbol,
                zh_name=INDICES.get(symbol, symbol),
                current_price=current_price.quantize(Decimal("0.01")),
                previous_close=prev_close.quantize(Decimal("0.01")),
                change_amount=change_amount.quantize(Decimal("0.01")),
                change_percent=change_percent.quantize(Decimal("0.01")),
                high_52w=Decimal(str(high_52w or 0)).quantize(Decimal("0.01")),
                low_52w=Decimal(str(low_52w or 0)).quantize(Decimal("0.01")),
                last_updated=datetime.utcnow(),
                data_source=DataSourceEnum.ALPHA_VANTAGE,
            )

        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to parse {symbol} response from Alpha Vantage: {e}")
            return None
