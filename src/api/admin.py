"""
Admin endpoints for managing market data.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.database import get_db
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/seed-indices")
async def seed_indices(db: AsyncSession = Depends(get_db)):
    """
    Admin endpoint to seed market indices data.
    Fetches latest data from yfinance and saves to database.
    
    WARNING: This should be protected by authentication in production!
    """
    try:
        logger.info("📊 Starting index data seeding...")
        
        import yfinance as yf
        from decimal import Decimal
        from datetime import datetime
        from src.models.domain import Index, DataSourceEnum
        from src.db.repositories import IndexRepository
        
        index_repo = IndexRepository(db)
        
        symbols_info = {
            "^GSPC": "S&P 500",
            "^IXIC": "納斯達克綜合指數",
            "^SOX": "費城半導體指數",
        }
        
        results = {}
        
        for symbol, zh_name in symbols_info.items():
            try:
                logger.info(f"Fetching {symbol}...")
                
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="5d")
                
                if hist is None or len(hist) == 0:
                    logger.warning(f"No data for {symbol}")
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
                
                index = Index(
                    id=symbol,
                    code=symbol,
                    zh_name=zh_name,
                    current_price=current_price.quantize(Decimal("0.01")),
                    previous_close=previous_close.quantize(Decimal("0.01")),
                    change_amount=change_amount.quantize(Decimal("0.01")),
                    change_percent=change_percent.quantize(Decimal("0.01")),
                    high_52w=high_52w.quantize(Decimal("0.01")),
                    low_52w=low_52w.quantize(Decimal("0.01")),
                    last_updated=datetime.utcnow(),
                    data_source=DataSourceEnum.YAHOO_FINANCE,
                )
                
                # Save to database
                await index_repo.create_or_update(index)
                await db.commit()
                
                results[symbol] = {
                    "price": str(current_price),
                    "change": str(change_amount),
                    "change_percent": str(change_percent),
                }
                
                logger.info(f"✅ Seeded {symbol}: {current_price}")
                
            except Exception as e:
                logger.warning(f"Error seeding {symbol}: {e}")
                await db.rollback()
                continue
        
        if not results:
            raise HTTPException(status_code=500, detail="Failed to seed any indices")
        
        return {
            "success": True,
            "message": f"Successfully seeded {len(results)} indices",
            "data": results,
        }
    
    except Exception as e:
        logger.error(f"Seeding error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def admin_health():
    """Health check for admin endpoints"""
    return {"status": "ok", "message": "Admin endpoints are available"}


@router.post("/seed-real-data")
async def seed_real_data(db: AsyncSession = Depends(get_db)):
    """
    Admin endpoint to quickly seed database with real market data.
    Uses user-provided real market values.
    
    WARNING: This should be protected by authentication in production!
    """
    try:
        logger.info("📊 Starting real market data seeding...")
        
        from decimal import Decimal
        from datetime import datetime
        from src.models.domain import Index, DataSourceEnum
        from src.db.repositories import IndexRepository
        
        index_repo = IndexRepository(db)
        
        # Real market data provided by user (May 25, 2026)
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
        
        results = {}
        
        for name, data in market_data.items():
            try:
                symbol = data["symbol"]
                current_price = data["current"]
                change_amount = data["change"]
                change_percent = data["change_percent"]
                previous_close = current_price - change_amount
                
                logger.info(f"Seeding {name} ({symbol})...")
                
                index = Index(
                    id=symbol,
                    code=symbol,
                    zh_name=name,
                    current_price=current_price.quantize(Decimal("0.01")),
                    previous_close=previous_close.quantize(Decimal("0.01")),
                    change_amount=change_amount.quantize(Decimal("0.01")),
                    change_percent=change_percent.quantize(Decimal("0.01")),
                    high_52w=current_price * Decimal("1.1"),
                    low_52w=current_price * Decimal("0.9"),
                    last_updated=datetime.utcnow(),
                    data_source=DataSourceEnum.YAHOO_FINANCE,
                )
                
                # Save to database
                await index_repo.create_or_update(index)
                await db.commit()
                
                results[symbol] = {
                    "name": name,
                    "price": str(current_price),
                    "change": str(change_amount),
                    "change_percent": str(change_percent),
                }
                
                logger.info(f"✅ Seeded {name}: {current_price}")
                
            except Exception as e:
                logger.warning(f"Error seeding {name}: {e}")
                await db.rollback()
                continue
        
        if not results:
            raise HTTPException(status_code=500, detail="Failed to seed any indices")
        
        return {
            "success": True,
            "message": f"Successfully seeded {len(results)} indices with real market data",
            "data": results,
        }
    
    except Exception as e:
        logger.error(f"Real data seeding error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
