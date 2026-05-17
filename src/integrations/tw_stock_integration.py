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


# Taiwan stock code to name mapping
TW_STOCK_NAMES = {
    "2330": {"name": "Taiwan Semiconductor Manufacturing Company", "zh_name": "台積電", "code": "2330"},
    "2454": {"name": "MediaTek", "zh_name": "聯發科", "code": "2454"},
    "2317": {"name": "Acer", "zh_name": "宏碁", "code": "2317"},
    "3008": {"name": "Largan Precision", "zh_name": "大立光", "code": "3008"},
    "2498": {"name": "HTC", "zh_name": "宏達電", "code": "2498"},
    "2412": {"name": "Chunghwa Telecom", "zh_name": "中華電", "code": "2412"},
    "1303": {"name": "Nanya Technology", "zh_name": "南亞科", "code": "1303"},
    "2882": {"name": "Cathay Pacific Airways", "zh_name": "國泰金", "code": "2882"},
    "1101": {"name": "Taiwan Cement", "zh_name": "台泥", "code": "1101"},
    "2891": {"name": "China Airlines", "zh_name": "中華航", "code": "2891"},
    "1216": {"name": "Uni-President Enterprises", "zh_name": "統一", "code": "1216"},
    "9904": {"name": "Powertech Technology", "zh_name": "寶硯", "code": "9904"},
    "2409": {"name": "WISTRON", "zh_name": "威盛", "code": "2409"},
    "2357": {"name": "AU Optronics", "zh_name": "群創", "code": "2357"},
    "2308": {"name": "Delta Electronics", "zh_name": "台達電", "code": "2308"},
    "2348": {"name": "BroadTech", "zh_name": "華通", "code": "2348"},
    "2618": {"name": "Walton Advanced Engineering", "zh_name": "和鑫", "code": "2618"},
    "2603": {"name": "Long Tech Precision", "zh_name": "長智", "code": "2603"},
    "2610": {"name": "Realtek", "zh_name": "瑞昱", "code": "2610"},
    "1590": {"name": "Taiga Motors", "zh_name": "亞德客", "code": "1590"},
    "2542": {"name": "Gemtek", "zh_name": "智易", "code": "2542"},
    "3231": {"name": "Apex Materials Technology", "zh_name": "耀華", "code": "3231"},
    "4561": {"name": "Sunrise Medical Taiwan", "zh_name": "晟德", "code": "4561"},
    "2635": {"name": "Giga-Byte Technology", "zh_name": "技嘉", "code": "2635"},
    "2727": {"name": "Acer Aspire", "zh_name": "金寶", "code": "2727"},
    "5222": {"name": "TPK Touch Panel", "zh_name": "TPK", "code": "5222"},
}


class TaiwanStockClient:
    """Taiwan stock data fetcher using TWSE (Taiwan Stock Exchange) open API"""

    TWSE_URL = "https://mis.twse.com.tw/stock/api/getStockInfo.jsp"
    TIMEOUT = 8.0
    
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

                        # Prefer known stock info, fall back to TWSE names
                        stock_info = TW_STOCK_NAMES.get(stock_code, {})
                        zh_name = stock_info.get("zh_name", msg.get("n", stock_code))
                        en_name = stock_info.get("name", msg.get("nf", stock_code))
                        
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
            Stock code or None if not found
        """
        code_or_name = code_or_name.strip()
        
        # Check if it's a direct code (4 digits)
        if code_or_name.isdigit() and len(code_or_name) == 4:
            if code_or_name in TW_STOCK_NAMES:
                return code_or_name
            # If not in our mapping, still try to fetch it (might be valid code)
            return code_or_name
        
        # Check if it's a company name (Chinese)
        for code, info in TW_STOCK_NAMES.items():
            if info["zh_name"].lower() == code_or_name.lower():
                return code
        
        return None
