"""
Script to seed market data into database.
Run this locally to update the database with real market data.

Usage:
    python seed_market_data.py
"""

import asyncio
import yfinance as yf
from datetime import datetime
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.database import Base, IndexData
from src.config import get_settings


async def seed_indices():
    """Fetch real indices data and save to database"""
    
    settings = get_settings()
    
    # Create database session
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    symbols_info = {
        "^GSPC": "S&P 500",
        "^IXIC": "納斯達克綜合指數",
        "^SOX": "費城半導體指數",
    }
    
    print("📊 Fetching market data from Yahoo Finance...")
    
    for symbol, zh_name in symbols_info.items():
        try:
            print(f"\nFetching {symbol}...")
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")
            
            if hist is None or len(hist) == 0:
                print(f"⚠️  No data for {symbol}")
                continue
            
            # Get latest and previous data
            latest = hist.iloc[-1]
            previous = hist.iloc[-2] if len(hist) > 1 else latest
            
            current_price = Decimal(str(latest['Close']))
            previous_close = Decimal(str(previous['Close']))
            high_52w = Decimal(str(hist['High'].max()))
            low_52w = Decimal(str(hist['Low'].min()))
            
            change_amount = current_price - previous_close
            change_percent = (change_amount / previous_close * 100) if previous_close > 0 else Decimal("0")
            
            # Check if record exists
            existing = session.query(IndexData).filter_by(id=symbol).first()
            
            if existing:
                # Update existing record
                existing.current_price = current_price
                existing.previous_close = previous_close
                existing.change_amount = change_amount
                existing.change_percent = change_percent
                existing.high_52w = high_52w
                existing.low_52w = low_52w
                existing.last_updated = datetime.utcnow()
                print(f"✅ Updated {symbol}: {current_price}")
            else:
                # Create new record
                index_data = IndexData(
                    id=symbol,
                    code=symbol,
                    zh_name=zh_name,
                    current_price=current_price,
                    previous_close=previous_close,
                    change_amount=change_amount,
                    change_percent=change_percent,
                    high_52w=high_52w,
                    low_52w=low_52w,
                    last_updated=datetime.utcnow(),
                    data_source="YAHOO_FINANCE",
                )
                session.add(index_data)
                print(f"✅ Created {symbol}: {current_price}")
        
        except Exception as e:
            print(f"❌ Error fetching {symbol}: {e}")
            continue
    
    try:
        session.commit()
        print("\n✅ All data saved to database successfully!")
    except Exception as e:
        session.rollback()
        print(f"❌ Database error: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    asyncio.run(seed_indices())
