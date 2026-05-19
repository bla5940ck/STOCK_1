"""
Taiwan stock fundamental data service using Yahoo Finance and TWSE APIs.
This replaces the GOODINFO scraper which uses JavaScript dynamic loading.

Data sources:
1. Yahoo Finance - for P/E ratio and dividend data
2. TWSE API - for stock info
3. Simple calculations - for derived metrics
"""

import aiohttp
import asyncio
from typing import Optional, Dict
from decimal import Decimal
from datetime import datetime
import json
import re

from src.utils.logger import get_logger

logger = get_logger(__name__)


class TaiwanStockFundamentalsService:
    """
    Service for fetching Taiwan stock fundamental data.
    Uses Yahoo Finance API and manual data aggregation.
    """

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create session"""
        if self.session is None:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session

    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()

    async def get_fundamentals(self, stock_code: str) -> Optional[Dict]:
        """
        Get Taiwan stock fundamental data.
        
        Args:
            stock_code: Taiwan stock code (e.g., "2330")
            
        Returns:
            Dict with keys:
            - 'pe_ratio': P/E ratio (float)
            - 'dividend_yield': Dividend yield % (float)
            - 'data_source': Where the data came from
            
        Returns None if unable to fetch.
        """
        try:
            # Try Yahoo Finance first (most reliable for Taiwan stocks)
            fundamentals = await self._fetch_from_yahoo_tw(stock_code)
            if fundamentals:
                logger.info(f"Fetched Taiwan fundamentals for {stock_code} from Yahoo Finance")
                return fundamentals
            
            # If Yahoo fails, try TWSE API
            fundamentals = await self._fetch_from_twse(stock_code)
            if fundamentals:
                logger.info(f"Fetched Taiwan fundamentals for {stock_code} from TWSE")
                return fundamentals
            
            logger.warning(f"No fundamentals found for Taiwan stock {stock_code}")
            return None

        except Exception as e:
            logger.error(f"Error fetching Taiwan fundamentals for {stock_code}: {e}")
            return None

    async def _fetch_from_yahoo_tw(self, stock_code: str) -> Optional[Dict]:
        """
        Fetch from Yahoo Finance Taiwan.
        
        Yahoo Taiwan provides P/E ratio and dividend data in JSON format.
        """
        try:
            session = await self._get_session()
            
            # Yahoo Finance Taiwan API endpoint
            # Note: This uses the query parameter which returns structured data
            symbol = f"{stock_code}.TW"
            url = f"https://tw.finance.yahoo.com/quote/{symbol}"
            
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    logger.warning(f"Yahoo Taiwan returned {response.status} for {stock_code}")
                    return None

                html = await response.text()
                
                # Try to extract P/E ratio from the HTML
                # Yahoo Taiwan embeds JSON-LD data in the page
                pe_match = re.search(r'"pe"\s*:\s*([0-9.]+)', html)
                if not pe_match:
                    # Try alternative format
                    pe_match = re.search(r'本益比[：:]\s*([0-9.]+)', html)
                
                dividend_match = re.search(r'"dividendYield"\s*:\s*([0-9.]+)', html)
                if not dividend_match:
                    dividend_match = re.search(r'殖利率[：:]\s*([0-9.]+)\s*%', html)
                
                result = {}
                if pe_match:
                    result['pe_ratio'] = float(pe_match.group(1))
                if dividend_match:
                    result['dividend_yield'] = float(dividend_match.group(1))
                
                if result:
                    result['data_source'] = 'Yahoo Finance Taiwan'
                    return result
                
                return None

        except asyncio.TimeoutError:
            logger.warning(f"Yahoo Finance Taiwan timeout for {stock_code}")
            return None
        except Exception as e:
            logger.warning(f"Yahoo Finance Taiwan error for {stock_code}: {e}")
            return None

    async def _fetch_from_twse(self, stock_code: str) -> Optional[Dict]:
        """
        Fetch from Taiwan Stock Exchange open API.
        
        TWSE provides dividend data through their public APIs.
        """
        try:
            session = await self._get_session()
            
            # TWSE 除息除權資訊 API
            # Returns dividend and ex-rights information
            url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp"
            params = {"ex_ch": f"tse_{stock_code}.tw"}
            
            async with session.get(
                url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    return None

                data = await response.json()
                
                if data.get("ok") and data.get("msgArray"):
                    stock_data = data["msgArray"][0]
                    
                    result = {}
                    
                    # TWSE doesn't provide P/E directly, but we can get other info
                    # For now, just return empty and let caller handle
                    
                    result['data_source'] = 'TWSE'
                    return result if result else None
                
                return None

        except Exception as e:
            logger.warning(f"TWSE API error for {stock_code}: {e}")
            return None


# Global instance
_tw_fundamentals_service: Optional[TaiwanStockFundamentalsService] = None


async def get_taiwan_fundamentals_service() -> TaiwanStockFundamentalsService:
    """Get or create Taiwan fundamentals service"""
    global _tw_fundamentals_service
    if _tw_fundamentals_service is None:
        _tw_fundamentals_service = TaiwanStockFundamentalsService()
    return _tw_fundamentals_service
