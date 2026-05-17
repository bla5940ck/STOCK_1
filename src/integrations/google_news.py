"""
Google News RSS integration for fetching financial news articles.
"""

import aiohttp
import asyncio
import feedparser
from datetime import datetime, timedelta
from typing import List, Optional
from xml.etree import ElementTree as ET

from src.models.domain import NewsArticle, DataSourceEnum
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GoogleNewsClient:
    """Google News RSS client for fetching stock-related news"""

    BASE_URL = "https://news.google.com/rss/search"
    TIMEOUT = 10.0  # 10 second timeout per spec
    
    # RSS query keywords for different news types
    NEWS_QUERIES = {
        "stock": "stock market",
        "economic": "fed interest rate inflation",
        "earnings": "earnings report",
        "tech": "technology sector",
        "finance": "financial news",
    }

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def fetch_news(
        self,
        query: str = "stock",
        limit: int = 5,
        sort_by: str = "recent"
    ) -> List[NewsArticle]:
        """
        Fetch news from Google News RSS feed.
        
        Args:
            query: Search query (stock, economic, earnings, etc.)
            limit: Maximum number of articles to fetch
            sort_by: Sort order (recent, relevant)
            
        Returns:
            List of NewsArticle objects
        """
        session = await self._get_session()
        
        # Build RSS feed URL
        search_term = self.NEWS_QUERIES.get(query, query)
        params = {
            "q": search_term,
            "hl": "en",
            "gl": "US",
        }

        try:
            async with session.get(
                self.BASE_URL,
                params=params,
                timeout=aiohttp.ClientTimeout(total=self.TIMEOUT),
            ) as response:
                if response.status != 200:
                    logger.error(f"Google News API error: {response.status}")
                    return []

                feed_content = await response.text()
                return await self._parse_feed(feed_content, query, limit)

        except asyncio.TimeoutError:
            logger.warning(f"Google News timeout for query: {query}")
            return []
        except aiohttp.ClientError as e:
            logger.warning(f"Google News connection error: {e}")
            return []

    async def fetch_stock_news(
        self,
        stock_code: str,
        limit: int = 5,
    ) -> List[NewsArticle]:
        """
        Fetch news related to specific stock.
        
        Args:
            stock_code: Stock code (e.g., "AAPL")
            limit: Maximum number of articles
            
        Returns:
            List of NewsArticle objects
        """
        session = await self._get_session()
        
        params = {
            "q": stock_code,
            "hl": "en",
            "gl": "US",
        }

        try:
            async with session.get(
                self.BASE_URL,
                params=params,
                timeout=aiohttp.ClientTimeout(total=self.TIMEOUT),
            ) as response:
                if response.status != 200:
                    logger.error(f"Google News API error for {stock_code}: {response.status}")
                    return []

                feed_content = await response.text()
                return await self._parse_feed(
                    feed_content,
                    stock_code,
                    limit,
                    related_stocks=[stock_code]
                )

        except asyncio.TimeoutError:
            logger.warning(f"Google News timeout for {stock_code}")
            return []
        except aiohttp.ClientError as e:
            logger.warning(f"Google News connection error for {stock_code}: {e}")
            return []

    async def _parse_feed(
        self,
        feed_content: str,
        query: str,
        limit: int,
        related_stocks: Optional[List[str]] = None,
    ) -> List[NewsArticle]:
        """
        Parse Google News RSS feed.
        
        Args:
            feed_content: RSS feed XML content
            query: Search query used
            limit: Maximum articles to return
            related_stocks: Stocks related to articles
            
        Returns:
            List of NewsArticle objects
        """
        articles = []

        try:
            # Parse RSS feed using feedparser
            feed = feedparser.parse(feed_content)
            
            if "entries" not in feed:
                logger.warning(f"No entries in feed for query: {query}")
                return []

            for entry in feed.entries[:limit]:
                try:
                    article = self._parse_entry(entry, query, related_stocks)
                    if article:
                        articles.append(article)
                except Exception as e:
                    logger.warning(f"Failed to parse entry: {e}")
                    continue

            logger.info(f"Parsed {len(articles)} articles for query: {query}")
            return articles

        except Exception as e:
            logger.error(f"Failed to parse feed: {e}")
            return []

    def _parse_entry(
        self,
        entry,
        query: str,
        related_stocks: Optional[List[str]] = None,
    ) -> Optional[NewsArticle]:
        """
        Parse individual RSS entry to NewsArticle.
        
        Args:
            entry: RSS entry object
            query: Original search query
            related_stocks: Related stock codes
            
        Returns:
            NewsArticle object or None if parsing fails
        """
        try:
            # Extract fields
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            link = entry.get("link", "")
            published = entry.get("published", "")
            source = entry.get("source", {}).get("title", "Unknown")

            if not title or not summary:
                return None

            # Truncate summary to 150 characters
            if len(summary) > 150:
                summary = summary[:147] + "..."

            # Parse published date
            published_at = self._parse_date(published)
            if not published_at:
                published_at = datetime.utcnow()

            # Generate unique article ID
            article_id = f"news_{hash(title + link) % 1000000}"

            # Determine category and relevance
            category = self._categorize_article(title, summary, query)
            relevance_score = self._calculate_relevance(title, summary, query)

            return NewsArticle(
                id=article_id,
                title=title,
                summary=summary,
                source=source,
                url=link,
                published_at=published_at,
                category=category,
                related_stocks=related_stocks,
                relevance_score=relevance_score,
                fetched_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.warning(f"Failed to parse entry: {e}")
            return None

    def _parse_date(self, date_string: str) -> Optional[datetime]:
        """Parse date from RSS entry"""
        try:
            # Try RFC 2822 format
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_string)
        except Exception:
            try:
                # Try ISO format
                return datetime.fromisoformat(date_string.replace("Z", "+00:00"))
            except Exception:
                logger.warning(f"Could not parse date: {date_string}")
                return None

    def _categorize_article(
        self,
        title: str,
        summary: str,
        query: str
    ) -> str:
        """Categorize article based on content"""
        text = f"{title} {summary}".lower()

        if any(word in text for word in ["fed", "interest rate", "inflation", "monetary"]):
            return "economic"
        elif any(word in text for word in ["earnings", "revenue", "profit", "guidance"]):
            return "earnings"
        elif any(word in text for word in ["ipo", "listing", "acquisition", "merger"]):
            return "corporate"
        elif any(word in text for word in ["technical", "analysis", "chart", "resistance"]):
            return "technical"
        else:
            return "market"

    def _calculate_relevance(
        self,
        title: str,
        summary: str,
        query: str
    ) -> float:
        """Calculate relevance score (0-1)"""
        text = f"{title} {summary}".lower()
        query_terms = query.lower().split()

        matches = sum(1 for term in query_terms if term in text)
        max_matches = len(query_terms)

        if max_matches == 0:
            return 0.5

        # Title matches are worth more
        title_matches = sum(1 for term in query_terms if term in title.lower())
        
        relevance = (matches / max_matches) * 0.7 + (title_matches / max_matches) * 0.3

        return min(1.0, max(0.0, relevance))
