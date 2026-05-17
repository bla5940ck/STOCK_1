"""
Taiwan stock integration for fetching real-time stock data using TWSE open API.
"""

import aiohttp
import asyncio
import random
from typing import Dict, Optional, Tuple
from decimal import Decimal
from datetime import datetime

from src.models.domain import Stock, DataSourceEnum
from src.exceptions import APIError, TimeoutError as TimeoutException
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TaiwanStockClient:
    """Taiwan stock data fetcher using TWSE (Taiwan Stock Exchange) open API"""

    TWSE_URL = "https://mis.twse.com.tw/stock/api/getStockInfo.jsp"
    TWSE_LISTING_URL = "https://mis.twse.com.tw/stock/api/twtrade.jsp"  # For stock list
    TIMEOUT = 8.0
    
    # Simple in-memory cache for stock names -> codes (populated on first search)
    _stock_name_cache = {}  # e.g., {"台積電": "2330", "健策": "2425", ...}
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    ]

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            self.session = None

    def _get_random_user_agent(self) -> str:
        """Get random User-Agent"""
        return random.choice(self.USER_AGENTS)

    async def fetch_tw_stock(self, symbol: str, retries: int = 3) -> Optional[dict]:
        """
        Fetch Taiwan stock real-time data from TWSE open API.
        
        Args:
            symbol: Taiwan stock code (e.g., "2330")
            retries: Number of retry attempts
            
        Returns:
            Dict with stock info or None if failed
        """
        session = await self._get_session()
        
        # Normalize symbol (remove .TW suffix if present)
        stock_code = symbol.replace(".TW", "").replace(".tw", "")
        
        # Try TSE first, then OTC
        for market in ("tse", "otc"):
            ex_ch = f"{market}_{stock_code}.tw"
            params = {
                "ex_ch": ex_ch,
                "json": "1",
                "delay": "0",
            }
            headers = {
                "User-Agent": self._get_random_user_agent(),
                "Referer": "https://mis.twse.com.tw/stock/fibest.jsp",
            }

            for attempt in range(retries):
                try:
                    async with session.get(
                        self.TWSE_URL,
                        params=params,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=self.TIMEOUT),
                    ) as response:
                        if response.status == 429:
                            if attempt < retries - 1:
                                wait_time = 2 ** attempt
                                logger.warning(f"Rate limited for {stock_code}, retrying in {wait_time}s...")
                                await asyncio.sleep(wait_time)
                                continue
                            else:
                                break  # Try next market (tse->otc)
                        
                        if response.status != 200:
                            logger.warning(f"TWSE API returned {response.status} for {ex_ch}")
                            break  # Try next market

                        data = await response.json(content_type=None)
                        msg_array = data.get("msgArray", [])
                        
                        if not msg_array:
                            break  # Try next market (stock might be on OTC)
                        
                        msg = msg_array[0]
                        
                        # z = current price, y = previous close
                        current_price_str = msg.get("z", "-")
                        if current_price_str == "-" or not current_price_str:
                            # Market closed - use previous close as current
                            current_price_str = msg.get("pz", msg.get("y", "0"))
                        
                        previous_close_str = msg.get("y", "0")
                        open_price_str = msg.get("o", "0")
                        high_price_str = msg.get("h", "0")
                        low_price_str = msg.get("l", "0")
                        volume_str = msg.get("v", "0")
                        
                        current_price = Decimal(current_price_str) if current_price_str and current_price_str != "-" else Decimal("0")
                        previous_close = Decimal(previous_close_str) if previous_close_str and previous_close_str != "-" else Decimal("0")
                        open_price = Decimal(open_price_str) if open_price_str and open_price_str != "-" else Decimal("0")
                        high_price = Decimal(high_price_str) if high_price_str and high_price_str != "-" else Decimal("0")
                        low_price = Decimal(low_price_str) if low_price_str and low_price_str != "-" else Decimal("0")
                        volume = int(volume_str) * 1000 if volume_str and volume_str != "-" else 0
                        
                        if current_price == 0:
                            logger.warning(f"Zero price for {stock_code}")
                            return None

                        # Calculate change
                        change_amount = current_price - previous_close if previous_close > 0 else Decimal("0")
                        change_percent = (change_amount / previous_close * 100) if previous_close > 0 else Decimal("0")

                        # Stock name from TWSE API
                        zh_name = msg.get("n", stock_code)
                        en_name = msg.get("nf", stock_code)
                        
                        return {
                            "code": stock_code,
                            "name": en_name,
                            "zh_name": zh_name,
                            "current_price": current_price,
                            "previous_close": previous_close,
                            "open_price": open_price,
                            "high_price": high_price,
                            "low_price": low_price,
                            "change_amount": change_amount,
                            "change_percent": change_percent,
                            "volume": volume,
                            "data_source": "twse",
                            "currency": "TWD",
                        }
                except asyncio.TimeoutError:
                    if attempt < retries - 1:
                        wait_time = 2 ** attempt
                        logger.warning(f"Timeout fetching {stock_code}, retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    logger.error(f"Timeout fetching Taiwan stock {stock_code} after {retries} retries")
                    break
                except Exception as e:
                    logger.error(f"Error fetching Taiwan stock {stock_code}: {e}")
                    break

        logger.error(f"Failed to fetch Taiwan stock data for {stock_code}")
        return None

    @staticmethod
    def resolve_tw_stock_code(code_or_name: str) -> Optional[str]:
        """
        Resolve Taiwan stock code from code or company name.
        
        Args:
            code_or_name: Stock code (e.g., "2330") or company name (e.g., "台積電")
            
        Returns:
            Stock code or None if not found. 
            For codes: returns directly. For names: should use search_tw_stock() for dynamic lookup.
        """
        code_or_name = code_or_name.strip()
        
        # Check if it's a direct code (4 digits)
        if code_or_name.isdigit() and len(code_or_name) == 4:
            # Return the code directly - TWSE API will validate it
            return code_or_name
        
        # For company names, return None here - caller should use search_tw_stock() instead
        # This supports dynamic lookup without hardcoded mappings
        return None

    async def search_tw_stock(self, company_name: str, retries: int = 2) -> Optional[str]:
        """
        Search for Taiwan stock code by company name using cached stock list.
        
        First tries to find exact match in cache, then fetches from TWSE if not cached.
        
        Args:
            company_name: Chinese company name (e.g., "台積電", "健策")
            retries: Number of retry attempts
            
        Returns:
            Stock code if found, None otherwise
        """
        company_name = company_name.strip().lower()
        
        # Try to find in cache first
        for cached_name, code in TaiwanStockClient._stock_name_cache.items():
            if cached_name.lower() == company_name or company_name in cached_name.lower():
                logger.debug(f"Found {company_name} in cache -> {code}")
                return code
        
        # If not in cache, try to fetch the stock directly
        # (in case user knows the code or it's a common stock)
        # Try fetching by trying the first few possible formats
        session = await self._get_session()
        
        # Build a simple query using the name
        params = {
            "ex_ch": f"tse_{company_name}.tw",
            "json": "1",
            "delay": "0",
        }
        
        headers = {
            "User-Agent": self._get_random_user_agent(),
            "Referer": "https://mis.twse.com.tw/stock/fibest.jsp",
        }
        
        for attempt in range(retries):
            try:
                async with session.get(
                    self.TWSE_URL,
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.TIMEOUT),
                ) as response:
                    if response.status == 200:
                        data = await response.json(content_type=None)
                        msg_array = data.get("msgArray", [])
                        
                        if msg_array:
                            msg = msg_array[0]
                            # Cache this result
                            stock_zh_name = msg.get("n", "").strip()
                            if stock_zh_name:
                                TaiwanStockClient._stock_name_cache[stock_zh_name] = company_name
                            
                            ex_ch = msg.get("ex_ch", "")
                            if ex_ch and "_" in ex_ch:
                                code = ex_ch.split("_")[1].replace(".tw", "")
                                logger.debug(f"Found {company_name} via API -> {code}")
                                return code
                    
                    if response.status == 429 and attempt < retries - 1:
                        wait_time = 2 ** attempt
                        logger.warning(f"Rate limited searching {company_name}, retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                        
            except asyncio.TimeoutError:
                if attempt < retries - 1:
                    logger.debug(f"Timeout searching {company_name}, retrying...")
                    await asyncio.sleep(1)
                    continue
            except Exception as e:
                logger.debug(f"Error searching stock {company_name}: {e}")
        
        logger.debug(f"No stock found for {company_name}")
        return None
