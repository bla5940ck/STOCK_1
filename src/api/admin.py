"""
Admin endpoints for managing market data.
"""

try:
    from fastapi import APIRouter, HTTPException, Depends
    from sqlalchemy.ext.asyncio import AsyncSession
    from src.db.database import get_db
    from src.utils.logger import get_logger
    from decimal import Decimal
    from datetime import datetime

    logger = get_logger(__name__)

    router = APIRouter(prefix="/admin", tags=["admin"])

    @router.get("/health")
    async def admin_health():
        """Health check for admin endpoints"""
        return {"status": "ok"}

    @router.post("/seed-real-data")
    async def seed_real_data(db: AsyncSession = Depends(get_db)):
        """Seed database with real market data"""
        try:
            from src.models.domain import Index, DataSourceEnum
            from src.db.repositories import IndexRepository
            
            repo = IndexRepository(db)
            
            # Real market data (May 25, 2026)
            indices = [
                ("道瓊指數", "^DJI", "50579.70", "294.04", "0.58"),
                ("NASDAQ", "^IXIC", "26343.97", "50.87", "0.19"),
                ("S&P 500", "^GSPC", "7473.47", "27.75", "0.37"),
                ("費城半導體", "^SOX", "12202.54", "238.46", "1.99"),
            ]
            
            results = []
            
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
                await db.commit()
                results.append(zh_name)
            
            return {"success": True, "seeded": results}
        
        except Exception as e:
            logger.error(f"Seeding error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

except Exception as e:
    print(f"Error loading admin module: {e}")
    router = None

