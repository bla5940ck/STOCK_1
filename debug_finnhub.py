#!/usr/bin/env python3
"""
Test Finnhub API with indices.
"""

import asyncio
import os
from src.integrations.finnhub_client import FinnhubClient

async def main():
    key = os.getenv("FINNHUB_API_KEY", "demo")
    print(f"Testing with API key: {key[:20]}...")
    
    client = FinnhubClient(api_key=key)
    
    # Test different symbol formats
    symbols_to_test = [
        "^GSPC",      # Standard format
        "GSPC",       # Without ^
        "%5EGSPC",    # URL encoded
    ]
    
    for symbol in symbols_to_test:
        print(f"\nTesting {symbol}...")
        quote = await client.fetch_quote(symbol)
        if quote:
            print(f"  ✅ Success: {quote}")
        else:
            print(f"  ❌ Failed")

asyncio.run(main())
