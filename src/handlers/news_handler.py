"""
Handler for economic news queries.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from src.services.news_service import NewsService
from src.utils.formatters import format_news_message, format_error_message
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def handle_news_query(db: AsyncSession) -> dict:
    """
    Handle general economic news query.
    
    Fetches latest economic and market news articles.
    
    Args:
        db: Database session
        
    Returns:
        Dict with:
        - 'success': bool
        - 'message': str (formatted message for LINE)
        - 'error_code': str (on failure)
        - 'error_message': str (on failure)
    """
    news_service = NewsService(db)
    
    try:
        # Fetch economic news
        result = await news_service.fetch_economic_news(limit=5)
        
        if not result.get("success"):
            error_code = result.get("error_code", "E003_API_ERROR")
            error_message = result.get("error_message", "無法取得新聞數據")
            
            logger.warning(f"News query failed: {error_code}")
            
            return {
                "success": False,
                "error_code": error_code,
                "message": format_error_message(error_code, error_message),
            }

        articles = result.get("data", [])
        
        # Format message for LINE
        message = format_news_message(articles)
        
        logger.info(f"News query successful, {len(articles)} articles returned")
        
        return {
            "success": True,
            "message": message,
            "article_count": len(articles),
            "source": result.get("source"),
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in news handler: {e}")
        return {
            "success": False,
            "error_code": "E999_INTERNAL_ERROR",
            "message": format_error_message("E999_INTERNAL_ERROR", "系統內部錯誤，請稍後重試。"),
        }
    finally:
        await news_service.close()
