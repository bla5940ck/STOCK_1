"""
IEX Cloud API client for real-time stock quotes.

Free tier: 100 requests/month (perfect for daily index queries)
Reliable and works well on cloud platforms like Render
"""

import asyncio
import logging
import os
from decimal import Decimal
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)


class IEXCloudClient:
    """Client for IEX Cloud API - real-time market data"""
    
    BASE_URL = "https://cloud.iexapis.com/stable"
    
    def __init__(self):
        """Initialize IEX Cloud client with API token from environment"""
        self.api_token = os.getenv("IEX_CLOUD_TOKEN")
        if not self.api_token:
            logger.warning("⚠️  IEX_CLOUD_TOKEN not set in environment")
    
    async def fetch_quote(self, symbol: str) -> Optional[dict]:
        """
        Fetch real-time quote for a symbol.
        
        Args:
            symbol: Stock symbol (e.g., "^GSPC" for S&P 500)
            
        Returns:
            Dict with price data or None if fetch fails
        """
        if not self.api_token:
            logger.error("❌ IEX_CLOUD_TOKEN not configured")
            return None
        
        url = f"{self.BASE_URL}/data/core/quote/{symbol}"
        params = {"token": self.api_token}
        
        try:
            async with aiohttp.ClientSession() as session:
                logger.info(f"📊 Fetching {symbol} from IEX Cloud...")
                
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(f"✅ Fetched {symbol}: ${data.get('latestPrice')}")
                        return data
                    elif resp.status == 403:
                        logger.error(f"❌ Invalid API token")
                        return None
                    elif resp.status == 404:
                        logger.warning(f"⚠️  Symbol not found: {symbol}")
                        return None
                    else:
                        logger.warning(f"⚠️  IEX Cloud returned {resp.status}")
                        return None
                        
        except asyncio.TimeoutError:
            logger.error(f"❌ IEX Cloud timeout for {symbol}")
            return None
        except Exception as e:
            logger.error(f"❌ IEX Cloud fetch failed: {str(e)[:100]}")
            return None
    
    async def fetch_indices(self, symbols: list[str]) -> dict:
        """
        Fetch multiple indices.
        
        Args:
            symbols: List of index symbols (e.g., ["^GSPC", "^IXIC", "^SOX"])
            
        Returns:
            Dict mapping symbol -> quote data
        """
        results = {}
        
        for symbol in symbols:
            quote = await self.fetch_quote(symbol)
            if quote:
                results[symbol] = quote
        
        return results

