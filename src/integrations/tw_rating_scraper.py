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



# Taiwan stock code → US ADR ticker mapping (for analyst data fallback)
TW_TO_US_ADR: Dict[str, str] = {
    "2330": "TSM",   # TSMC
    "2317": "HNHPF", # Foxconn
    "2412": "CHT",   # Chunghwa Telecom
    "2882": "FUBON", # Fubon (limited ADR)
}


class TaiwanStockRatingScraper:
    """Fetch Taiwan stock analyst ratings and target prices via Yahoo Finance"""

    def __init__(self):
        pass

    async def get_analyst_ratings(self, stock_code: str) -> Optional[Dict]:
        """
        Get analyst ratings and target prices from Yahoo Finance.

        Returns dict with buy_count, hold_count, sell_count,
        avg_target_price, max_target_price, min_target_price,
        rating_score, data_source. Returns None if unavailable.
        """
        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, self._fetch_yfinance_data, stock_code)
            return result
        except Exception as e:
            logger.error(f"Error fetching analyst data for {stock_code}: {e}")
            return None

    def _get_usd_twd_rate(self, yf) -> float:
        """Return current USD/TWD exchange rate; falls back to 32.0 on failure."""
        try:
            fx = yf.Ticker("USDTWD=X")
            rate = fx.fast_info.last_price
            if rate and 25.0 < float(rate) < 45.0:
                return float(rate)
        except Exception:
            pass
        return 32.0

    def _extract_from_info(self, info: dict, usd_rate: float = 1.0) -> dict:
        """Pull price targets and recommendation key from a yfinance info dict."""
        result = {}
        mean_price = info.get("targetMeanPrice")
        high_price = info.get("targetHighPrice")
        low_price  = info.get("targetLowPrice")
        num_analysts = info.get("numberOfAnalystOpinions", 0)
        rec_key = info.get("recommendationKey", "")

        if mean_price:
            result["avg_target_price"] = round(float(mean_price) * usd_rate)
        if high_price:
            result["max_target_price"] = round(float(high_price) * usd_rate)
        if low_price:
            result["min_target_price"] = round(float(low_price) * usd_rate)
        if num_analysts:
            result["num_analysts"] = int(num_analysts)
        if rec_key:
            result["recommendation_key"] = rec_key
        return result

    def _extract_recs(self, ticker) -> dict:
        """Pull buy/hold/sell counts and rating_score from recommendations_summary."""
        result = {}
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
                    result["rating_score"] = round(result["buy_count"] / total * 10, 1)
        except Exception as e:
            logger.debug(f"Could not read recommendations_summary: {e}")
        return result

    def _fetch_yfinance_data(self, stock_code: str) -> Optional[Dict]:
        """
        Fetch analyst data from Yahoo Finance synchronously.
        1. Try {code}.TW directly.
        2. If no analyst data, fall back to US ADR (if mapped) with USD→TWD conversion.
        """
        try:
            import yfinance as yf

            # ── Step 1: Try Taiwan market ticker ──────────────────────────────
            tw_symbol = f"{stock_code}.TW"
            try:
                ticker = yf.Ticker(tw_symbol)
                info = ticker.info or {}
                result = self._extract_from_info(info)
                result.update(self._extract_recs(ticker))

                if result.get("avg_target_price") or result.get("buy_count"):
                    result["data_source"] = "Yahoo Finance (TW)"
                    logger.info(f"Analyst data from {tw_symbol}: {result}")
                    return result
            except Exception as e:
                logger.debug(f"Taiwan ticker failed for {tw_symbol}: {e}")

            # ── Step 2: Fall back to US ADR ────────────────────────────────────
            us_symbol = TW_TO_US_ADR.get(stock_code)
            if not us_symbol:
                logger.warning(f"No analyst data and no US ADR mapping for {stock_code}")
                return None

            logger.info(f"No TW analyst data for {stock_code}, trying US ADR: {us_symbol}")
            try:
                usd_rate = self._get_usd_twd_rate(yf)
                ticker = yf.Ticker(us_symbol)
                info = ticker.info or {}
                result = self._extract_from_info(info, usd_rate=usd_rate)
                result.update(self._extract_recs(ticker))

                if result.get("avg_target_price") or result.get("buy_count"):
                    result["data_source"] = f"Yahoo Finance ({us_symbol} ADR, ×{usd_rate:.1f})"
                    logger.info(f"Analyst data from {us_symbol} ADR (rate={usd_rate}): {result}")
                    return result
            except Exception as e:
                logger.debug(f"US ADR fetch failed for {us_symbol}: {e}")

            logger.warning(f"No analyst data available for {stock_code}")
            return None

        except Exception as e:
            logger.error(f"yfinance error for {stock_code}: {e}")
            return None

    # Legacy stubs (kept for interface compatibility)
    def _parse_cnyes_ratings(self, html: str, stock_code: str) -> Optional[Dict]:
        return None

    def _extract_price(self, text: str) -> Optional[float]:
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
