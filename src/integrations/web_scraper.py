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
