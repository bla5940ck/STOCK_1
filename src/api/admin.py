"""
Admin endpoints for managing market data.
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/seed-indices")
async def seed_indices(db: AsyncSession):
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
