"""
Handler for Taiwan stock direct queries (e.g., 台積電, 2330).
Supports dynamic stock lookup from live data sources.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from src.integrations.tw_stock_dynamic import get_taiwan_stock_client
from src.integrations.tw_stock_integration import TaiwanStockClient
from src.services.news_service import NewsService
from src.services.fundamental_data import FundamentalDataService
from src.utils.formatters import format_tw_stock_price_message, format_error_message
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def handle_tw_stock_search(db: AsyncSession, query: str) -> dict:
    """
    Handle Taiwan stock search by name or code.
    
    Features:
    - Search by stock code (e.g., "2330")
    - Search by Chinese name (e.g., "台積電", "健策")
    - Automatic fuzzy matching for similar names
    - Fetches real-time price and related news
    
    Args:
        db: Database session
        query: Stock code (e.g., "2330") or name (e.g., "台積電")
        
    Returns:
        Dict with:
        - 'success': bool
        - 'message': str (formatted message for LINE)
        - 'error_code': str (on failure)
    """
    try:
        # Get dynamic client for live Taiwan stock lookup
        dynamic_client = await get_taiwan_stock_client()
        tw_client = TaiwanStockClient()
        news_service = NewsService(db)
        fundamental_service = FundamentalDataService()
        
        # Search for stock by code or name
        logger.info(f"Searching Taiwan stock: {query}")
        stock_info = await dynamic_client.search_stock(query)
        
        if not stock_info:
            logger.warning(f"Taiwan stock not found: {query}")
            return {
                "success": False,
                "error_code": "E004_STOCK_NOT_FOUND",
                "message": format_error_message("E004_STOCK_NOT_FOUND", f"找不到台股標的：{query}"),
            }

        stock_code = stock_info["code"]
        logger.info(f"Found Taiwan stock: {stock_code} ({stock_info.get('zh_name', '')})")

        # Fetch real-time stock data
        stock_data = await tw_client.fetch_tw_stock(stock_code)
        
        if not stock_data:
            logger.warning(f"Failed to fetch Taiwan stock data: {stock_code}")
            return {
                "success": False,
                "error_code": "E003_API_ERROR",
                "message": format_error_message("E003_API_ERROR", f"無法取得台股數據：{stock_code}"),
            }

        # Try to fetch fundamental data (PE, dividend yield) - optional
        fundamentals = None
        try:
            from decimal import Decimal
            current_price = Decimal(str(stock_data.get("current_price", 0)))
            fundamentals = await fundamental_service.get_tw_stock_fundamentals(stock_code, current_price)
            logger.info(f"Fetched Taiwan stock fundamentals for {stock_code}")
        except Exception as e:
            logger.warning(f"Could not fetch Taiwan stock fundamentals for {stock_code}: {e}")

        # Fetch related news (use Chinese name)
        company_name = stock_info.get("zh_name", stock_code)
        news_result = await news_service.fetch_related_news(company_name, limit=3)
        news_articles = news_result.get("data", []) if news_result.get("success") else []

        # Format message for LINE
        message = format_tw_stock_price_message(stock_data, news_articles, fundamentals)

        logger.info(f"Taiwan stock query successful for {stock_code}")

        return {
            "success": True,
            "message": message,
            "stock_code": stock_code,
            "news_count": len(news_articles),
        }

    except Exception as e:
        logger.error(f"Unexpected error in Taiwan stock search handler: {e}")
        return {
            "success": False,
            "error_code": "E999_INTERNAL_ERROR",
            "message": format_error_message("E999_INTERNAL_ERROR", "系統內部錯誤，請稍後重試。"),
        }
    finally:
        await tw_client.close()
        await news_service.close()
        await fundamental_service.close()
