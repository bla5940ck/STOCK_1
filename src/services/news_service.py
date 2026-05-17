"""
News service for fetching and filtering stock-related news articles.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.domain import NewsArticle
from src.integrations.google_news import GoogleNewsClient
from src.utils.cache import CacheManager, CacheKeyBuilder, CachePolicies
from src.utils.logger import get_logger
from src.db.repositories import NewsArticleRepository

logger = get_logger(__name__)


class NewsService:
    """Service for fetching, filtering, and caching news articles"""

    def __init__(self, db: AsyncSession):
        """
        Initialize news service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.cache_manager = CacheManager(db)
        self.news_repo = NewsArticleRepository(db)
        self.google_news_client = GoogleNewsClient()

    async def close(self):
        """Clean up resources"""
        await self.google_news_client.close()

    async def fetch_related_news(
        self,
        stock_code: str,
        limit: int = 5,
    ) -> dict:
        """
        Fetch news related to specific stock with caching.
        
        Args:
            stock_code: Stock code (e.g., "AAPL")
            limit: Maximum number of articles
            
        Returns:
            Dict with:
            - 'success': bool
            - 'data': List[NewsArticle] (on success)
            - 'error_code': str (on failure)
            - 'error_message': str (on failure)
        """
        cache_key = CacheKeyBuilder.stock_news(stock_code)
        
        # Step 1: Check cache
        cached_data = await self.cache_manager.get(cache_key)
        if cached_data:
            logger.info(f"Returning {stock_code} news from cache")
            return {
                "success": True,
                "data": [NewsArticle(**article) for article in cached_data["articles"]],
                "source": "cache",
            }

        # Step 2: Fetch from Google News
        try:
            logger.info(f"Fetching news for {stock_code} from Google News")
            articles = await self.google_news_client.fetch_stock_news(
                stock_code,
                limit=limit * 2,  # Fetch more to filter
            )
            
            if not articles:
                logger.warning(f"No news found for {stock_code}")
                return {
                    "success": False,
                    "error_code": "E003_API_ERROR",
                    "error_message": f"無法找到 {stock_code} 的相關新聞，請稍後重試。",
                }

            # Filter and rank by relevance
            filtered_articles = self._filter_and_rank(articles, stock_code)[:limit]

            # Truncate summaries to 150 chars
            for article in filtered_articles:
                article.summary = self._truncate_summary(article.summary, 150)

            # Cache successful result
            cache_data = {
                "articles": [article.dict() for article in filtered_articles]
            }
            await self.cache_manager.set(
                cache_key,
                cache_data,
                "news_stock",
                CachePolicies.STOCK_NEWS_TTL_HOURS * 60,
            )

            logger.info(f"Successfully fetched {len(filtered_articles)} articles for {stock_code}")

            return {
                "success": True,
                "data": filtered_articles,
                "source": "google_news",
            }

        except Exception as e:
            logger.error(f"Error fetching news for {stock_code}: {e}")
            
            # Try stale cache as fallback
            try:
                cached_data = await self.cache_manager.get(cache_key)
                if cached_data:
                    logger.info(f"Returning stale cached news for {stock_code}")
                    return {
                        "success": True,
                        "data": [NewsArticle(**article) for article in cached_data["articles"]],
                        "source": "stale_cache",
                        "warning": "新聞數據可能已過期",
                    }
            except Exception:
                pass

            return {
                "success": False,
                "error_code": "E003_API_ERROR",
                "error_message": f"無法從 Google News 取得 {stock_code} 相關新聞，請稍後重試。",
            }

    async def fetch_economic_news(
        self,
        limit: int = 5,
    ) -> dict:
        """
        Fetch general economic news.
        
        Args:
            limit: Maximum number of articles
            
        Returns:
            Dict with success status and news articles or error
        """
        cache_key = CacheKeyBuilder.economic_news()
        
        # Check cache
        cached_data = await self.cache_manager.get(cache_key)
        if cached_data:
            logger.info("Returning economic news from cache")
            return {
                "success": True,
                "data": [NewsArticle(**article) for article in cached_data["articles"]],
                "source": "cache",
            }

        # Fetch from Google News
        try:
            logger.info("Fetching economic news from Google News")
            articles = await self.google_news_client.fetch_news(
                "economic",
                limit=limit * 2,
            )
            
            if not articles:
                return {
                    "success": False,
                    "error_code": "E003_API_ERROR",
                    "error_message": "無法找到經濟新聞，請稍後重試。",
                }

            filtered_articles = articles[:limit]

            # Truncate summaries
            for article in filtered_articles:
                article.summary = self._truncate_summary(article.summary, 150)

            # Cache
            cache_data = {
                "articles": [article.dict() for article in filtered_articles]
            }
            await self.cache_manager.set(
                cache_key,
                cache_data,
                "news_economic",
                CachePolicies.ECONOMIC_NEWS_TTL_HOURS * 60,
            )

            return {
                "success": True,
                "data": filtered_articles,
                "source": "google_news",
            }

        except Exception as e:
            logger.error(f"Error fetching economic news: {e}")
            
            return {
                "success": False,
                "error_code": "E003_API_ERROR",
                "error_message": "無法從 Google News 取得經濟新聞，請稍後重試。",
            }

    def _filter_and_rank(
        self,
        articles: List[NewsArticle],
        stock_code: str,
    ) -> List[NewsArticle]:
        """
        Filter and rank articles by relevance.
        
        Args:
            articles: List of articles
            stock_code: Stock code to filter for
            
        Returns:
            Sorted list of articles by relevance
        """
        # Filter articles that mention the stock code
        filtered = [
            article for article in articles
            if stock_code.lower() in article.title.lower() or
               stock_code.lower() in (article.summary or "").lower()
        ]

        # If less than half of articles mention stock code, include top articles anyway
        if len(filtered) < len(articles) / 2:
            filtered = sorted(articles, key=lambda a: a.relevance_score or 0, reverse=True)

        # Sort by relevance score
        filtered.sort(key=lambda a: a.relevance_score or 0, reverse=True)

        return filtered

    def _truncate_summary(self, text: str, max_length: int = 150) -> str:
        """
        Truncate summary to max length while preserving sentence boundaries.
        
        Args:
            text: Text to truncate
            max_length: Maximum length
            
        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text

        # Find last sentence boundary before max_length
        truncated = text[:max_length]
        
        # Try to find sentence boundary (。, !, ?)
        for boundary in ["。", "！", "？", ".", "!", "?"]:
            last_boundary = truncated.rfind(boundary)
            if last_boundary > max_length * 0.8:  # Within 80% of target length
                return truncated[:last_boundary + 1]

        # If no boundary found, just truncate and add ellipsis
        return truncated.rstrip() + "…"
