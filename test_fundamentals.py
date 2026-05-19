"""
Quick test script to verify fundamental data fetching works.
Run with: python test_fundamentals.py
"""

import asyncio
import aiohttp
from decimal import Decimal

async def test_alpha_vantage():
    """Test Alpha Vantage API"""
    print("\n=== 測試 Alpha Vantage (美股) ===")
    
    api_key = "X3D9JOV3419U3TU1"
    symbol = "AAPL"
    
    async with aiohttp.ClientSession() as session:
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "OVERVIEW",
            "symbol": symbol,
            "apikey": api_key,
        }
        
        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Alpha Vantage 響應成功")
                    
                    # Check key fields
                    fields = ["TrailingPE", "EPS", "DividendYield", "AnalystTargetPrice"]
                    for field in fields:
                        value = data.get(field, "N/A")
                        print(f"   {field}: {value}")
                    
                    return True
                else:
                    print(f"❌ Alpha Vantage 返回狀態碼: {response.status}")
                    return False
        except asyncio.TimeoutError:
            print(f"❌ Alpha Vantage 超時（>15秒）")
            return False
        except Exception as e:
            print(f"❌ Alpha Vantage 錯誤: {e}")
            return False

async def test_goodinfo():
    """Test GOODINFO scraper"""
    print("\n=== 測試 GOODINFO 台股爬蟲 ===")
    
    stock_code = "2330"  # TSMC
    url = f"https://goodinfo.tw/StockInfo/StockBzPerformance.asp"
    
    async with aiohttp.ClientSession(
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    ) as session:
        try:
            async with session.get(
                url,
                params={"STOCK_ID": stock_code},
                timeout=aiohttp.ClientTimeout(total=15),
                ssl=False
            ) as response:
                if response.status == 200:
                    html = await response.text()
                    print(f"✅ GOODINFO 響應成功 (HTML 長度: {len(html)} 字符)")
                    
                    # Try to find P/E ratio in HTML
                    import re
                    pe_match = re.search(r'本益比[：:]\s*([0-9.]+)', html)
                    if pe_match:
                        print(f"   ✅ 找到本益比: {pe_match.group(1)}x")
                    else:
                        print(f"   ⚠️  找不到本益比 (HTML 結構可能改變)")
                    
                    return True
                else:
                    print(f"❌ GOODINFO 返回狀態碼: {response.status}")
                    return False
        except asyncio.TimeoutError:
            print(f"❌ GOODINFO 超時（>15秒）")
            return False
        except Exception as e:
            print(f"❌ GOODINFO 錯誤: {e}")
            return False

async def test_yahoo_tw():
    """Test Yahoo Finance Taiwan"""
    print("\n=== 測試 Yahoo Finance Taiwan ===")
    
    stock_code = "2330"
    symbol = f"{stock_code}.TW"
    url = f"https://tw.finance.yahoo.com/quote/{symbol}"
    
    async with aiohttp.ClientSession(
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    ) as session:
        try:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                if response.status == 200:
                    html = await response.text()
                    print(f"✅ Yahoo Taiwan 響應成功 (HTML 長度: {len(html)} 字符)")
                    
                    # Try to find data
                    import re
                    pe_match = re.search(r'本益比[：:]\s*([0-9.]+)', html)
                    if pe_match:
                        print(f"   ✅ 找到本益比: {pe_match.group(1)}x")
                    else:
                        print(f"   ⚠️  找不到本益比")
                    
                    return True
                else:
                    print(f"❌ Yahoo Taiwan 返回狀態碼: {response.status}")
                    return False
        except asyncio.TimeoutError:
            print(f"❌ Yahoo Taiwan 超時（>15秒）")
            return False
        except Exception as e:
            print(f"❌ Yahoo Taiwan 錯誤: {e}")
            return False

async def main():
    print("🔧 基本面數據源測試")
    print("=" * 50)
    
    results = {
        "Alpha Vantage (美股)": await test_alpha_vantage(),
        "GOODINFO (台股)": await test_goodinfo(),
        "Yahoo Taiwan (台股)": await test_yahoo_tw(),
    }
    
    print("\n" + "=" * 50)
    print("📊 測試結果摘要:")
    for source, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {source}")

if __name__ == "__main__":
    asyncio.run(main())
