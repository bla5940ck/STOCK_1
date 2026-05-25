#!/usr/bin/env python3
"""
Quick test script for IEX Cloud API integration.

Usage:
  export IEX_CLOUD_TOKEN=your_token_here
  python test_iex_cloud.py
"""

import asyncio
import os
import sys
from decimal import Decimal

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.integrations.iex_cloud import IEXCloudClient


async def main():
    # Check if token is set
    token = os.getenv("IEX_CLOUD_TOKEN")
    if not token:
        print("❌ IEX_CLOUD_TOKEN not set!")
        print("\nTo use IEX Cloud:")
        print("1. Go to https://iexcloud.io/console/tokens")
        print("2. Sign up for free account (100 requests/month)")
        print("3. Copy your PUBLIC token")
        print("4. Set: export IEX_CLOUD_TOKEN=your_token_here")
        print("5. Or add to .env: IEX_CLOUD_TOKEN=your_token_here")
        return
    
    print(f"✅ IEX_CLOUD_TOKEN set: {token[:20]}...")
    
    # Test IEX Cloud client
    client = IEXCloudClient()
    
    print("\n📊 Testing index quotes...\n")
    
    symbols = ["^GSPC", "^IXIC", "^SOX"]
    quotes = await client.fetch_indices(symbols)
    
    if quotes:
        print(f"✅ Successfully fetched {len(quotes)} indices:\n")
        
        for symbol, quote in quotes.items():
            price = quote.get("latestPrice", "N/A")
            prev = quote.get("previousClose", "N/A")
            print(f"{symbol}:")
            print(f"  Current: {price}")
            print(f"  Previous Close: {prev}")
            print()
    else:
        print("❌ No quotes returned")


if __name__ == "__main__":
    asyncio.run(main())
