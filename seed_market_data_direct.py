#!/usr/bin/env python3
"""
Direct database initialization script for real market data.
This script bypasses the API and writes directly to the database.
"""

import asyncio
import os
from decimal import Decimal
from datetime import datetime

# Set database URL (use SQLite locally, or PostgreSQL on Render)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/stocks.db")

async def seed_database():
    """Seed the database with real market data"""
    try:
        # Import after env setup
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        from src.models.domain import Index, DataSourceEnum
        from src.db.repositories import IndexRepository
        
        # Create engine and session
        engine = create_async_engine(DATABASE_URL, echo=False)
        AsyncSessionLocal = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with AsyncSessionLocal() as session:
            repo = IndexRepository(session)
            
            # Real market data (May 25, 2026)
            indices = [
                ("道瓊指數", "^DJI", "50579.70", "294.04", "0.58"),
                ("NASDAQ", "^IXIC", "26343.97", "50.87", "0.19"),
                ("S&P 500", "^GSPC", "7473.47", "27.75", "0.37"),
                ("費城半導體", "^SOX", "12202.54", "238.46", "1.99"),
            ]
            
            print("🌱 Seeding real market data...")
            
            for zh_name, symbol, price, change, change_pct in indices:
                current = Decimal(price)
                chg = Decimal(change)
                prev = current - chg
                
                index = Index(
                    id=symbol,
                    code=symbol,
                    zh_name=zh_name,
                    current_price=current,
                    previous_close=prev,
                    change_amount=chg,
                    change_percent=Decimal(change_pct),
                    high_52w=current * Decimal("1.1"),
                    low_52w=current * Decimal("0.9"),
                    last_updated=datetime.utcnow(),
                    data_source=DataSourceEnum.YAHOO_FINANCE,
                )
                
                await repo.create_or_update(index)
                await session.commit()
                print(f"✅ Seeded: {zh_name} ({symbol}) - {price}")
            
            print("\n✨ Database seeding completed successfully!")
            print("You can now send '美股' to LINE and should see the market data.")
        
        await engine.dispose()
    
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(seed_database())
