"""
Seed market data with real market values.
This is temporary data initialization - will be updated via API or scheduled jobs.
"""

import asyncio
from decimal import Decimal
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.database import Base, IndexData
from src.config import get_settings


async def seed_real_data():
    """Seed database with real market data"""
    
    settings = get_settings()
    
    # Create database session
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Real market data provided by user
    market_data = {
        "道瓊指數": {
            "symbol": "^DJI",
            "current": Decimal("50579.70"),
            "change": Decimal("294.04"),
            "change_percent": Decimal("0.58"),
        },
        "NASDAQ": {
            "symbol": "^IXIC",
            "current": Decimal("26343.97"),
            "change": Decimal("50.87"),
            "change_percent": Decimal("0.19"),
        },
        "S&P 500": {
            "symbol": "^GSPC",
            "current": Decimal("7473.47"),
            "change": Decimal("27.75"),
            "change_percent": Decimal("0.37"),
        },
        "費城半導體": {
            "symbol": "^SOX",
            "current": Decimal("12202.54"),
            "change": Decimal("238.46"),
            "change_percent": Decimal("1.99"),
        },
        "AMEX綜合": {
            "symbol": "^XAX",
            "current": Decimal("9021.43"),
            "change": Decimal("-48.74"),
            "change_percent": Decimal("-0.54"),
        },
        "羅素2000": {
            "symbol": "^RUT",
            "current": Decimal("2870.64"),
            "change": Decimal("27.19"),
            "change_percent": Decimal("0.96"),
        },
        "NASDAQ100": {
            "symbol": "^NDX",
            "current": Decimal("29481.64"),
            "change": Decimal("124.37"),
            "change_percent": Decimal("0.42"),
        },
        "NYSE科技100": {
            "symbol": "^NYK",
            "current": Decimal("10135.59"),
            "change": Decimal("147.26"),
            "change_percent": Decimal("1.47"),
        },
    }
    
    print("📊 Seeding market data...")
    
    for name, data in market_data.items():
        try:
            symbol = data["symbol"]
            current_price = data["current"]
            change_amount = data["change"]
            change_percent = data["change_percent"]
            previous_close = current_price - change_amount
            
            print(f"Processing {name} ({symbol})...")
            
            # Check if record exists
            existing = session.query(IndexData).filter_by(id=symbol).first()
            
            if existing:
                # Update existing record
                existing.current_price = current_price
                existing.previous_close = previous_close
                existing.change_amount = change_amount
                existing.change_percent = change_percent
                existing.last_updated = datetime.utcnow()
                print(f"  ✅ Updated: {current_price} ({change_percent}%)")
            else:
                # Create new record
                index_data = IndexData(
                    id=symbol,
                    code=symbol,
                    zh_name=name,
                    current_price=current_price,
                    previous_close=previous_close,
                    change_amount=change_amount,
                    change_percent=change_percent,
                    high_52w=current_price * Decimal("1.1"),  # Estimated
                    low_52w=current_price * Decimal("0.9"),   # Estimated
                    last_updated=datetime.utcnow(),
                    data_source="USER_PROVIDED",
                )
                session.add(index_data)
                print(f"  ✅ Created: {current_price} ({change_percent}%)")
        
        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue
    
    try:
        session.commit()
        print("\n✅ All data saved to database successfully!")
        print("\n Now you can:")
        print("  1. Send '美股' to LINE bot to see the data")
        print("  2. Call /admin/seed-indices to refresh with latest Yahoo Finance data")
    except Exception as e:
        session.rollback()
        print(f"❌ Database error: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    asyncio.run(seed_real_data())
