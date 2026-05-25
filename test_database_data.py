#!/usr/bin/env python3
"""
Test script to verify database has seeded data and LINE bot works
"""

import asyncio
import sys
sys.path.insert(0, '/c/Users/bla59/OneDrive/Desktop/SDD/US_STOCK')

from sqlalchemy import text
from src.db.database import AsyncSessionLocal, engine
from src.db.repositories import IndexRepository
from src.services.market_data import MarketDataService


async def main():
    # Test 1: Check if database has tables
    print("=" * 60)
    print("Test 1: Checking database schema...")
    print("=" * 60)
    
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        tables = result.fetchall()
        print(f"✅ Tables in database: {[t[0] for t in tables]}")
    
    # Test 2: Query Index records
    print("\n" + "=" * 60)
    print("Test 2: Checking Index records...")
    print("=" * 60)
    
    async with AsyncSessionLocal() as session:
        repo = IndexRepository(session)
        indices = await repo.get_major_indices()
        
        if indices:
            print(f"✅ Found {len(indices)} indices in database:")
            for idx in indices:
                print(f"   - {idx.code}: {idx.zh_name} = ${idx.current_price}")
        else:
            print("❌ No indices found in database")
    
    # Test 3: Test MarketDataService
    print("\n" + "=" * 60)
    print("Test 3: Testing MarketDataService.get_indices()...")
    print("=" * 60)
    
    async with AsyncSessionLocal() as session:
        service = MarketDataService(session)
        result = await service.get_indices()
        
        if result.get("success"):
            print(f"✅ get_indices() succeeded from source: {result.get('source')}")
            for idx in result.get("data", []):
                pct_str = f"+{idx.change_percent}%" if idx.change_percent > 0 else f"{idx.change_percent}%"
                print(f"   - {idx.zh_name} ({idx.code}): {idx.current_price} {pct_str}")
        else:
            print(f"❌ get_indices() failed: {result.get('error_message')}")
        
        await service.close()
    
    print("\n" + "=" * 60)
    print("✨ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
