"""
Alternative web scraper using requests library with better headers.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict
import re

from src.models.domain import Index, DataSourceEnum

logger = logging.getLogger(__name__)


class AlternativeWebScraper:
    """Use requests library for more reliable web scraping"""
    
    TIMEOUT = 10.0
    
    # More realistic browser headers
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    
    def fetch_from_yahoo_tw_sync(self) -> Dict[str, Index]:
        """
        Fetch US market indices using requests library (synchronous).
        This can be called from async code via executor.
        
        Returns:
            Dict mapping symbol to Index object
        """
        try:
            import requests
            
            logger.info("📄 Fetching from Yahoo Taiwan with requests library...")
            
            url = "https://tw.stock.yahoo.com/markets"
            
            response = requests.get(
                url,
                headers=self.HEADERS,
                timeout=self.TIMEOUT,
            )
            
            if response.status_code != 200:
                logger.warning(f"Yahoo Taiwan returned {response.status_code}")
                return {}
            
            html = response.text
            logger.info(f"✅ Got response ({len(html)} chars)")
            
            # Log first 1000 chars for debugging
            logger.info(f"Page content sample: {html[:1000]}")
            
            return self._parse_html(html)
        
        except ImportError:
            logger.warning("requests library not available")
            return {}
        except Exception as e:
            logger.warning(f"Error fetching from Yahoo Taiwan: {e}")
            return {}
    
    def _parse_html(self, html: str) -> Dict[str, Index]:
        """
        Parse HTML content for index data.
        
        Args:
            html: HTML content from the page
            
        Returns:
            Dict of indices
        """
        results = {}
        
        try:
            # Try with lxml if available for better parsing
            try:
                from lxml import html as lxml_html
                doc = lxml_html.fromstring(html)
                text = doc.text_content()
                logger.info("Using lxml parser")
            except ImportError:
                # Fallback to simple text extraction
                text = html
                logger.info("Using text fallback (lxml not available)")
            
            logger.info(f"Extracted text length: {len(text)}")
            logger.info(f"Text sample: {text[:500]}")
            
            # Search for index data with more flexible patterns
            # Looking for patterns like "^GSPC 5650" or "S&P 500 5650.75" or "5650.75 +25.25 0.45%"
            
            symbol_names = {
                "^GSPC": "S&P 500",
                "^IXIC": "納斯達克綜合指數",
                "^SOX": "費城半導體指數",
            }
            
            # Try various patterns to find index data
            patterns = {
                "^GSPC": [
                    r"(?:S&P\s*500|標普\s*500|SP500|GSPC)[^\d]*(\d+[.,]?\d*)[^\d]*([+-]?\d+[.,]?\d*)[^\d]*([+-]?\d+\.?\d*%)",
                    r"5[,.]?\d{3}[^\d]*([+-]?\d+[.,]?\d*)[^\d]*([+-]?\d+\.?\d*%)",  # S&P typically in 5000-6000 range
                ],
                "^IXIC": [
                    r"(?:NASDAQ|納斯達克|IXIC)[^\d]*(\d+[.,]?\d*)[^\d]*([+-]?\d+[.,]?\d*)[^\d]*([+-]?\d+\.?\d*%)",
                    r"1[67][,.]?\d{3}[^\d]*([+-]?\d+[.,]?\d*)[^\d]*([+-]?\d+\.?\d*%)",  # NASDAQ typically in 15000-18000 range
                ],
                "^SOX": [
                    r"(?:Philadelphia|費城|SOX)[^\d]*(\d+[.,]?\d*)[^\d]*([+-]?\d+[.,]?\d*)[^\d]*([+-]?\d+\.?\d*%)",
                    r"1[,.]?\d{4}[^\d]*([+-]?\d+[.,]?\d*)[^\d]*([+-]?\d+\.?\d*%)",  # SOX typically in 12000+ range
                ],
            }
            
            for symbol, pattern_list in patterns.items():
                for pattern in pattern_list:
                    matches = list(re.finditer(pattern, text, re.IGNORECASE))
                    if matches:
                        logger.info(f"Found {len(matches)} matches for {symbol}")
                        # Use the first match
                        match = matches[0]
                        try:
                            current_price = Decimal(match.group(1).replace(",", ""))
                            change_amount = Decimal(match.group(2).replace(",", ""))
                            change_percent_str = match.group(3).replace("%", "").replace("+", "")
                            change_percent = Decimal(change_percent_str)
                            
                            previous_close = current_price - change_amount
                            
                            if current_price > 0 and previous_close > 0:
                                index = Index(
                                    id=symbol,
                                    code=symbol,
                                    zh_name=symbol_names[symbol],
                                    current_price=current_price.quantize(Decimal("0.01")),
                                    previous_close=previous_close.quantize(Decimal("0.01")),
                                    change_amount=change_amount.quantize(Decimal("0.01")),
                                    change_percent=change_percent.quantize(Decimal("0.01")),
                                    high_52w=Decimal("0"),
                                    low_52w=Decimal("0"),
                                    last_updated=datetime.utcnow(),
                                    data_source=DataSourceEnum.YAHOO_FINANCE,
                                )
                                results[symbol] = index
                                logger.info(f"✅ Parsed {symbol}: {current_price}")
                                break
                        except Exception as e:
                            logger.warning(f"Error parsing {symbol}: {e}")
                            continue
            
            logger.info(f"Successfully parsed {len(results)} indices")
            return results
        
        except Exception as e:
            logger.warning(f"HTML parsing error: {e}")
            return {}
