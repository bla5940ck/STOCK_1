"""
Handler for stock queries.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from src.services.market_data import MarketDataService
from src.services.news_service import NewsService
from src.utils.formatters import format_stock_message, format_error_message
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def handle_stock_query(db: AsyncSession, stock_code: str) -> dict:
    """
    Handle stock query (individual stock code).
    
    Fetches stock price data and related news articles.
    
    Args:
        db: Database session
        stock_code: Stock code (e.g., "AAPL")
        
    Returns:
        Dict with:
        - 'success': bool
        - 'message': str (formatted message for LINE)
        - 'error_code': str (on failure)
        - 'error_message': str (on failure)
    """
    market_service = MarketDataService(db)
    news_service = NewsService(db)
    
    try:
        # Fetch stock data
        stock_result = await market_service.get_stock(stock_code)
        
        if not stock_result.get("success"):
            error_code = stock_result.get("error_code", "E003_API_ERROR")
            error_message = stock_result.get("error_message", "無法取得股票數據")
            
            logger.warning(f"Stock query failed: {error_code}")
            
            return {
                "success": False,
                "error_code": error_code,
                "message": format_error_message(error_code, error_message),
            }

        stock = stock_result.get("data")
        
        # Fetch related news
        news_result = await news_service.fetch_related_news(stock_code, limit=3)
        news_articles = news_result.get("data", []) if news_result.get("success") else []
        
        # Format message for LINE
        message = format_stock_message(stock, news_articles)
        
        logger.info(f"Stock query successful for {stock_code}")
        
        return {
            "success": True,
            "message": message,
            "stock": stock,
            "news_count": len(news_articles),
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in stock handler: {e}")
        return {
            "success": False,
            "error_code": "E999_INTERNAL_ERROR",
            "message": format_error_message("E999_INTERNAL_ERROR", "系統內部錯誤，請稍後重試。"),
        }
    finally:
        await market_service.close()
        await news_service.close()
