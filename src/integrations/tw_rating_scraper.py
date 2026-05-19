"""
Taiwan stock fundamentals scraper from CNYES and WantGoo.
Fetches analyst ratings, target prices, and quarterly EPS rankings.
Uses Playwright for JavaScript-rendered pages.
"""

import asyncio
from typing import Optional, Dict, List
from datetime import datetime
from decimal import Decimal
import re
from html import unescape

from src.utils.logger import get_logger

logger = get_logger(__name__)

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    logger.warning("Playwright not available, will use basic HTTP fallback")
    PLAYWRIGHT_AVAILABLE = False


class TaiwanStockRatingScraper:
    """Scrape Taiwan stock ratings and price targets from CNYES using Playwright"""
    
    def __init__(self):
        self.base_url = "https://www.cnyes.com/twstock/board/ratediff.aspx"
        
    async def get_analyst_ratings(self, stock_code: str) -> Optional[Dict]:
        """
        Get analyst ratings and target prices from CNYES.
        Uses Playwright to handle JavaScript-rendered content.
        
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
            
        Returns None if unable to fetch.
        """
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright not available for CNYES scraping")
            return None
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                try:
                    # Navigate to CNYES rating page
                    url = f"{self.base_url}?StockCode={stock_code}"
                    logger.info(f"Loading CNYES page: {url}")
                    
                    await page.goto(url, wait_until="networkidle", timeout=10000)
                    
                    # Wait for table to load
                    await page.wait_for_selector("table tr", timeout=5000)
                    
                    # Get the rendered HTML
                    html = await page.content()
                    
                    # Parse the HTML to extract ratings
                    result = self._parse_cnyes_ratings(html, stock_code)
                    
                    if result:
                        logger.info(f"Successfully scraped {stock_code} ratings from CNYES")
                        return result
                    else:
                        logger.warning(f"Could not parse ratings for {stock_code} from rendered HTML")
                        return None
                
                finally:
                    await browser.close()
                    
        except Exception as e:
            logger.error(f"Error scraping CNYES with Playwright for {stock_code}: {e}")
            return None
    
    def _parse_cnyes_ratings(self, html: str, stock_code: str) -> Optional[Dict]:
        """
        Parse HTML content to extract analyst ratings for specific stock.
        
        CNYES table format:
        <TR>
            <TD>Date</TD>
            <TD>Stock Code-Name</TD>
            <TD>Firm</TD>
            <TD>Rating (買進/強力買進/etc)</TD>
            <TD>Price 1</TD>
            <TD>Price 2</TD>
            ...
        </TR>
        """
        try:
            result = {}
            
            # Debug: Check if HTML contains expected keywords
            if "買進" not in html and "持有" not in html and "賣出" not in html:
                logger.warning(f"HTML doesn't contain rating keywords for {stock_code}")
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
                
                # Extract all <TD>...</TD> values
                td_pattern = r'<TD[^>]*>([^<]*)</TD>'
                tds = re.findall(td_pattern, row)
                
                logger.debug(f"Row {matches_found}: Found {len(tds)} TD values")
                
                if len(tds) < 4:
                    logger.debug(f"Row has only {len(tds)} TD values, need at least 4")
                    continue
                
                # Find rating column (search through TDs for rating keywords)
                rating = ""
                rating_idx = -1
                for i in range(len(tds)):
                    if "買進" in tds[i] or "持有" in tds[i] or "賣出" in tds[i] or "強力" in tds[i]:
                        rating = tds[i].strip()
                        rating_idx = i
                        break
                
                if not rating or rating_idx == -1:
                    logger.debug(f"No rating found in row")
                    continue
                
                logger.debug(f"Found rating: '{rating}' at index {rating_idx}")
                
                # Extract prices - look for numeric values after rating
                prices = []
                for i in range(rating_idx + 1, len(tds)):
                    td_val = tds[i].strip()
                    if td_val:  # Not empty
                        price = self._extract_price(td_val)
                        if price:
                            prices.append(price)
                            logger.debug(f"Extracted price from TD[{i}]: {price}")
                
                # Map rating to buy/hold/sell
                if "買進" in rating or "強力買進" in rating:
                    result["buy_count"] = result.get("buy_count", 0) + 1
                elif "持有" in rating:
                    result["hold_count"] = result.get("hold_count", 0) + 1
                elif "賣出" in rating:
                    result["sell_count"] = result.get("sell_count", 0) + 1
                
                # Store target prices
                if prices:
                    if "target_prices" not in result:
                        result["target_prices"] = []
                    result["target_prices"].extend(prices)
            
            logger.info(f"Total rating rows found for {stock_code}: {matches_found}")
            
            # Calculate aggregates if we found data
            if "target_prices" in result and result["target_prices"]:
                prices = result["target_prices"]
                result["avg_target_price"] = sum(prices) / len(prices)
                result["max_target_price"] = max(prices)
                result["min_target_price"] = min(prices)
                del result["target_prices"]
                
                # Set counts with defaults
                result["buy_count"] = result.get("buy_count", 0)
                result["hold_count"] = result.get("hold_count", 0)
                result["sell_count"] = result.get("sell_count", 0)
                
                # Calculate rating score
                total = result["buy_count"] + result["hold_count"] + result["sell_count"]
                if total > 0:
                    buy_ratio = result["buy_count"] / total
                    result["rating_score"] = round(buy_ratio * 10, 1)
                
                logger.info(f"Successfully parsed ratings for {stock_code}: buy={result['buy_count']}, hold={result['hold_count']}, sell={result['sell_count']}, avg_price={result['avg_target_price']:.2f}")
                return result
            
            logger.warning(f"No prices found for {stock_code}")
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
