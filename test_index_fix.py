#!/usr/bin/env python3
"""
Direct test of the index query fix
Tests the CSV download strategy without needing full app startup
"""
import asyncio
import sys
from decimal import Decimal
from datetime import datetime

# Mock the necessary imports
class MockIndex:
    def __init__(self, code, zh_name, current_price, change_percent):
        self.id = code
        self.code = code
        self.zh_name = zh_name
        self.current_price = current_price
        self.change_percent = change_percent
        self.previous_close = Decimal("0")
        self.change_amount = Decimal("0")
        self.high_52w = Decimal("0")
        self.low_52w = Decimal("0")
        self.last_updated = datetime.utcnow()
        self.data_source = "YAHOO_FINANCE"
    
    def __repr__(self):
        return f"Index({self.code}, {self.zh_name}, {self.current_price}, {self.change_percent}%)"

async def test_csv_download():
    """Test Yahoo Finance CSV download logic"""
    import aiohttp
    
    print("=" * 70)
    print("🧪 Testing Yahoo Finance CSV Download Strategy")
    print("=" * 70)
    
    indices_dict = {}
    index_info = {
        "^GSPC": "S&P 500",
        "^IXIC": "納斯達克綜合指數",
        "^SOX": "費城半導體指數",
    }
    
    # Test CSV download
    try:
        print("\n📊 Attempting Yahoo Finance CSV download...")
        print(f"   Timeout: 10 seconds per index")
        print(f"   Endpoints: query1.finance.yahoo.com")
        
        async with aiohttp.ClientSession() as session:
            for symbol, zh_name in index_info.items():
                try:
                    url = f"https://query1.finance.yahoo.com/v7/finance/download/{symbol}"
                    params = {
                        "period1": "1",
                        "period2": "9999999999",
                        "interval": "1d",
                        "events": "history",
                    }
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5",
                    }
                    
                    print(f"\n   📥 Fetching {symbol} ({zh_name})...")
                    async with session.get(
                        url,
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=10),
                        headers=headers,
                    ) as response:
                        print(f"      Status: {response.status}")
                        
                        if response.status != 200:
                            print(f"      ❌ Failed: HTTP {response.status}")
                            continue
                        
                        text = await response.text()
                        lines = text.strip().split('\n')
                        print(f"      ✅ Got {len(lines)} lines of CSV data")
                        
                        if len(lines) < 2:
                            print(f"      ⚠️  No data rows found")
                            continue
                        
                        # Parse header
                        header = lines[0]
                        print(f"      Header: {header}")
                        
                        # Parse latest row
                        latest_line = lines[-1]
                        print(f"      Latest: {latest_line[:50]}...")
                        
                        parts = latest_line.split(',')
                        
                        if len(parts) < 5:
                            print(f"      ❌ Invalid format: only {len(parts)} columns")
                            continue
                        
                        try:
                            date = parts[0]
                            open_price = Decimal(parts[1])
                            high_price = Decimal(parts[2])
                            low_price = Decimal(parts[3])
                            close_price = Decimal(parts[4])
                            
                            change_amount = close_price - open_price
                            change_percent = (change_amount / open_price * 100) if open_price > 0 else Decimal("0")
                            
                            index = MockIndex(
                                code=symbol,
                                zh_name=zh_name,
                                current_price=close_price.quantize(Decimal("0.01")),
                                change_percent=change_percent.quantize(Decimal("0.01"))
                            )
                            
                            indices_dict[symbol] = index
                            print(f"      ✅ Parsed successfully!")
                            print(f"         Date: {date}")
                            print(f"         Open: ${open_price}")
                            print(f"         Close: ${close_price}")
                            print(f"         Change: {change_percent:.2f}%")
                            
                        except (ValueError, IndexError) as e:
                            print(f"      ❌ Parse error: {e}")
                            continue
                            
                except asyncio.TimeoutError:
                    print(f"      ❌ Timeout after 10 seconds")
                except Exception as e:
                    print(f"      ❌ Error: {type(e).__name__}: {str(e)[:100]}")
        
        print(f"\n{'=' * 70}")
        print(f"📊 Results:")
        print(f"{'=' * 70}")
        
        if len(indices_dict) >= 2:
            print(f"\n✅ SUCCESS! Retrieved {len(indices_dict)} indices:")
            for symbol, index in indices_dict.items():
                print(f"\n   📈 {index.zh_name} ({symbol})")
                print(f"      Current Price: ${index.current_price}")
                print(f"      Change: {index.change_percent}%")
            
            print(f"\n🎉 CSV Download Strategy Working!")
            return True
        else:
            print(f"\n⚠️  WARNING: Only retrieved {len(indices_dict)} indices (need >= 2)")
            print(f"   This would trigger fallback to stale cache or error")
            return False
            
    except Exception as e:
        print(f"\n❌ FAILED: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the test"""
    success = await test_csv_download()
    
    print(f"\n{'=' * 70}")
    if success:
        print("✅ Test PASSED - Index query fix is working!")
        sys.exit(0)
    else:
        print("❌ Test WARNING - May need fallback strategies")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
