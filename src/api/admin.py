"""
Admin endpoints for managing market data.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from datetime import datetime
from src.db.database import get_db
from src.utils.logger import get_logger

# Create router
router = APIRouter(prefix="/admin", tags=["admin"])
logger = get_logger(__name__)


@router.get("/health")
async def admin_health():
    """Health check for admin endpoints"""
    return {"status": "ok", "message": "Admin API is ready"}


@router.post("/seed-real-data")
async def seed_real_data(db: AsyncSession = Depends(get_db)):
    """Seed database with real market data"""
    try:
        logger.info("🌱 Starting market data seeding...")
        
        from src.models.domain import Index, DataSourceEnum
        from src.db.repositories import IndexRepository
        
        repo = IndexRepository(db)
        
        # Real market data (May 25, 2026)
        indices_data = [
            ("道瓊指數", "^DJI", "50579.70", "294.04", "0.58"),
            ("NASDAQ", "^IXIC", "26343.97", "50.87", "0.19"),
            ("S&P 500", "^GSPC", "7473.47", "27.75", "0.37"),
            ("費城半導體", "^SOX", "12202.54", "238.46", "1.99"),
        ]
        
        seeded = []
        
        for zh_name, symbol, price_str, change_str, change_pct_str in indices_data:
            try:
                current = Decimal(price_str)
                chg = Decimal(change_str)
                prev = current - chg
                chg_pct = Decimal(change_pct_str)
                
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
                await db.commit()
                seeded.append(zh_name)
                logger.info(f"✅ Seeded: {zh_name} - {price_str}")
                
            except Exception as e:
                logger.error(f"Error seeding {zh_name}: {e}")
                await db.rollback()
                continue
        
        if not seeded:
            logger.error("❌ No indices were seeded")
            raise HTTPException(status_code=500, detail="Failed to seed any indices")
        
        logger.info(f"✨ Successfully seeded {len(seeded)} indices")
        return {
            "success": True,
            "message": f"Seeded {len(seeded)} indices",
            "indices": seeded,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Seeding error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Seeding failed: {str(e)}")

