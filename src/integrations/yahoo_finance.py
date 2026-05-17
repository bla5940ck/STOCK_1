"""
Yahoo Finance API integration for fetching index and stock data.
"""

import aiohttp
import asyncio
from typing import Dict, Optional, Tuple
from decimal import Decimal
from datetime import datetime
import random

from src.models.domain import Index, Stock, DataSourceEnum
from src.exceptions import APIError, TimeoutError
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Major US market indices
INDICES = {
    "^GSPC": "S&P 500",
    "^IXIC": "納斯達克綜合指數",
    "^SOX": "費城半導體指數",
}


class YahooFinanceClient:
    """Yahoo Finance API client for fetching market data"""

    BASE_URL = "https://query1.finance.yahoo.com"
    TIMEOUT = 5.0  # 5 second timeout
    RATE_LIMIT_DELAY = 1.0  # 1 second between calls
    
    # User-Agent rotation to bypass anti-bot measures
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    ]

    def __init__(self):
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

    def _get_random_user_agent(self) -> str:
        """Get random User-Agent for anti-bot bypass"""
        return random.choice(self.USER_AGENTS)

    async def fetch_index(self, symbol: str) -> Optional[Index]:
        """
        Fetch single index data from Yahoo Finance.
        
        Args:
            symbol: Index symbol (e.g., "^GSPC")
            
        Returns:
            Index object or None if failed
            
        Raises:
            TimeoutError: If request times out
            APIError: If API returns error
        """
        session = await self._get_session()
        
        url = f"{self.BASE_URL}/v10/finance/quoteSummary/{symbol}"
        params = {
            "modules": "price",
        }
        
        headers = {
            "User-Agent": self._get_random_user_agent(),
        }

        try:
            async with session.get(
                url,
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.TIMEOUT),
            ) as response:
                if response.status != 200:
                    logger.error(f"Yahoo Finance API error for {symbol}: {response.status}")
                    raise APIError(
                        error_code="E003_API_ERROR",
                        message=f"Yahoo Finance 返回錯誤狀態碼：{response.status}"
                    )

                data = await response.json()
                return self._parse_index_response(symbol, data)

        except asyncio.TimeoutError:
            logger.error(f"Yahoo Finance timeout for {symbol}")
            raise TimeoutError(
                error_code="E001_TIMEOUT",
                message="Yahoo Finance API 響應超時（5 秒內無回應）"
            )
        except aiohttp.ClientError as e:
            logger.error(f"Yahoo Finance connection error for {symbol}: {e}")
            raise APIError(
                error_code="E003_API_ERROR",
                message=f"無法連接 Yahoo Finance：{str(e)}"
            )

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
                    logger.info(f"Fetched index {symbol}: {index.current_price}")
                    
                # Rate limiting: 1 second delay between calls
                if symbol != symbols[-1]:  # Don't sleep after last call
                    await asyncio.sleep(self.RATE_LIMIT_DELAY)
                    
            except (TimeoutError, APIError) as e:
                logger.warning(f"Failed to fetch {symbol}: {e}")
                # Continue with next symbol instead of failing entirely
                continue

        return results

    def _parse_index_response(
        self, symbol: str, data: dict
    ) -> Optional[Index]:
        """
        Parse Yahoo Finance API response.
        
        Args:
            symbol: Index symbol
            data: JSON response from Yahoo Finance
            
        Returns:
            Index object or None if parsing fails
        """
        try:
            # Extract price data from response
            # Yahoo Finance v10 API structure: quoteSummary -> result[0] -> price
            if "quoteSummary" not in data or "result" not in data["quoteSummary"]:
                logger.error(f"Unexpected response structure for {symbol}")
                return None

            result = data["quoteSummary"]["result"][0]
            if "price" not in result:
                logger.error(f"No price data for {symbol}")
                return None

            price_data = result["price"]

            # Extract required fields
            current_price = Decimal(str(price_data.get("regularMarketPrice", {}).get("raw", 0)))
            previous_close = Decimal(str(price_data.get("regularMarketPreviousClose", {}).get("raw", 0)))
            high_52w = Decimal(str(price_data.get("fiftyTwoWeekHigh", {}).get("raw", 0)))
            low_52w = Decimal(str(price_data.get("fiftyTwoWeekLow", {}).get("raw", 0)))

            # Calculate change
            change_amount = current_price - previous_close
            change_percent = (change_amount / previous_close * 100) if previous_close > 0 else Decimal("0")

            return Index(
                id=symbol,
                zh_name=INDICES.get(symbol, symbol),
                current_price=current_price.quantize(Decimal("0.01")),
                previous_close=previous_close.quantize(Decimal("0.01")),
                change_amount=change_amount.quantize(Decimal("0.01")),
                change_percent=change_percent.quantize(Decimal("0.01")),
                high_52w=high_52w.quantize(Decimal("0.01")),
                low_52w=low_52w.quantize(Decimal("0.01")),
                last_updated=datetime.utcnow(),
                data_source=DataSourceEnum.YAHOO_FINANCE,
            )

        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to parse {symbol} response: {e}")
            return None

    async def fetch_stock(self, symbol: str) -> Optional[Stock]:
        """
        Fetch individual stock data from Yahoo Finance.
        
        Args:
            symbol: Stock symbol (e.g., "AAPL")
            
        Returns:
            Stock object or None if failed
            
        Raises:
            TimeoutError: If request times out
        """
        session = await self._get_session()
        
        url = f"{self.BASE_URL}/v10/finance/quoteSummary/{symbol.upper()}"
        params = {
            "modules": "price,summaryDetail,assetProfile",
        }
        
        headers = {
            "User-Agent": self._get_random_user_agent(),
        }

        try:
            async with session.get(
                url,
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.TIMEOUT),
            ) as response:
                if response.status != 200:
                    logger.error(f"Yahoo Finance API error for {symbol}: {response.status}")
                    raise APIError(
                        error_code="E003_API_ERROR",
                        message=f"Yahoo Finance 返回錯誤狀態碼：{response.status}"
                    )

                data = await response.json()
                return self._parse_stock_response(symbol, data)

        except asyncio.TimeoutError:
            logger.error(f"Yahoo Finance timeout for {symbol}")
            raise TimeoutError(
                error_code="E001_TIMEOUT",
                message="Yahoo Finance API 響應超時（5 秒內無回應）"
            )
        except aiohttp.ClientError as e:
            logger.error(f"Yahoo Finance connection error for {symbol}: {e}")
            raise APIError(
                error_code="E003_API_ERROR",
                message=f"無法連接 Yahoo Finance：{str(e)}"
            )

    def _parse_stock_response(
        self, symbol: str, data: dict
    ) -> Optional[Stock]:
        """
        Parse Yahoo Finance stock response.
        
        Args:
            symbol: Stock symbol
            data: JSON response from Yahoo Finance
            
        Returns:
            Stock object or None if parsing fails
        """
        try:
            if "quoteSummary" not in data or "result" not in data["quoteSummary"]:
                logger.error(f"Unexpected response structure for {symbol}")
                return None

            result = data["quoteSummary"]["result"][0]
            price_data = result.get("price", {})
            detail_data = result.get("summaryDetail", {})
            asset_data = result.get("assetProfile", {})

            # Extract required fields
            current_price = Decimal(str(price_data.get("regularMarketPrice", {}).get("raw", 0)))
            previous_close = Decimal(str(price_data.get("regularMarketPreviousClose", {}).get("raw", 0)))

            if current_price == 0 or previous_close == 0:
                logger.warning(f"Invalid price data for {symbol}")
                return None

            change_amount = current_price - previous_close
            change_percent = (change_amount / previous_close * 100) if previous_close > 0 else Decimal("0")

            # Extract optional fields
            market_cap = detail_data.get("marketCap", {}).get("raw")
            market_cap_billion = Decimal(str(market_cap / 1_000_000_000)) if market_cap else None

            pe_ratio = detail_data.get("trailingPE", {}).get("raw")
            pe_ratio_decimal = Decimal(str(pe_ratio)) if pe_ratio else None

            dividend_yield = detail_data.get("dividendYield", {}).get("raw")
            dividend_yield_decimal = Decimal(str(dividend_yield * 100)) if dividend_yield else None

            # Extract price range
            open_price = price_data.get("regularMarketOpen", {}).get("raw")
            open_price_decimal = Decimal(str(open_price)) if open_price else None
            
            high_price = price_data.get("regularMarketDayHigh", {}).get("raw")
            high_price_decimal = Decimal(str(high_price)) if high_price else None
            
            low_price = price_data.get("regularMarketDayLow", {}).get("raw")
            low_price_decimal = Decimal(str(low_price)) if low_price else None

            company_name = asset_data.get("longName", symbol)
            sector = asset_data.get("sector")
            industry = asset_data.get("industry")

            # Get Chinese name from mapping
            from src.integrations.alpha_vantage import STOCK_NAMES
            stock_info = STOCK_NAMES.get(symbol.upper(), {"name": company_name, "zh_name": None})
            zh_name = stock_info.get("zh_name")

            return Stock(
                code=symbol.upper(),
                company_name=company_name,
                zh_name=zh_name,
                current_price=current_price.quantize(Decimal("0.01")),
                previous_close=previous_close.quantize(Decimal("0.01")),
                change_amount=change_amount.quantize(Decimal("0.01")),
                change_percent=change_percent.quantize(Decimal("0.01")),
                open_price=open_price_decimal.quantize(Decimal("0.01")) if open_price_decimal else None,
                high_price=high_price_decimal.quantize(Decimal("0.01")) if high_price_decimal else None,
                low_price=low_price_decimal.quantize(Decimal("0.01")) if low_price_decimal else None,
                market_cap_billion=market_cap_billion.quantize(Decimal("0.1")) if market_cap_billion else None,
                pe_ratio=pe_ratio_decimal.quantize(Decimal("0.01")) if pe_ratio_decimal else None,
                dividend_yield=dividend_yield_decimal.quantize(Decimal("0.01")) if dividend_yield_decimal else None,
                sector=sector,
                industry=industry,
                last_updated=datetime.utcnow(),
                data_source=DataSourceEnum.YAHOO_FINANCE,
            )

        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to parse {symbol} response: {e}")
            return None
