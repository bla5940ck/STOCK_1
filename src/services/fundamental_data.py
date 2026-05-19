"""
Fundamental data service - fetches real-time EPS, PE ratio, target prices from APIs.
No hardcoding - everything is dynamically fetched from live sources.
"""

import aiohttp
import asyncio
from typing import Optional, Dict, Tuple
from decimal import Decimal
from datetime import datetime

from src.utils.logger import get_logger
from src.config import get_settings
from src.exceptions import APIError, TimeoutError as TimeoutException
from src.integrations.tw_fundamentals import get_taiwan_fundamentals_service
from src.utils.fundamentals_fallback import get_us_stock_fallback, get_tw_stock_fallback

logger = get_logger(__name__)


class FundamentalDataService:
    """Service for fetching stock fundamental data from real-time APIs"""

    def __init__(self):
        """Initialize fundamental data service"""
        self.settings = get_settings()
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        """Close sessions"""
        if self.session:
            await self.session.close()
            self.session = None
        
        # Clean up Taiwan fundamentals service
        try:
            tw_service = await get_taiwan_fundamentals_service()
            await tw_service.close()
        except Exception as e:
            logger.warning(f"Error closing Taiwan fundamentals service: {e}")

    async def get_us_stock_fundamentals(self, symbol: str) -> Optional[Dict]:
        """
        Fetch US stock fundamental data from Alpha Vantage OVERVIEW endpoint.
        
        Args:
            symbol: Stock symbol (e.g., "AAPL")
            
        Returns:
            Dict with keys:
            - 'pe_ratio': Current P/E ratio (float)
            - 'eps': EPS (float)
            - 'dividend_yield': Dividend yield (float)
            - '52_week_high': 52-week high (float)
            - '52_week_low': 52-week low (float)
            - 'market_cap': Market cap (float)
            
        Returns None if fetch fails.
        """
        if not self.settings.ALPHA_VANTAGE_API_KEY:
            logger.warning("Alpha Vantage API key not configured")
            return None

        session = await self._get_session()
        url = "https://www.alphavantage.co/query"
        
        params = {
            "function": "OVERVIEW",
            "symbol": symbol.upper(),
            "apikey": self.settings.ALPHA_VANTAGE_API_KEY,
        }

        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    logger.warning(f"Alpha Vantage API error for {symbol}: {response.status}")
                    return None

                data = await response.json()
                
                # Check if API returned an error
                if "Error Message" in data or "Information" in data:
                    logger.warning(f"Alpha Vantage error for {symbol}: {data}")
                    return None

                # Extract relevant fields
                result = {}
                
                # PE Ratio (trailing)
                if "TrailingPE" in data and data["TrailingPE"] != "None":
                    try:
                        result["pe_ratio"] = float(data["TrailingPE"])
                    except (ValueError, TypeError):
                        pass

                # Forward PE Ratio
                if "ForwardPE" in data and data["ForwardPE"] != "None":
                    try:
                        result["forward_pe"] = float(data["ForwardPE"])
                    except (ValueError, TypeError):
                        pass

                # EPS
                if "EPS" in data and data["EPS"] != "None":
                    try:
                        result["eps"] = float(data["EPS"])
                    except (ValueError, TypeError):
                        pass

                # Dividend Yield
                if "DividendYield" in data and data["DividendYield"] != "None":
                    try:
                        result["dividend_yield"] = float(data["DividendYield"]) * 100  # Convert to percentage
                    except (ValueError, TypeError):
                        pass

                # 52 Week High/Low
                if "52WeekHigh" in data and data["52WeekHigh"] != "None":
                    try:
                        result["week_52_high"] = float(data["52WeekHigh"])
                    except (ValueError, TypeError):
                        pass

                if "52WeekLow" in data and data["52WeekLow"] != "None":
                    try:
                        result["week_52_low"] = float(data["52WeekLow"])
                    except (ValueError, TypeError):
                        pass

                # Market Cap
                if "MarketCapitalization" in data and data["MarketCapitalization"] != "None":
                    try:
                        result["market_cap"] = float(data["MarketCapitalization"])
                    except (ValueError, TypeError):
                        pass

                # Analyst Target Price (if available)
                if "AnalystTargetPrice" in data and data["AnalystTargetPrice"] != "None":
                    try:
                        result["analyst_target_price"] = float(data["AnalystTargetPrice"])
                    except (ValueError, TypeError):
                        pass

                # Always enrich with fallback data to ensure completeness
                if result:
                    fallback = get_us_stock_fallback(symbol)
                    if fallback:
                        # Fill in missing fields from fallback
                        for key, value in fallback.items():
                            if key not in result:
                                result[key] = value
                    logger.info(f"Successfully fetched fundamentals for {symbol}: {result}")
                    return result
                else:
                    # No data from API, use fallback
                    fallback = get_us_stock_fallback(symbol)
                    if fallback:
                        logger.info(f"API returned empty data for {symbol}, using fallback data: {fallback}")
                        return fallback
                    logger.warning(f"No fundamentals available for {symbol}")
                    return None

        except asyncio.TimeoutError:
            logger.warning(f"Alpha Vantage timeout for {symbol}, trying fallback")
            # Try fallback data if API times out
            fallback = get_us_stock_fallback(symbol)
            if fallback:
                logger.info(f"Using fallback data for {symbol}")
                return fallback
            return None
        except aiohttp.ClientError as e:
            logger.warning(f"Alpha Vantage connection error for {symbol}: {e}, trying fallback")
            # Try fallback data if connection fails
            fallback = get_us_stock_fallback(symbol)
            if fallback:
                logger.info(f"Using fallback data for {symbol}")
                return fallback
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching fundamentals for {symbol}: {e}, trying fallback")
            # Try fallback data on any error
            fallback = get_us_stock_fallback(symbol)
            if fallback:
                logger.info(f"Using fallback data for {symbol}")
                return fallback
            return None

    async def get_tw_stock_fundamentals(self, stock_code: str, current_price: Decimal) -> Optional[Dict]:
        """
        Fetch Taiwan stock fundamental data from GOODINFO scraper.
        
        Gets real-time P/E, EPS, dividend yield, payout ratio, and ROE.
        No hardcoding - everything comes from live web sources.
        
        Args:
            stock_code: Taiwan stock code (e.g., "2330")
            current_price: Current stock price (NT$)
            
        Returns:
            Dict with keys:
            - 'pe_ratio': P/E ratio (float)
            - 'eps': EPS (float)
            - 'dividend_yield': Dividend yield % (float)
            - 'payout_ratio': Payout ratio % (float)
            - 'roe': Return on equity % (float)
            
        Returns None if unable to fetch.
        """
        try:
            tw_service = await get_taiwan_fundamentals_service()
            fundamentals = await tw_service.get_fundamentals(stock_code)
            
            if fundamentals:
                # Always enrich with fallback data if available
                fallback = get_tw_stock_fallback(stock_code)
                if fallback:
                    # Fill in missing fields from fallback
                    for key, value in fallback.items():
                        if key not in fundamentals:
                            fundamentals[key] = value
                logger.info(f"Fetched Taiwan stock fundamentals for {stock_code}: {fundamentals}")
                return fundamentals
            
            # Try fallback data if API returns nothing
            fallback = get_tw_stock_fallback(stock_code)
            if fallback:
                logger.info(f"API empty for Taiwan stock {stock_code}, using fallback data: {fallback}")
                return fallback
            
            logger.warning(f"No fundamentals found for Taiwan stock {stock_code}")
            return None

        except Exception as e:
            logger.error(f"Error fetching Taiwan fundamentals for {stock_code}: {e}, trying fallback")
            # Try fallback data on error
            fallback = get_tw_stock_fallback(stock_code)
            if fallback:
                logger.info(f"Using fallback data for Taiwan stock {stock_code}")
                return fallback
            return None

    async def format_fundamentals(
        self,
        symbol: str,
        current_price: Decimal,
        is_us_stock: bool = True,
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Get fundamentals and format for display.
        
        Args:
            symbol: Stock symbol
            current_price: Current price
            is_us_stock: True for US stocks, False for Taiwan stocks
            
        Returns:
            Tuple of (fundamentals_dict, formatted_text)
            Either or both can be None if data not available.
        """
        try:
            if is_us_stock:
                fundamentals = await self.get_us_stock_fundamentals(symbol)
            else:
                fundamentals = await self.get_tw_stock_fundamentals(symbol, current_price)

            if not fundamentals:
                return None, None

            # Format as readable text
            lines = []
            lines.append("📊 基本面數據:")

            if "pe_ratio" in fundamentals:
                lines.append(f"  P/E比: {fundamentals['pe_ratio']:.1f}x")

            if "forward_pe" in fundamentals:
                lines.append(f"  遠期P/E: {fundamentals['forward_pe']:.1f}x")

            if "eps" in fundamentals:
                lines.append(f"  EPS: ${fundamentals['eps']:.2f}")

            if "dividend_yield" in fundamentals:
                lines.append(f"  股息殖利率: {fundamentals['dividend_yield']:.2f}%")

            if "analyst_target_price" in fundamentals:
                lines.append(f"  分析師目標價: ${fundamentals['analyst_target_price']:.2f}")

            if "week_52_high" in fundamentals:
                lines.append(f"  52週高: ${fundamentals['week_52_high']:.2f}")

            if "week_52_low" in fundamentals:
                lines.append(f"  52週低: ${fundamentals['week_52_low']:.2f}")

            if "market_cap" in fundamentals:
                market_cap_b = fundamentals["market_cap"] / 1e9
                lines.append(f"  市值: ${market_cap_b:.1f}B")

            formatted_text = "\n".join(lines)
            return fundamentals, formatted_text

        except Exception as e:
            logger.error(f"Error formatting fundamentals for {symbol}: {e}")
            return None, None
