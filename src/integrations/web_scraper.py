"""
Web scraper for fetching market data directly from websites.
"""

import asyncio
import aiohttp
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict
import logging

from src.models.domain import Index, DataSourceEnum
from src.exceptions import APIError

logger = logging.getLogger(__name__)


class WebScraper:
    """Scrape market data from public websites"""
    
    # Yahoo Finance quote endpoint (returns JSON)
    YAHOO_FINANCE_URL = "https://query1.finance.yahoo.com/v10/finance/quoteSummary"
    
    # Alternative: Investing.com (returns HTML)
    INVESTING_COM_URLS = {
        "^GSPC": "https://www.investing.com/indices/us-spx-500",
        "^IXIC": "https://www.investing.com/indices/nasdaq-composite",
        "^SOX": "https://www.investing.com/indices/philadelphia-semiconductor",
    }
    
    TIMEOUT = 10.0  # 10 second timeout
    
    def __init__(self):
        """Initialize web scraper"""
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def fetch_index(self, symbol: str) -> Optional[Index]:
        """
        Fetch index data by scraping Yahoo Finance.
        
        Args:
            symbol: Index symbol (e.g., "^GSPC")
            
        Returns:
            Index object or None if failed
        """
        try:
            session = await self._get_session()
            
            # Try Yahoo Finance API endpoint first (returns JSON)
            url = f"{self.YAHOO_FINANCE_URL}/{symbol}"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            params = {
                "modules": "price",
            }
            
            logger.info(f"Fetching {symbol} from Yahoo Finance...")
            
            async with session.get(
                url,
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.TIMEOUT),
            ) as response:
                if response.status != 200:
                    logger.warning(f"Yahoo Finance returned {response.status} for {symbol}")
                    return None
                
                data = await response.json()
                
                # Parse response
                try:
                    price_data = data.get("quoteSummary", {}).get("result", [{}])[0].get("price", {})
                    
                    if not price_data:
                        logger.warning(f"No price data for {symbol}")
                        return None
                    
                    current_price = Decimal(str(price_data.get("regularMarketPrice", {}).get("raw", 0)))
                    previous_close = Decimal(str(price_data.get("regularMarketPreviousClose", {}).get("raw", 0)))
                    
                    if current_price <= 0 or previous_close <= 0:
                        logger.warning(f"Invalid price data for {symbol}: current={current_price}, prev={previous_close}")
                        return None
                    
                    change_amount = current_price - previous_close
                    change_percent = (change_amount / previous_close * 100) if previous_close > 0 else Decimal("0")
                    
                    # Map symbol to Chinese name
                    symbol_names = {
                        "^GSPC": "S&P 500",
                        "^IXIC": "納斯達克綜合指數",
                        "^SOX": "費城半導體指數",
                    }
                    
                    index = Index(
                        id=symbol,
                        code=symbol,
                        zh_name=symbol_names.get(symbol, symbol),
                        current_price=current_price.quantize(Decimal("0.01")),
                        previous_close=previous_close.quantize(Decimal("0.01")),
                        change_amount=change_amount.quantize(Decimal("0.01")),
                        change_percent=change_percent.quantize(Decimal("0.01")),
                        high_52w=Decimal(str(price_data.get("fiftyTwoWeekHigh", {}).get("raw", 0))).quantize(Decimal("0.01")),
                        low_52w=Decimal(str(price_data.get("fiftyTwoWeekLow", {}).get("raw", 0))).quantize(Decimal("0.01")),
                        last_updated=datetime.utcnow(),
                        data_source=DataSourceEnum.YAHOO_FINANCE,
                    )
                    
                    logger.info(f"✅ Scraped {symbol}: {current_price} (change: {change_percent}%)")
                    return index
                    
                except (KeyError, ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse response for {symbol}: {e}")
                    return None
        
        except asyncio.TimeoutError:
            logger.warning(f"Timeout scraping {symbol}")
            return None
        except aiohttp.ClientError as e:
            logger.warning(f"Network error scraping {symbol}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error scraping {symbol}: {e}")
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
                
                # Rate limiting: 1 second delay between requests
                if symbol != symbols[-1]:  # Don't sleep after last call
                    await asyncio.sleep(1.0)
                    
            except Exception as e:
                logger.warning(f"Failed to fetch {symbol}: {e}")
                continue
        
        return results
