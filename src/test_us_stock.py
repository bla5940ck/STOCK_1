#!/usr/bin/env python3
"""Test US stock query"""

import asyncio
import sys
sys.path.insert(0, '/app')

from src.integrations.twelve_data_client import TwelveDataClient


async def main():
    client = TwelveDataClient()
    
    print("Testing US stock queries with Twelve Data...")
    print("=" * 50)
    
    # Test 1: AAPL
    print("\nTest 1: AAPL")
    try:
        stock = await client.fetch_stock("AAPL")
        if stock:
            print(f"✅ AAPL: ${stock.current_price} ({stock.data_source})")
        else:
            print("❌ AAPL: No data returned")
    except Exception as e:
        print(f"❌ AAPL Error: {e}")
    
    # Test 2: TSLA
    print("\nTest 2: TSLA")
    try:
        stock = await client.fetch_stock("TSLA")
        if stock:
            print(f"✅ TSLA: ${stock.current_price} ({stock.data_source})")
        else:
            print("❌ TSLA: No data returned")
    except Exception as e:
        print(f"❌ TSLA Error: {e}")
    
    # Test 3: MSFT
    print("\nTest 3: MSFT")
    try:
        stock = await client.fetch_stock("MSFT")
        if stock:
            print(f"✅ MSFT: ${stock.current_price} ({stock.data_source})")
        else:
            print("❌ MSFT: No data returned")
    except Exception as e:
        print(f"❌ MSFT Error: {e}")
    
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
