#!/usr/bin/env python3
"""
Test which API works for getting US market indices
Run this locally to verify before pushing to Render
"""
import asyncio
import aiohttp
from decimal import Decimal

async def test_yahoo_finance():
    """Test Yahoo Finance quote endpoint"""
    print("\n" + "="*70)
    print("🧪 Testing Yahoo Finance Quote Endpoint")
    print("="*70)
    
    symbols = ["^GSPC", "^IXIC", "^SOX"]
    
    async with aiohttp.ClientSession() as session:
        for symbol in symbols:
            try:
                url = "https://query1.finance.yahoo.com/v10/finance/quoteSummary/" + symbol
                params = {"modules": "price"}
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                }
                
                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=5),
                    headers=headers,
                ) as response:
                    print(f"\n{symbol}: HTTP {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        print(f"  ✅ Got data: {str(data)[:100]}...")
                    else:
                        text = await response.text()
                        print(f"  ❌ Error: {text[:100]}")
                        
            except Exception as e:
                print(f"{symbol}: ❌ Exception: {str(e)[:100]}")

async def test_iex():
    """Test IEX Cloud API (free tier)"""
    print("\n" + "="*70)
    print("🧪 Testing IEX Cloud API")
    print("="*70)
    
    symbols = ["GSPC", "IXIC", "SOX"]  # IEX uses different format
    
    async with aiohttp.ClientSession() as session:
        for symbol in symbols:
            try:
                url = f"https://cloud.iexapis.com/stable/data/core_quote/{symbol}"
                params = {"token": "pk_free"}  # Free tier token
                
                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    print(f"\n{symbol}: HTTP {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        price = data.get("latestPrice")
                        change = data.get("change")
                        print(f"  ✅ Price: {price}, Change: {change}")
                    else:
                        text = await response.text()
                        print(f"  ❌ Error: {text[:100]}")
                        
            except Exception as e:
                print(f"{symbol}: ❌ Exception: {str(e)[:100]}")

async def test_polygon():
    """Test Polygon.io API (free tier)"""
    print("\n" + "="*70)
    print("🧪 Testing Polygon.io API")
    print("="*70)
    
    symbols = ["I:GSPC", "I:IXIC", "I:SOX"]
    
    async with aiohttp.ClientSession() as session:
        for symbol in symbols:
            try:
                url = f"https://api.polygon.io/v3/quotes/{symbol}"
                params = {"apiKey": "test"}  # Need real key
                
                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    print(f"\n{symbol}: HTTP {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        print(f"  ✅ Got data: {str(data)[:100]}...")
                    else:
                        print(f"  ❌ HTTP {response.status}")
                        
            except Exception as e:
                print(f"{symbol}: ❌ Exception: {str(e)[:100]}")

async def test_simple_json_api():
    """Test a simple public JSON API"""
    print("\n" + "="*70)
    print("🧪 Testing Simple Public APIs")
    print("="*70)
    
    # Try marketstack.com (free tier available)
    try:
        print("\n📍 Trying marketstack.com...")
        async with aiohttp.ClientSession() as session:
            url = "http://api.marketstack.com/v1/tickers/AAPL/intraday"
            params = {
                "access_key": "test",  # Would need real key
            }
            
            async with session.get(url, params=params, timeout=5) as response:
                print(f"  Status: {response.status}")
                data = await response.json()
                print(f"  Response: {str(data)[:100]}...")
                
    except Exception as e:
        print(f"  ❌ {str(e)[:100]}")

async def main():
    print("\n" + "🔍 Testing Multiple APIs for US Market Indices" + "\n")
    
    print("""
Instructions:
1. Run this script locally to find which API works
2. Once we find a working API, update market_data.py
3. Then push to Render

Testing endpoints...
    """)
    
    try:
        await test_yahoo_finance()
    except Exception as e:
        print(f"Yahoo Finance test failed: {e}")
    
    try:
        await test_iex()
    except Exception as e:
        print(f"IEX test failed: {e}")
        
    try:
        await test_polygon()
    except Exception as e:
        print(f"Polygon test failed: {e}")
        
    try:
        await test_simple_json_api()
    except Exception as e:
        print(f"Simple API test failed: {e}")
    
    print("\n" + "="*70)
    print("✅ Test Complete - Check which API returned data")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(main())
