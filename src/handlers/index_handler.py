"""
Handler for index queries (美股 keyword).
"""

from sqlalchemy.ext.asyncio import AsyncSession

from src.services.market_data import MarketDataService
from src.utils.formatters import format_index_message
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def handle_index_query(db: AsyncSession) -> dict:
    """
    Handle index query (美股 keyword).
    
    Fetches S&P 500, NASDAQ, and Philadelphia Semiconductor indices
    and formats them for LINE display.
    
    Args:
        db: Database session
        
    Returns:
        Dict with:
        - 'success': bool
        - 'message': str (formatted message for LINE)
        - 'error_code': str (on failure)
        - 'error_message': str (on failure)
    """
    service = MarketDataService(db)
    
    try:
        # Fetch indices with fallback logic
        result = await service.get_indices()
        
        if result.get("success"):
            indices = result.get("data", [])
            
            # Format message for LINE
            message = format_index_message(indices)
            
            logger.info(f"Index query successful, {len(indices)} indices returned")
            
            return {
                "success": True,
                "message": message,
                "count": len(indices),
                "source": result.get("source"),
            }
        else:
            # Return error message
            error_code = result.get("error_code", "E003_API_ERROR")
            error_message = result.get("error_message", "無法取得指數數據")
            
            logger.warning(f"Index query failed: {error_code}")
            
            return {
                "success": False,
                "error_code": error_code,
                "message": f"❌ {error_message}",
            }
            
    except Exception as e:
        logger.error(f"Unexpected error in index handler: {e}")
        return {
            "success": False,
            "error_code": "E999_INTERNAL_ERROR",
            "message": "❌ 系統內部錯誤，請稍後重試。",
        }
    finally:
        await service.close()
