#!/usr/bin/env python3
"""Test the CNYES rating scraper locally"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def main():
    from integrations.tw_rating_scraper import TaiwanStockRatingScraper
    
    scraper = TaiwanStockRatingScraper()
    
    # Test with 2330 (TSMC)
    print("Testing 2330 (台積電)...")
    ratings = await scraper.get_analyst_ratings("2330")
    print(f"Result: {ratings}")
    print()
    
    # Test with 2454 (MediaTek)
    print("Testing 2454 (聯發科)...")
    ratings = await scraper.get_analyst_ratings("2454")
    print(f"Result: {ratings}")
    print()
    
    # Test with 2376 (技嘉)
    print("Testing 2376 (技嘉)...")
    ratings = await scraper.get_analyst_ratings("2376")
    print(f"Result: {ratings}")
    
    await scraper.close()

if __name__ == "__main__":
    asyncio.run(main())
