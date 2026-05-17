"""
End-to-end integration tests for economic news queries (Phase 5 - US3).
"""

import pytest
import json
import hmac
import hashlib
import base64
from fastapi.testclient import TestClient
from unittest.mock import patch
from datetime import datetime

from src.main import app
from src.models.domain import NewsArticle
from src.config import get_settings


@pytest.fixture
def client():
    """TestClient for FastAPI app"""
    return TestClient(app)


@pytest.fixture
def news_webhook_payload():
    """Sample LINE Webhook payload for news query"""
    return {
        "destination": "xxxxxxxxxx",
        "events": [
            {
                "type": "message",
                "message": {
                    "type": "text",
                    "id": "100003",
                    "text": "新聞",
                },
                "timestamp": 1462629479859,
                "source": {
                    "type": "user",
                    "userId": "U206d25c2ea6bd87c17655609a1c37cb8"
                },
                "replyToken": "nHuyWiB7yP5Zw52FIkcQT",
            }
        ]
    }


@pytest.fixture
def sample_economic_news():
    """Sample economic news articles"""
    return [
        NewsArticle(
            id="econ_001",
            title="聯準會升息決定確認",
            summary="美國聯邦準備委員會宣佈升息 0.5%，以控制通脹，市場反應積極...",
            source="路透社",
            url="https://example.com/news1",
            published_at=datetime(2026, 5, 17),
            category="economic",
            related_stocks=["SPY", "QQQ"],
            relevance_score=0.95,
            fetched_at=datetime.utcnow(),
        ),
        NewsArticle(
            id="econ_002",
            title="美國失業率創新低",
            summary="美國 4 月失業率下降至 3.4%，創 50 年新低...",
            source="美聯社",
            url="https://example.com/news2",
            published_at=datetime(2026, 5, 16),
            category="economic",
            related_stocks=["DIA"],
            relevance_score=0.88,
            fetched_at=datetime.utcnow(),
        ),
        NewsArticle(
            id="econ_003",
            title="供應鏈緩解推動製造業恢復",
            summary="隨著全球供應鏈正常化，美國製造業指數反彈...",
            source="財經新聞",
            url="https://example.com/news3",
            published_at=datetime(2026, 5, 15),
            category="economic",
            related_stocks=["IYM"],
            relevance_score=0.82,
            fetched_at=datetime.utcnow(),
        ),
    ]


class TestNewsQueryE2E:
    """End-to-end tests for economic news query (Phase 5)"""

    def test_webhook_news_query_valid_signature(
        self, client, news_webhook_payload, sample_economic_news
    ):
        """Test news query with valid webhook signature"""
        body = json.dumps(news_webhook_payload).encode('utf-8')
        settings = get_settings()
        hash_object = hmac.new(
            settings.LINE_CHANNEL_SECRET.encode('utf-8'),
            body,
            hashlib.sha256
        )
        signature = base64.b64encode(hash_object.digest()).decode('utf-8')

        with patch("src.api.webhooks.handle_news_query") as mock_handler:
            mock_handler.return_value = {
                "success": True,
                "message": "📰 最新美國經濟新聞\n\n• 聯準會升息決定確認\n...",
                "article_count": 3,
                "source": "google_news",
            }

            response = client.post(
                "/webhook/line",
                json=news_webhook_payload,
                headers={"X-Line-Signature": signature},
            )

            assert response.status_code == 200
            assert response.json() == {"message": "OK"}

    def test_webhook_news_query_invalid_signature(self, client, news_webhook_payload):
        """Test news query with invalid webhook signature"""
        invalid_signature = "invalid_signature_here"

        response = client.post(
            "/webhook/line",
            json=news_webhook_payload,
            headers={"X-Line-Signature": invalid_signature},
        )

        assert response.status_code == 403

    def test_webhook_missing_signature_header(self, client, news_webhook_payload):
        """Test webhook request without signature header"""
        response = client.post(
            "/webhook/line",
            json=news_webhook_payload,
        )

        assert response.status_code == 403


class TestNewsMessageFormatting:
    """Tests for economic news message formatting (Phase 5)"""

    def test_format_economic_news_message(self, sample_economic_news):
        """Test formatting economic news articles"""
        from src.utils.formatters import format_news_message
        
        message = format_news_message(sample_economic_news)
        
        # Verify message structure
        assert "新聞" in message or "經濟" in message
        
        # Verify all articles are included
        assert "聯準會" in message
        assert "失業率" in message
        assert "製造業" in message

    def test_news_message_contains_sources(self, sample_economic_news):
        """Test that news message contains article sources"""
        from src.utils.formatters import format_news_message
        
        message = format_news_message(sample_economic_news)
        
        # Verify sources are included
        assert "路透社" in message
        assert "美聯社" in message
        assert "財經新聞" in message

    def test_news_message_contains_dates(self, sample_economic_news):
        """Test that news message contains publication dates"""
        from src.utils.formatters import format_news_message
        
        message = format_news_message(sample_economic_news)
        
        # Verify dates are included (at least some date references)
        assert "2026" in message or "5" in message

    def test_news_message_length_within_limits(self, sample_economic_news):
        """Test that formatted news message respects LINE message limit"""
        from src.utils.formatters import format_news_message
        
        message = format_news_message(sample_economic_news)
        
        # LINE message limit is 2000 characters
        assert len(message) <= 2000, f"Message too long: {len(message)} chars"

    def test_news_message_with_empty_articles(self):
        """Test formatting when no articles are provided"""
        from src.utils.formatters import format_news_message
        
        message = format_news_message([])
        
        # Should still return valid message
        assert isinstance(message, str)
        assert len(message) > 0


class TestNewsKeywordDetection:
    """Tests for news keyword detection in queries"""

    def test_detect_news_keyword_chinese(self):
        """Test detection of Chinese news keyword"""
        from src.utils.validators import detect_query_type
        
        assert detect_query_type("新聞") == "news"

    def test_detect_news_keyword_english(self):
        """Test detection of English news keyword"""
        from src.utils.validators import detect_query_type
        
        assert detect_query_type("news") == "news"
        assert detect_query_type("NEWS") == "news"
        assert detect_query_type("News") == "news"

    def test_detect_non_news_queries(self):
        """Test that non-news queries are not detected as news"""
        from src.utils.validators import detect_query_type
        
        assert detect_query_type("美股") != "news"
        assert detect_query_type("AAPL") != "news"
        assert detect_query_type("查詢") != "news"


class TestNewsServiceIntegration:
    """Integration tests for news service (Phase 5)"""

    @pytest.mark.asyncio
    async def test_fetch_economic_news_returns_valid_structure(self, test_db):
        """Test that economic news fetching returns valid article structure"""
        from src.services.news_service import NewsService
        
        service = NewsService(test_db)
        
        # Mock the Google News client
        with patch.object(service.google_news_client, 'fetch_news') as mock_fetch:
            mock_fetch.return_value = [
                NewsArticle(
                    id="test",
                    title="測試新聞",
                    summary="測試摘要",
                    source="測試來源",
                    url="https://example.com",
                    published_at=datetime.utcnow(),
                    category="economic",
                    related_stocks=[],
                    relevance_score=0.8,
                    fetched_at=datetime.utcnow(),
                )
            ]
            
            result = await service.fetch_economic_news(limit=5)
            
            assert result["success"] is True
            assert len(result["data"]) >= 1
            assert all(isinstance(article, NewsArticle) for article in result["data"])
