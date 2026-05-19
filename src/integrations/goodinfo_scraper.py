"""
Taiwan stock fundamental data integration using web scraping.
Fetches real-time P/E ratio, EPS, dividend yield from GOODINFO Taiwan.

GOODINFO (https://goodinfo.tw) provides the most comprehensive Taiwan stock data including:
- P/E ratio (本益比)
- EPS (每股盈餘)
- Dividend yield (股息殖利率)
- Payout ratio (配息率)
- ROE (股東權益報酬率)
"""

import aiohttp
import asyncio
from typing import Optional, Dict
from decimal import Decimal
from datetime import datetime
import re

from src.utils.logger import get_logger

logger = get_logger(__name__)


class GOODINFOScraper:
    """
    Web scraper for GOODINFO Taiwan stock data.
    
    GOODINFO is the most comprehensive Taiwan stock information source.
    This scraper extracts fundamental data without hardcoding.
    """

    BASE_URL = "https://goodinfo.tw/StockInfo"
    TIMEOUT = 10.0
    
    # GOODINFO uses different pages for different data
    PAGES = {
        "performance": "StockBzPerformance.asp",  # P/E, EPS, dividend
        "dividend": "StockDividendPolicy.asp",    # Dividend history
        "finance": "FinanceStatement.asp",        # Financial statements
    }

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create session"""
        if self.session is None:
            # GOODINFO requires a user-agent
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session

    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()

    async def fetch_fundamentals(self, stock_code: str) -> Optional[Dict]:
        """
        Fetch stock fundamental data from GOODINFO.
        
        Args:
            stock_code: Taiwan stock code (e.g., "2330")
            
        Returns:
            Dict with keys:
            - 'pe_ratio': Current P/E ratio (float)
            - 'eps': Earnings per share (float)
            - 'dividend_yield': Dividend yield % (float)
            - 'payout_ratio': Payout ratio % (float)
            - 'roe': Return on equity % (float)
            
        Returns None if fetch fails.
        """
        try:
            session = await self._get_session()
            
            # GOODINFO stock performance page
            url = f"{self.BASE_URL}/{self.PAGES['performance']}"
            params = {"STOCK_ID": stock_code}
            
            # GOODINFO blocks many requests, so we need to be careful
            async with session.get(
                url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=self.TIMEOUT),
                ssl=False  # Some HTTPS issues with GOODINFO
            ) as response:
                if response.status != 200:
                    logger.warning(f"GOODINFO returned {response.status} for {stock_code}")
                    return None

                html = await response.text()
                return self._parse_fundamentals(html, stock_code)

        except asyncio.TimeoutError:
            logger.warning(f"GOODINFO timeout for {stock_code}")
            return None
        except aiohttp.ClientError as e:
            logger.warning(f"GOODINFO connection error for {stock_code}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching GOODINFO for {stock_code}: {e}")
            return None

    def _parse_fundamentals(self, html: str, stock_code: str) -> Optional[Dict]:
        """
        Parse HTML from GOODINFO to extract fundamental data.
        
        Looks for specific patterns in the HTML table structure.
        """
        try:
            result = {}
            
            # Extract P/E ratio - look for "本益比" or "P/E Ratio"
            pe_match = re.search(r'本益比[：:]\s*([0-9.]+)', html)
            if pe_match:
                try:
                    result['pe_ratio'] = float(pe_match.group(1))
                except (ValueError, TypeError):
                    pass

            # Extract EPS - look for "每股盈餘"
            eps_match = re.search(r'每股盈餘[：:]\s*([0-9.]+)', html)
            if eps_match:
                try:
                    result['eps'] = float(eps_match.group(1))
                except (ValueError, TypeError):
                    pass

            # Extract dividend yield - look for "股息殖利率"
            div_match = re.search(r'股息殖利率[：:]\s*([0-9.]+)\s*%', html)
            if div_match:
                try:
                    result['dividend_yield'] = float(div_match.group(1))
                except (ValueError, TypeError):
                    pass

            # Extract payout ratio - look for "配息率"
            payout_match = re.search(r'配息率[：:]\s*([0-9.]+)\s*%', html)
            if payout_match:
                try:
                    result['payout_ratio'] = float(payout_match.group(1))
                except (ValueError, TypeError):
                    pass

            # Extract ROE - look for "股東權益報酬率"
            roe_match = re.search(r'股東權益報酬率[：:]\s*([0-9.]+)\s*%', html)
            if roe_match:
                try:
                    result['roe'] = float(roe_match.group(1))
                except (ValueError, TypeError):
                    pass

            logger.info(f"Parsed GOODINFO for {stock_code}: {len(result)} fields")
            return result if result else None

        except Exception as e:
            logger.error(f"Error parsing GOODINFO HTML for {stock_code}: {e}")
            return None


class TaiwanStockFundamentalsService:
    """
    Service for fetching Taiwan stock fundamental data.
    Tries multiple sources: GOODINFO first, then fallback strategies.
    """

    def __init__(self):
        self.goodinfo_scraper = GOODINFOScraper()
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        """Close all sessions"""
        await self.goodinfo_scraper.close()
        if self.session:
            await self.session.close()

    async def get_fundamentals(self, stock_code: str) -> Optional[Dict]:
        """
        Get Taiwan stock fundamental data from available sources.
        
        Sources tried in order:
        1. GOODINFO Taiwan (most complete)
        2. Yahoo Finance Taiwan (fallback)
        3. Return None if all sources fail
        
        Args:
            stock_code: Taiwan stock code (e.g., "2330")
            
        Returns:
            Dict with fundamental data, or None if unable to fetch
        """
        # Try GOODINFO first (most comprehensive)
        try:
            fundamentals = await self.goodinfo_scraper.fetch_fundamentals(stock_code)
            if fundamentals:
                logger.info(f"Fetched Taiwan fundamentals from GOODINFO for {stock_code}")
                return fundamentals
        except Exception as e:
            logger.warning(f"GOODINFO fetch failed for {stock_code}: {e}")

        # Try Yahoo Finance Taiwan as fallback
        try:
            fundamentals = await self._fetch_from_yahoo_tw(stock_code)
            if fundamentals:
                logger.info(f"Fetched Taiwan fundamentals from Yahoo Finance for {stock_code}")
                return fundamentals
        except Exception as e:
            logger.warning(f"Yahoo Finance Taiwan fetch failed for {stock_code}: {e}")

        logger.warning(f"No Taiwan fundamentals found for {stock_code}")
        return None

    async def _fetch_from_yahoo_tw(self, stock_code: str) -> Optional[Dict]:
        """
        Fetch Taiwan stock data from Yahoo Finance Taiwan.
        
        Note: Yahoo Finance Taiwan may not have all fundamental data.
        Primarily used as fallback when GOODINFO fails.
        """
        try:
            session = await self._get_session()
            
            # Yahoo Finance Taiwan format: stock_code.TW
            symbol = f"{stock_code}.TW"
            url = f"https://tw.finance.yahoo.com/quote/{symbol}"
            
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=8),
            ) as response:
                if response.status != 200:
                    return None

                html = await response.text()
                
                # Extract P/E ratio from Yahoo Taiwan page
                pe_match = re.search(r'本益比[：:]\s*([0-9.]+)', html)
                if pe_match:
                    return {
                        'pe_ratio': float(pe_match.group(1))
                    }
                
                return None

        except Exception as e:
            logger.warning(f"Yahoo Finance Taiwan error for {stock_code}: {e}")
            return None


# Global instance for reuse
_tw_fundamentals_service: Optional[TaiwanStockFundamentalsService] = None


async def get_taiwan_fundamentals_service() -> TaiwanStockFundamentalsService:
    """Get or create Taiwan fundamentals service"""
    global _tw_fundamentals_service
    if _tw_fundamentals_service is None:
        _tw_fundamentals_service = TaiwanStockFundamentalsService()
    return _tw_fundamentals_service
