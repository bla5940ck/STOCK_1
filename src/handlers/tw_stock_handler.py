"""
Handler for Taiwan stock queries.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from src.services.tw_stock_service import TaiwanStockService
from src.utils.formatters import format_tw_stock_message, format_error_message
from src.utils.validators import validate_stock_code
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def handle_tw_stock_query(db: AsyncSession, us_code: str) -> dict:
    """
    Handle Taiwan stock correlation query.
    
    Fetches Taiwan stocks related to the given US stock code.
    
    Args:
        db: Database session
        us_code: US stock code (e.g., "AAPL")
        
    Returns:
        Dict with:
        - 'success': bool
        - 'message': str (formatted message for LINE)
        - 'error_code': str (on failure)
    """
    tw_stock_service = TaiwanStockService(db)
    
    try:
        # Validate stock code
        try:
            us_code = validate_stock_code(us_code)
        except Exception as e:
            logger.warning(f"Taiwan stock query: invalid code {us_code}: {e}")
            return {
                "success": False,
                "error_code": "E002_INVALID_INPUT",
                "message": format_error_message("E002_INVALID_INPUT", "股票代碼無效"),
            }

        # Fetch related Taiwan stocks
        result = await tw_stock_service.get_related_tw_stocks(us_code, limit=10)
        
        if not result.get("success"):
            error_code = result.get("error_code", "E005_TW_STOCK_FETCH_ERROR")
            error_message = result.get("error_message", "無法取得台股相關標的")
            
            logger.warning(f"Taiwan stock query failed: {error_code}")
            
            return {
                "success": False,
                "error_code": error_code,
                "message": format_error_message(error_code, error_message),
            }

        tw_stocks = result.get("data", [])

        if not tw_stocks:
            # No related Taiwan stocks found
            message = f"🔗 無法找到 {us_code} 相關的台股標的。\n\n目前資料庫中尚無相關記錄。"
            
            logger.info(f"No Taiwan stocks found for {us_code}")
            
            return {
                "success": True,
                "message": message,
                "tw_stock_count": 0,
            }

        # Format message for LINE
        message = format_tw_stock_message(us_code, tw_stocks)
        
        logger.info(f"Taiwan stock query successful for {us_code}")
        
        return {
            "success": True,
            "message": message,
            "tw_stock_count": len(tw_stocks),
            "source": result.get("source"),
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in Taiwan stock handler: {e}")
        return {
            "success": False,
            "error_code": "E999_INTERNAL_ERROR",
            "message": format_error_message("E999_INTERNAL_ERROR", "系統內部錯誤，請稍後重試。"),
        }
    finally:
        await tw_stock_service.close()
