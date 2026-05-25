#!/usr/bin/env python3
"""
Auto-seed script that runs as part of Dockerfile initialization
This ensures database is populated on every Render deployment
"""

import asyncio
import os
import sys
from decimal import Decimal
from datetime import datetime

async def auto_seed():
    """Auto-seed database on startup"""
    try:
        db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/stocks.db")
        
        if db_url.startswith("sqlite://"):
            db_url = db_url.replace("sqlite://", "sqlite+aiosqlite:///")
        
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        
        print("[SEED] Creating async engine...")
        engine = create_async_engine(db_url, echo=False)
        
        print("[SEED] Creating tables...")
        async with engine.begin() as conn:
            from src.models.database import Base
            await conn.run_sync(Base.metadata.create_all)
        
        AsyncSessionLocal = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        async with AsyncSessionLocal() as session:
            from src.models.domain import Index, DataSourceEnum
            from src.db.repositories import IndexRepository
            
            repo = IndexRepository(session)
            
            # Check if data already exists
            existing = await repo.get_major_indices()
            if existing and len(existing) >= 2:
                print("[SEED] Data already exists, skipping...")
                await engine.dispose()
                return
            
            print("[SEED] Seeding market data...")
            
            indices = [
                ("道瓊指數", "^DJI", "50579.70", "294.04", "0.58"),
                ("NASDAQ", "^IXIC", "26343.97", "50.87", "0.19"),
                ("S&P 500", "^GSPC", "7473.47", "27.75", "0.37"),
                ("費城半導體", "^SOX", "12202.54", "238.46", "1.99"),
            ]
            
            count = 0
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
                print(f"[SEED] ✅ {zh_name} ({symbol})")
                count += 1
            
            print(f"[SEED] Seeded {count} indices")
        
        await engine.dispose()
        print("[SEED] ✨ Done!")
        
    except Exception as e:
        print(f"[SEED] Error: {e}")
        import traceback
        traceback.print_exc()
        # Don't exit with error - let app continue

if __name__ == "__main__":
    asyncio.run(auto_seed())
