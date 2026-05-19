"""
Taiwan stock fundamentals scraper from CNYES and WantGoo.
Fetches analyst ratings, target prices, and quarterly EPS rankings.
"""

import aiohttp
import asyncio
from typing import Optional, Dict, List
from datetime import datetime
from decimal import Decimal
import re
from html import unescape

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Import fallback ratings at module level to avoid import issues
try:
    from src.utils.ratings_fallback import get_tw_stock_fallback_ratings
except ImportError as e:
    logger.warning(f"Could not import fallback ratings: {e}")
    def get_tw_stock_fallback_ratings(code: str):
        return {}


class TaiwanStockRatingScraper:
    """Scrape Taiwan stock ratings and price targets from CNYES"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = "https://www.cnyes.com/twstock/board/ratediff.aspx"
        
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
    
    async def get_analyst_ratings(self, stock_code: str) -> Optional[Dict]:
        """
        Get analyst ratings and target prices from CNYES.
        Falls back to cached data if live scraping fails.
        
        Args:
            stock_code: Taiwan stock code (e.g., "2330")
            
        Returns:
            Dict with keys:
            - 'buy_count': Number of buy ratings
            - 'hold_count': Number of hold ratings  
            - 'sell_count': Number of sell ratings
            - 'avg_target_price': Average analyst target price
            - 'max_target_price': Highest target price
            - 'min_target_price': Lowest target price
            - 'rating_score': Overall rating score (0-10)
            - 'source': "live" or "fallback" indicating data source
            
        Returns None if unable to fetch live data and no fallback available.
        """
        session = await self._get_session()
        
        try:
            # Try multiple URL formats for CNYES
            urls = [
                f"{self.base_url}?StockCode={stock_code}",  # Query parameter format
                f"https://www.cnyes.com/twstock/board/rating/{stock_code}",  # Direct path format
                f"https://www.cnyes.com/twstock/board/ratediff.aspx?StockCode={stock_code}",  # Explicit full URL
            ]
            
            result = None
            for url in urls:
                try:
                    async with session.get(
                        url,
                        timeout=aiohttp.ClientTimeout(total=8),
                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                    ) as response:
                        if response.status != 200:
                            logger.debug(f"CNYES URL returned {response.status}: {url}")
                            continue
                        
                        html = await response.text()
                        
                        # Parse HTML to extract rating data
                        result = self._parse_cnyes_ratings(html, stock_code)
                        
                        if result:
                            result["source"] = "live"
                            logger.info(f"Fetched analyst ratings for {stock_code} from {url}")
                            return result
                        else:
                            logger.debug(f"Could not parse ratings from {url}")
                
                except asyncio.TimeoutError:
                    logger.debug(f"CNYES timeout for {url}")
                    continue
                except Exception as e:
                    logger.debug(f"Error fetching {url}: {e}")
                    continue
            
            # If live scraping failed, try fallback data
            logger.info(f"Live CNYES scraping failed for {stock_code}, attempting fallback")
            fallback_result = self._get_fallback_ratings(stock_code)
            if fallback_result:
                logger.info(f"Using fallback ratings for {stock_code}")
                return fallback_result
            
            logger.warning(f"Could not fetch analyst ratings from any source for {stock_code}")
            return None
                    
        except Exception as e:
            logger.error(f"Error in get_analyst_ratings for {stock_code}: {e}")
            # Try fallback as last resort
            return self._get_fallback_ratings(stock_code)
    
    def _parse_cnyes_ratings(self, html: str, stock_code: str) -> Optional[Dict]:
        """
        Parse HTML content to extract analyst ratings for specific stock.
        
        CNYES returns a table with all recent ratings:
        <TR>
            <TD>20260519</TD>
            <TD><a href>2330-台積電</a></TD>
            <TD>Factset</TD>
            <TD></TD>
            <TD></TD>
            <TD>買進</TD>
            <TD>舊目標價</TD>
            <TD>新目標價</TD>
            <TD>其他價格</TD>
        </TR>
        """
        try:
            result = {}
            
            # Debug: Check if HTML contains expected keywords
            if "買進" not in html and "持有" not in html and "賣出" not in html:
                logger.warning(f"HTML doesn't contain rating keywords for {stock_code}")
                logger.debug(f"HTML sample (first 500 chars): {html[:500]}")
                return None
            
            if stock_code not in html:
                logger.warning(f"Stock code {stock_code} not found in HTML")
                return None
            
            # Split by <TR> to get individual rows
            rows = html.split('<TR')
            logger.debug(f"Found {len(rows)} potential rows in HTML")
            
            matches_found = 0
            for row in rows:
                # Look for the stock code in the row
                if not stock_code in row:
                    continue
                
                matches_found += 1
                logger.debug(f"Found row {matches_found} with stock code {stock_code}")
                
                # Extract all <TD>...</TD> values
                td_pattern = r'<TD[^>]*>([^<]*)</TD>'
                tds = re.findall(td_pattern, row)
                
                logger.debug(f"Extracted {len(tds)} TD values from row: {tds[:3]}...")  # Log first 3 TDs
                
                if len(tds) < 8:
                    logger.debug(f"Row has only {len(tds)} TD values, need at least 8")
                    continue
                
                # Expected format:
                # [0] = date
                # [1] = stock link (contains code and name)
                # [2] = analyst firm
                # [3] = blank
                # [4] = blank  
                # [5] = rating (買進/持有/賣出/強力買進)
                # [6] = old target price
                # [7] = new target price
                # [8+] = other prices
                
                rating = tds[5].strip() if len(tds) > 5 else ""
                old_price_str = tds[6].strip() if len(tds) > 6 else ""
                new_price_str = tds[7].strip() if len(tds) > 7 else ""
                
                logger.debug(f"Rating: '{rating}', Old Price: '{old_price_str}', New Price: '{new_price_str}'")
                
                # Extract price from strings (remove links, HTML, etc.)
                old_price = self._extract_price(old_price_str)
                new_price = self._extract_price(new_price_str)
                
                # Map rating to buy/hold/sell
                if "買進" in rating:
                    result["buy_count"] = result.get("buy_count", 0) + 1
                elif "持有" in rating:
                    result["hold_count"] = result.get("hold_count", 0) + 1
                elif "賣出" in rating:
                    result["sell_count"] = result.get("sell_count", 0) + 1
                
                # Store target prices
                if new_price:
                    if "target_prices" not in result:
                        result["target_prices"] = []
                    result["target_prices"].append(new_price)
                elif old_price:
                    if "target_prices" not in result:
                        result["target_prices"] = []
                    result["target_prices"].append(old_price)
            
            # Calculate aggregates if we found data
            if result or "target_prices" in result:
                # Calculate average target price
                if "target_prices" in result and result["target_prices"]:
                    prices = result["target_prices"]
                    result["avg_target_price"] = sum(prices) / len(prices)
                    result["max_target_price"] = max(prices)
                    result["min_target_price"] = min(prices)
                    del result["target_prices"]
                
                # Calculate rating score
                total = result.get("buy_count", 0) + result.get("hold_count", 0) + result.get("sell_count", 0)
                if total > 0:
                    buy_ratio = result.get("buy_count", 0) / total
                    result["rating_score"] = round(buy_ratio * 10, 1)
                
                if result:
                    return result
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing CNYES HTML: {e}")
            return None
    
    def _extract_price(self, text: str) -> Optional[float]:
        """Extract numeric price from text, handling NT$ prefix and commas"""
        if not text:
            return None
        
        try:
            # Remove HTML tags, links
            text = re.sub(r'<[^>]+>', '', text)
            # Remove NT$ prefix
            text = text.replace('NT$', '').replace('NT￥', '').strip()
            # Remove commas
            text = text.replace(',', '')
            
            if text and text != '-' and text != '':
                return float(text)
        except (ValueError, TypeError):
            pass
        
        return None
    
    def _get_fallback_ratings(self, stock_code: str) -> Optional[Dict]:
        """Get fallback analyst ratings for a stock"""
        try:
            fallback = get_tw_stock_fallback_ratings(stock_code)
            if fallback:
                fallback["source"] = "fallback"
                logger.debug(f"Returning fallback ratings for {stock_code}")
                return fallback
        except Exception as e:
            logger.debug(f"Error loading fallback ratings: {e}")
        
        return None


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
