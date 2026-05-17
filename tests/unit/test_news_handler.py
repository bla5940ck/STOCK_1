"""
Unit tests for news handler (Phase 5 - US3).
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from src.models.domain import NewsArticle, DataSourceEnum
from src.handlers.news_handler import handle_news_query


class TestNewsHandlerUS3:
    """Tests for economic news handler (Phase 5)"""

    @pytest.fixture
    def sample_economic_news(self):
        """Sample economic news articles"""
        return [
            NewsArticle(
                id="news_econ_001",
                title="聯準會升息決定確認",
                summary="美國聯邦準備委員會宣佈升息 0.5%，以控制通脹，市場反應積極，股市上漲 2%...",
                source="路透社",
                url="https://example.com/news1",
                published_at=datetime(2026, 5, 17),
                category="economic",
                related_stocks=["SPY", "QQQ"],
                relevance_score=0.95,
                fetched_at=datetime.utcnow(),
            ),
            NewsArticle(
                id="news_econ_002",
                title="美國失業率創新低",
                summary="美國 4 月失業率下降至 3.4%，創 50 年新低，勞動力市場供應緊張...",
                source="美聯社",
                url="https://example.com/news2",
                published_at=datetime(2026, 5, 16),
                category="economic",
                related_stocks=["DIA"],
                relevance_score=0.88,
                fetched_at=datetime.utcnow(),
            ),
            NewsArticle(
                id="news_econ_003",
                title="供應鏈緩解推動製造業恢復",
                summary="隨著全球供應鏈正常化，美國製造業指數反彈至 55.2，超過預期...",
                source="財經新聞",
                url="https://example.com/news3",
                published_at=datetime(2026, 5, 15),
                category="economic",
                related_stocks=["IYM"],
                relevance_score=0.82,
                fetched_at=datetime.utcnow(),
            ),
        ]

    @pytest.mark.asyncio
    async def test_handle_news_query_success(self, test_db, sample_economic_news):
        """Test successful economic news query"""
        with patch("src.handlers.news_handler.NewsService") as mock_news_service:
            news_service_instance = AsyncMock()
            news_service_instance.fetch_economic_news.return_value = {
                "success": True,
                "data": sample_economic_news,
                "source": "google_news",
            }
            news_service_instance.close = AsyncMock()
            mock_news_service.return_value = news_service_instance

            result = await handle_news_query(test_db)

            assert result["success"] is True
            assert "message" in result
            assert result["article_count"] == 3
            
            # Verify message contains news content
            message = result["message"]
            assert "聯準會" in message or "失業率" in message
            assert "新聞" in message or "經濟" in message

    @pytest.mark.asyncio
    async def test_handle_news_query_partial_results(self, test_db):
        """Test news query with fewer than expected articles"""
        sample_news = [
            NewsArticle(
                id="single_news",
                title="單一經濟新聞",
                summary="這是唯一可用的新聞...",
                source="新聞來源",
                url="https://example.com",
                published_at=datetime.utcnow(),
                category="economic",
                related_stocks=[],
                relevance_score=0.80,
                fetched_at=datetime.utcnow(),
            )
        ]
        
        with patch("src.handlers.news_handler.NewsService") as mock_news_service:
            news_service_instance = AsyncMock()
            news_service_instance.fetch_economic_news.return_value = {
                "success": True,
                "data": sample_news,
                "source": "google_news",
            }
            news_service_instance.close = AsyncMock()
            mock_news_service.return_value = news_service_instance

            result = await handle_news_query(test_db)

            assert result["success"] is True
            assert result["article_count"] == 1

    @pytest.mark.asyncio
    async def test_handle_news_query_empty_results(self, test_db):
        """Test news query with no articles available"""
        with patch("src.handlers.news_handler.NewsService") as mock_news_service:
            news_service_instance = AsyncMock()
            news_service_instance.fetch_economic_news.return_value = {
                "success": True,
                "data": [],
                "source": "google_news",
            }
            news_service_instance.close = AsyncMock()
            mock_news_service.return_value = news_service_instance

            result = await handle_news_query(test_db)

            assert result["success"] is True
            # Should still have a message, even if no articles
            assert "message" in result

    @pytest.mark.asyncio
    async def test_handle_news_query_api_error(self, test_db):
        """Test handling of API errors during news fetch"""
        with patch("src.handlers.news_handler.NewsService") as mock_news_service:
            news_service_instance = AsyncMock()
            news_service_instance.fetch_economic_news.return_value = {
                "success": False,
                "error_code": "E003_API_ERROR",
                "error_message": "無法連接到新聞 API",
            }
            news_service_instance.close = AsyncMock()
            mock_news_service.return_value = news_service_instance

            result = await handle_news_query(test_db)

            assert result["success"] is False
            assert "error_code" in result
            assert "message" in result

    @pytest.mark.asyncio
    async def test_handle_news_query_service_exception(self, test_db):
        """Test exception handling in news handler"""
        with patch("src.handlers.news_handler.NewsService") as mock_news_service:
            news_service_instance = AsyncMock()
            news_service_instance.fetch_economic_news.side_effect = Exception("Unexpected error")
            news_service_instance.close = AsyncMock()
            mock_news_service.return_value = news_service_instance

            result = await handle_news_query(test_db)

            assert result["success"] is False
            assert "error_code" in result


class TestNewsMessageFormatting:
    """Tests for news message formatting"""

    def test_format_news_with_multiple_articles(self):
        """Test formatting multiple news articles"""
        from src.utils.formatters import format_news_message
        
        articles = [
            NewsArticle(
                id="n1",
                title="標題 1",
                summary="摘要 1",
                source="來源 1",
                url="",
                published_at=datetime(2026, 5, 17),
                category="economic",
                related_stocks=[],
                relevance_score=0.9,
                fetched_at=datetime.utcnow(),
            ),
            NewsArticle(
                id="n2",
                title="標題 2",
                summary="摘要 2",
                source="來源 2",
                url="",
                published_at=datetime(2026, 5, 16),
                category="economic",
                related_stocks=[],
                relevance_score=0.8,
                fetched_at=datetime.utcnow(),
            ),
        ]
        
        message = format_news_message(articles)
        
        assert "新聞" in message or "標題" in message
        assert "標題 1" in message
        assert "標題 2" in message
        assert "來源 1" in message
        assert "來源 2" in message

    def test_format_news_with_date(self):
        """Test that article dates are included in formatted message"""
        from src.utils.formatters import format_news_message
        
        articles = [
            NewsArticle(
                id="dated_news",
                title="日期新聞",
                summary="帶有日期的新聞摘要...",
                source="新聞來源",
                url="",
                published_at=datetime(2026, 5, 17),
                category="economic",
                related_stocks=[],
                relevance_score=0.85,
                fetched_at=datetime.utcnow(),
            )
        ]
        
        message = format_news_message(articles)
        
        # Should contain date
        assert "2026-05-17" in message or "5-17" in message or "17" in message

    def test_format_news_truncates_long_summaries(self):
        """Test that very long summaries are truncated"""
        from src.utils.formatters import format_news_message, truncate_summary
        
        long_summary = "這是一個非常長的摘要。" * 30
        
        truncated = truncate_summary(long_summary, max_length=150)
        
        assert len(truncated) <= 160  # 150 + some buffer for sentence boundary
        assert "…" in truncated or "。" in truncated
