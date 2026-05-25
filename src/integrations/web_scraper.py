"""
Web scraper for fetching market data directly from websites.
"""

import asyncio
import aiohttp
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict
import logging
import re

from src.models.domain import Index, DataSourceEnum
from src.exceptions import APIError

logger = logging.getLogger(__name__)


class WebScraper:
    """Scrape market data from public websites"""
    
    # Yahoo Taiwan markets page with US indices
    YAHOO_TW_MARKETS_URL = "https://tw.stock.yahoo.com/markets"
    
    # Symbol mapping for finding data on the page
    # These are common ways indices are labeled on financial websites
    INDEX_NAMES = {
        "^GSPC": ["S&P 500", "SP500", "美股", "標普500"],
        "^IXIC": ["NASDAQ", "納斯達克", "IXIC"],
        "^SOX": ["費城半導體", "SOX", "Philadelphia"],
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
    
    async def fetch_from_yahoo_tw(self) -> Dict[str, Index]:
        """
        Fetch US market indices from Yahoo Taiwan markets page.
        
        Returns:
            Dict mapping symbol to Index object
        """
        try:
            logger.info(f"Fetching indices from {self.YAHOO_TW_MARKETS_URL}...")
            
            session = await self._get_session()
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            async with session.get(
                self.YAHOO_TW_MARKETS_URL,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.TIMEOUT),
            ) as response:
                if response.status != 200:
                    logger.warning(f"Yahoo Taiwan returned {response.status}")
                    return {}
                
                html = await response.text()
                return self._parse_yahoo_tw_markets(html)
        
        except Exception as e:
            logger.warning(f"Error fetching from Yahoo Taiwan: {e}")
            return {}
    
    def _parse_yahoo_tw_markets(self, html: str) -> Dict[str, Index]:
        """
        Parse HTML from Yahoo Taiwan markets page to extract US indices.
        
        Args:
            html: HTML content from the page
            
        Returns:
            Dict mapping symbol to Index object
        """
        results = {}
        
        try:
            # Try to find patterns for each index
            # Look for patterns like "S&P 500 5650.75 +25.25 (+0.45%)"
            
            patterns = {
                "^GSPC": [
                    r"S&P\s*500[^0-9]*([0-9,]+\.?[0-9]*)[^0-9]*([+-]?[0-9,]+\.?[0-9]*)[^0-9]*([+-]?[0-9\.]+%)",
                    r"標普\s*500[^0-9]*([0-9,]+\.?[0-9]*)[^0-9]*([+-]?[0-9,]+\.?[0-9]*)[^0-9]*([+-]?[0-9\.]+%)",
                    r"SP500[^0-9]*([0-9,]+\.?[0-9]*)[^0-9]*([+-]?[0-9,]+\.?[0-9]*)[^0-9]*([+-]?[0-9\.]+%)",
                ],
                "^IXIC": [
                    r"NASDAQ[^0-9]*([0-9,]+\.?[0-9]*)[^0-9]*([+-]?[0-9,]+\.?[0-9]*)[^0-9]*([+-]?[0-9\.]+%)",
                    r"納斯達克[^0-9]*([0-9,]+\.?[0-9]*)[^0-9]*([+-]?[0-9,]+\.?[0-9]*)[^0-9]*([+-]?[0-9\.]+%)",
                    r"IXIC[^0-9]*([0-9,]+\.?[0-9]*)[^0-9]*([+-]?[0-9,]+\.?[0-9]*)[^0-9]*([+-]?[0-9\.]+%)",
                ],
                "^SOX": [
                    r"費城半導體[^0-9]*([0-9,]+\.?[0-9]*)[^0-9]*([+-]?[0-9,]+\.?[0-9]*)[^0-9]*([+-]?[0-9\.]+%)",
                    r"SOX[^0-9]*([0-9,]+\.?[0-9]*)[^0-9]*([+-]?[0-9,]+\.?[0-9]*)[^0-9]*([+-]?[0-9\.]+%)",
                    r"Philadelphia[^0-9]*([0-9,]+\.?[0-9]*)[^0-9]*([+-]?[0-9,]+\.?[0-9]*)[^0-9]*([+-]?[0-9\.]+%)",
                ],
            }
            
            symbol_names = {
                "^GSPC": "S&P 500",
                "^IXIC": "納斯達克綜合指數",
                "^SOX": "費城半導體指數",
            }
            
            for symbol, pattern_list in patterns.items():
                for pattern in pattern_list:
                    match = re.search(pattern, html, re.IGNORECASE)
                    if match:
                        try:
                            current_price = Decimal(match.group(1).replace(",", ""))
                            change_amount = Decimal(match.group(2).replace(",", ""))
                            change_percent_str = match.group(3).replace("%", "").replace("+", "")
                            change_percent = Decimal(change_percent_str)
                            
                            # Calculate previous close from current price and change percent
                            if change_percent != 0:
                                previous_close = current_price - change_amount
                            else:
                                previous_close = current_price
                            
                            if current_price > 0 and previous_close > 0:
                                index = Index(
                                    id=symbol,
                                    code=symbol,
                                    zh_name=symbol_names[symbol],
                                    current_price=current_price.quantize(Decimal("0.01")),
                                    previous_close=previous_close.quantize(Decimal("0.01")),
                                    change_amount=change_amount.quantize(Decimal("0.01")),
                                    change_percent=change_percent.quantize(Decimal("0.01")),
                                    high_52w=Decimal("0"),  # Not available from markets page
                                    low_52w=Decimal("0"),   # Not available from markets page
                                    last_updated=datetime.utcnow(),
                                    data_source=DataSourceEnum.YAHOO_FINANCE,
                                )
                                results[symbol] = index
                                logger.info(f"✅ Parsed {symbol} from Yahoo Taiwan: {current_price}")
                                break  # Found this symbol, move to next
                        except (ValueError, IndexError) as e:
                            logger.warning(f"Failed to parse {symbol}: {e}")
                            continue
            
            logger.info(f"Successfully parsed {len(results)} indices from Yahoo Taiwan")
            return results
        
        except Exception as e:
            logger.warning(f"Error parsing HTML: {e}")
            return {}

    
    async def fetch_index(self, symbol: str) -> Optional[Index]:
        """
        Fetch index data using yfinance via async executor.
        Simpler and more reliable than direct API calls.
        
        Args:
            symbol: Index symbol (e.g., "^GSPC")
            
        Returns:
            Index object or None if failed
        """
        try:
            logger.info(f"Fetching {symbol} from Yahoo Finance...")
            
            # Run yfinance in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            index = await loop.run_in_executor(
                None, 
                self._fetch_with_yfinance, 
                symbol
            )
            
            if index:
                logger.info(f"✅ Fetched {symbol}: {index.current_price}")
                return index
            else:
                logger.warning(f"No data returned for {symbol}")
                return None
                
        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching {symbol}")
            return None
        except Exception as e:
            logger.warning(f"Error fetching {symbol}: {e}")
            return None
    
    def _fetch_with_yfinance(self, symbol: str) -> Optional[Index]:
        """
        Synchronous function to fetch index data using yfinance.
        
        Args:
            symbol: Index symbol
            
        Returns:
            Index object or None
        """
        try:
            import yfinance as yf
            
            # Get ticker data
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")  # Get last 5 days to ensure we have data
            
            if hist is None or len(hist) == 0:
                logger.warning(f"No historical data for {symbol}")
                return None
            
            # Get latest and previous data
            latest = hist.iloc[-1]
            previous = hist.iloc[-2] if len(hist) > 1 else latest
            
            current_price = Decimal(str(latest['Close']))
            previous_close = Decimal(str(previous['Close']))
            high_52w = Decimal(str(hist['High'].max()))
            low_52w = Decimal(str(hist['Low'].min()))
            
            if current_price <= 0 or previous_close <= 0:
                logger.warning(f"Invalid price for {symbol}: current={current_price}, prev={previous_close}")
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
                high_52w=high_52w.quantize(Decimal("0.01")),
                low_52w=low_52w.quantize(Decimal("0.01")),
                last_updated=datetime.utcnow(),
                data_source=DataSourceEnum.YAHOO_FINANCE,
            )
            
            return index
            
        except Exception as e:
            logger.warning(f"yfinance error for {symbol}: {e}")
            return None
    
    async def fetch_indices(self, symbols: list[str]) -> Dict[str, Index]:
        """
        Fetch multiple indices with rate limiting.
        
        Strategy:
        1. Try scraping from Yahoo Taiwan markets page (no API key needed)
        2. Fall back to yfinance if web scraping fails
        
        Args:
            symbols: List of index symbols
            
        Returns:
            Dict mapping symbol to Index object
        """
        # Step 1: Try Yahoo Taiwan markets page first
        try:
            logger.info("📄 Attempting to scrape from Yahoo Taiwan markets page...")
            results = await self.fetch_from_yahoo_tw()
            
            if results and len(results) >= 2:
                logger.info(f"✅ Successfully scraped {len(results)} indices from Yahoo Taiwan")
                return results
            else:
                logger.warning(f"Only got {len(results)} indices from Yahoo Taiwan, trying yfinance...")
        except Exception as e:
            logger.warning(f"Yahoo Taiwan scraping failed: {e}")
        
        # Step 2: Fall back to yfinance
        logger.info("📊 Falling back to yfinance...")
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
