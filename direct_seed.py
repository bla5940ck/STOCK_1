#!/usr/bin/env python3
"""
Direct database seeding script - bypasses FastAPI entirely
This can be run on Render via a one-time dyno or manually locally.
"""

import asyncio
import os
from decimal import Decimal
from datetime import datetime

async def seed():
    """Seed database directly"""
    try:
        # Set database URL
        db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/stocks.db")
        
        # Convert sqlite:// to sqlite+aiosqlite:// if needed
        if db_url.startswith("sqlite://"):
            db_url = db_url.replace("sqlite://", "sqlite+aiosqlite:///")
        
        print(f"Using database: {db_url}")
        
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        from src.models.database import Base
        from src.models.domain import Index, DataSourceEnum
        from src.db.repositories import IndexRepository
        
        # Create engine
        engine = create_async_engine(db_url, echo=False)
        
        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Create session factory
        AsyncSessionLocal = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        
        # Seed data
        async with AsyncSessionLocal() as session:
            repo = IndexRepository(session)
            
            indices = [
                ("道瓊指數", "^DJI", "50579.70", "294.04", "0.58"),
                ("NASDAQ", "^IXIC", "26343.97", "50.87", "0.19"),
                ("S&P 500", "^GSPC", "7473.47", "27.75", "0.37"),
                ("費城半導體", "^SOX", "12202.54", "238.46", "1.99"),
            ]
            
            for zh_name, symbol, price, change, change_pct in indices:
                current = Decimal(price)
                chg = Decimal(change)
                prev = current - chg
                chg_pct = Decimal(change_pct)
                
                index = Index(
                    id=symbol,
                    code=symbol,
                    zh_name=zh_name,
                    current_price=current,
                    previous_close=prev,
                    change_amount=chg,
                    change_percent=chg_pct,
                    high_52w=current * Decimal("1.1"),
                    low_52w=current * Decimal("0.9"),
                    last_updated=datetime.utcnow(),
                    data_source=DataSourceEnum.YAHOO_FINANCE,
                )
                
                await repo.create_or_update(index)
                await session.commit()
                print(f"✅ Seeded: {zh_name} ({symbol}) - {price}")
            
            print("\n✨ Database seeding completed!")
        
        await engine.dispose()
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    asyncio.run(seed())
