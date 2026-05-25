"""
Test web scraper functionality directly.
"""

import asyncio
import sys
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_web_scraper():
    """Test web scraper with direct API call"""
    
    import aiohttp
    from decimal import Decimal
    
    SYMBOLS = ["^GSPC", "^IXIC", "^SOX"]
    YAHOO_FINANCE_URL = "https://query1.finance.yahoo.com/v10/finance/quoteSummary"
    
    async with aiohttp.ClientSession() as session:
        for symbol in SYMBOLS:
            try:
                print(f"\n{'='*60}")
                print(f"Testing {symbol}...")
                print(f"{'='*60}")
                
                url = f"{YAHOO_FINANCE_URL}/{symbol}"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                params = {"modules": "price"}
                
                print(f"URL: {url}")
                print(f"Params: {params}")
                
                async with session.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10.0),
                ) as response:
                    print(f"Status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"\n✅ Response received (length: {len(str(data))} chars)")
                        
                        # Try to parse
                        try:
                            price_data = data.get("quoteSummary", {}).get("result", [{}])[0].get("price", {})
                            print(f"\nPrice data keys: {price_data.keys()}")
                            
                            current_price = price_data.get("regularMarketPrice", {}).get("raw", None)
                            previous_close = price_data.get("regularMarketPreviousClose", {}).get("raw", None)
                            
                            print(f"Current Price: {current_price}")
                            print(f"Previous Close: {previous_close}")
                            
                            if current_price and previous_close:
                                change = Decimal(str(current_price)) - Decimal(str(previous_close))
                                change_pct = (change / Decimal(str(previous_close)) * 100)
                                print(f"Change: {change} ({change_pct}%)")
                                print(f"\n✅ {symbol}: {current_price}")
                            else:
                                print(f"\n❌ Missing price data for {symbol}")
                        except Exception as parse_err:
                            print(f"\n❌ Parse error: {parse_err}")
                            print(f"Response sample: {str(data)[:200]}")
                    else:
                        text = await response.text()
                        print(f"❌ Status {response.status}: {text[:200]}")
                
                # Rate limiting
                await asyncio.sleep(1.0)
                
            except asyncio.TimeoutError:
                print(f"❌ Timeout for {symbol}")
            except aiohttp.ClientError as e:
                print(f"❌ Network error for {symbol}: {e}")
            except Exception as e:
                print(f"❌ Unexpected error for {symbol}: {e}")

if __name__ == "__main__":
    asyncio.run(test_web_scraper())
