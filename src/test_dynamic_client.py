#!/usr/bin/env python3
"""
Quick test of dynamic Taiwan stock client.
Tests if it can find "健策" and other stocks.
"""

import asyncio
import sys
sys.path.insert(0, '/app')

from src.integrations.tw_stock_dynamic import DynamicTaiwanStockClient


async def main():
    client = DynamicTaiwanStockClient()
    
    # Test 1: Search for 健策 by name
    print("=" * 50)
    print("Test 1: Search for 健策 (Dynamic)")
    print("=" * 50)
    stock = await client.search_stock("健策")
    if stock:
        print(f"✅ Found: {stock['code']} - {stock['zh_name']} ({stock['market']})")
    else:
        print("❌ Not found")
    
    # Test 2: Search for 台積電 by name
    print("\nTest 2: Search for 台積電 (Should find 2330)")
    print("=" * 50)
    stock = await client.search_stock("台積電")
    if stock:
        print(f"✅ Found: {stock['code']} - {stock['zh_name']} ({stock['market']})")
    else:
        print("❌ Not found")
    
    # Test 3: Search by code
    print("\nTest 3: Search by code (2330)")
    print("=" * 50)
    stock = await client.search_stock("2330")
    if stock:
        print(f"✅ Found: {stock['code']} - {stock['zh_name']} ({stock['market']})")
    else:
        print("❌ Not found")
    
    # Test 4: Get all stocks count
    print("\nTest 4: Get total stock count")
    print("=" * 50)
    all_stocks = await client.get_all_tw_stocks()
    print(f"✅ Total Taiwan stocks available: {len(all_stocks)}")
    
    # Show sample stocks
    if all_stocks:
        print("\nFirst 5 stocks:")
        for stock in all_stocks[:5]:
            print(f"  - {stock['code']}: {stock['zh_name']}")
    
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
