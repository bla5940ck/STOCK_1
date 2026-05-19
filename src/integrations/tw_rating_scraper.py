"""
Taiwan stock fundamentals scraper using Yahoo Finance (yfinance).
Fetches analyst ratings, target prices, and quarterly EPS rankings.
No browser automation needed - uses yfinance REST API.
"""

import asyncio
import aiohttp
from typing import Optional, Dict, List
from datetime import datetime
from decimal import Decimal
import re
from html import unescape

from src.utils.logger import get_logger

logger = get_logger(__name__)


class TaiwanStockRatingScraper:
    """Fetch Taiwan stock analyst ratings and target prices via Yahoo Finance"""
    
    def __init__(self):
        pass
        
    async def get_analyst_ratings(self, stock_code: str) -> Optional[Dict]:
        """
        Get analyst ratings and target prices from Yahoo Finance.
        
        Args:
            stock_code: Taiwan stock code (e.g., "2330")
            
        Returns:
            Dict with keys:
            - 'buy_count': Number of buy ratings
            - 'hold_count': Number of hold ratings  
            - 'sell_count': Number of sell ratings
            - 'avg_target_price': Average analyst target price (TWD)
            - 'max_target_price': Highest target price (TWD)
            - 'min_target_price': Lowest target price (TWD)
            - 'rating_score': Overall rating score (0-10)
            
        Returns None if unable to fetch.
        """
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._fetch_yfinance_data, stock_code)
            return result
        except Exception as e:
            logger.error(f"Error fetching analyst data for {stock_code}: {e}")
            return None
    
    def _fetch_yfinance_data(self, stock_code: str) -> Optional[Dict]:
        """
        Fetch analyst data from Yahoo Finance synchronously.
        Called via run_in_executor to avoid blocking the event loop.
        """
        try:
            import yfinance as yf
            
            symbol = f"{stock_code}.TW"
            ticker = yf.Ticker(symbol)
            result = {}
            
            # Get analyst price targets from ticker.info
            try:
                info = ticker.info
                if info:
                    mean_price = info.get("targetMeanPrice")
                    high_price = info.get("targetHighPrice")
                    low_price  = info.get("targetLowPrice")
                    num_analysts = info.get("numberOfAnalystOpinions", 0)
                    rec_key = info.get("recommendationKey", "")  # e.g. 'buy', 'strong_buy', 'hold'
                    
                    if mean_price:
                        result["avg_target_price"] = float(mean_price)
                    if high_price:
                        result["max_target_price"] = float(high_price)
                    if low_price:
                        result["min_target_price"] = float(low_price)
                    if num_analysts:
                        result["num_analysts"] = int(num_analysts)
                    if rec_key:
                        result["recommendation_key"] = rec_key
            except Exception as e:
                logger.debug(f"Could not read ticker.info for {symbol}: {e}")
            
            # Get recommendations summary (buy/hold/sell counts)
            try:
                recs = ticker.recommendations_summary
                if recs is not None and not recs.empty:
                    latest = recs.iloc[0]
                    strong_buy  = int(latest.get("strongBuy",  0) or 0)
                    buy         = int(latest.get("buy",         0) or 0)
                    hold        = int(latest.get("hold",        0) or 0)
                    sell        = int(latest.get("sell",        0) or 0)
                    strong_sell = int(latest.get("strongSell",  0) or 0)
                    
                    result["buy_count"]  = strong_buy + buy
                    result["hold_count"] = hold
                    result["sell_count"] = sell + strong_sell
                    
                    total = result["buy_count"] + result["hold_count"] + result["sell_count"]
                    if total > 0:
                        buy_ratio = result["buy_count"] / total
                        result["rating_score"] = round(buy_ratio * 10, 1)
            except Exception as e:
                logger.debug(f"Could not read recommendations_summary for {symbol}: {e}")
            
            if result and ("avg_target_price" in result or "buy_count" in result):
                result["data_source"] = "Yahoo Finance"
                logger.info(f"Fetched analyst data for {symbol}: {result}")
                return result
            
            logger.warning(f"No analyst data available on Yahoo Finance for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"yfinance error for {stock_code}: {e}")
            return None

    # Legacy stubs (kept for interface compatibility)
    def _parse_cnyes_ratings(self, html: str, stock_code: str) -> Optional[Dict]:
        """Legacy method — no longer used"""
        return None

    def _extract_price(self, text: str) -> Optional[float]:
        """Legacy method — no longer used"""
        return None

    #     <TD>Price 1 (old target)</TD>
    #     <TD>Price 2 (new target)</TD>
    #     <TD>Current Price</TD>
    # </TR>


class TaiwanStockEPSRankingScraper:
    """Scrape Taiwan stock EPS rankings from WantGoo"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = "https://www.wantgoo.com/stock/ranking/most-recent-quarter-eps"
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def get_top_eps_stocks(self, limit: int = 20) -> Optional[List[Dict]]:
        """
        Get top Taiwan stocks by most recent quarter EPS.
        
        Args:
            limit: Number of top stocks to return (default 20)
            
        Returns:
            List of dicts with keys:
            - 'code': Stock code
            - 'name': Stock name  
            - 'latest_quarter_eps': Latest quarter EPS
            - 'yoy_growth': Year-over-year growth %
            - 'rank': Ranking position
            
        Returns None if unable to fetch.
        """
        session = await self._get_session()
        
        try:
            async with session.get(
                self.base_url,
                timeout=aiohttp.ClientTimeout(total=15),
                headers={"User-Agent": "Mozilla/5.0"}
            ) as response:
                if response.status != 200:
                    logger.warning(f"WantGoo EPS ranking API error: {response.status}")
                    return None
                
                html = await response.text()
                
                # Parse HTML to extract EPS ranking data
                result = self._parse_wantgoo_eps(html, limit)
                
                if result:
                    logger.info(f"Fetched {len(result)} top EPS stocks from WantGoo")
                    return result
                else:
                    logger.warning("Could not parse WantGoo EPS ranking")
                    return None
                    
        except asyncio.TimeoutError:
            logger.warning("WantGoo EPS ranking timeout")
            return None
        except Exception as e:
            logger.error(f"Error fetching WantGoo EPS ranking: {e}")
            return None
    
    def _parse_wantgoo_eps(self, html: str, limit: int) -> Optional[List[Dict]]:
        """
        Parse HTML to extract EPS ranking data.
        
        Looks for table rows with:
        - Stock code
        - Stock name
        - Latest quarter EPS
        - YoY growth
        """
        try:
            results = []
            
            # Look for table rows with data-code or similar
            # Pattern: <tr ...>.*?<td>代碼</td>.*?<td>NT$數字</td>
            row_pattern = r'<tr[^>]*>(.*?)</tr>'
            rows = re.findall(row_pattern, html, re.DOTALL)
            
            rank = 1
            for row in rows[:limit]:
                # Extract code
                code_match = re.search(r'<td[^>]*>\s*(\d{4})\s*</td>', row)
                if not code_match:
                    continue
                    
                code = code_match.group(1)
                
                # Extract name
                name_match = re.search(r'<td[^>]*>\s*([^<]+)\s*</td>', row)
                name = name_match.group(1) if name_match else ""
                
                # Extract EPS
                eps_match = re.search(r'NT\$?([\d,]+\.?\d*)', row)
                eps = None
                if eps_match:
                    try:
                        eps = float(eps_match.group(1).replace(',', ''))
                    except (ValueError, TypeError):
                        pass
                
                if code and eps:
                    results.append({
                        'code': code,
                        'name': unescape(name.strip()),
                        'latest_quarter_eps': eps,
                        'rank': rank
                    })
                    rank += 1
            
            return results if results else None
            
        except Exception as e:
            logger.error(f"Error parsing WantGoo EPS HTML: {e}")
            return None


# Singleton instances
_rating_scraper: Optional[TaiwanStockRatingScraper] = None
_eps_scraper: Optional[TaiwanStockEPSRankingScraper] = None


async def get_rating_scraper() -> TaiwanStockRatingScraper:
    """Get or create rating scraper instance"""
    global _rating_scraper
    if _rating_scraper is None:
        _rating_scraper = TaiwanStockRatingScraper()
    return _rating_scraper


async def get_eps_ranking_scraper() -> TaiwanStockEPSRankingScraper:
    """Get or create EPS ranking scraper instance"""
    global _eps_scraper
    if _eps_scraper is None:
        _eps_scraper = TaiwanStockEPSRankingScraper()
    return _eps_scraper
