"""
End-to-end integration tests for stock and news queries.
"""

import pytest
import json
import hmac
import hashlib
import base64
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from decimal import Decimal
from datetime import datetime

from src.main import app
from src.models.domain import Stock, NewsArticle, DataSourceEnum
from src.config import get_settings


@pytest.fixture
def client():
    """TestClient for FastAPI app"""
    return TestClient(app)


@pytest.fixture
def stock_webhook_payload():
    """Sample LINE Webhook payload for stock query"""
    return {
        "destination": "xxxxxxxxxx",
        "events": [
            {
                "type": "message",
                "message": {
                    "type": "text",
                    "id": "100002",
                    "text": "AAPL",
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
def sample_stock():
    """Sample stock data"""
    return Stock(
        code="AAPL",
        company_name="Apple Inc.",
        zh_name="蘋果公司",
        current_price=Decimal("180.50"),
        previous_close=Decimal("179.25"),
        change_amount=Decimal("1.25"),
        change_percent=Decimal("0.70"),
        market_cap_billion=Decimal("2800.0"),
        pe_ratio=Decimal("28.5"),
        dividend_yield=Decimal("0.45"),
        sector="Technology",
        industry="Consumer Electronics",
        last_updated=datetime.utcnow(),
        data_source=DataSourceEnum.YAHOO_FINANCE,
    )


@pytest.fixture
def sample_news():
    """Sample news articles"""
    return [
        NewsArticle(
            id="news_001",
            title="蘋果新 iPhone 確認發佈",
            summary="蘋果公司宣佈將在下月舉辦新品發佈會，預計推出新款 iPhone...",
            source="科技新聞",
            url="https://example.com/news1",
            published_at=datetime.utcnow(),
            category="earnings",
            related_stocks=["AAPL"],
            relevance_score=0.95,
            fetched_at=datetime.utcnow(),
        ),
        NewsArticle(
            id="news_002",
            title="蘋果股價創新高",
            summary="受到新品發佈預期推動，蘋果股價今日創下年內新高...",
            source="財經新聞",
            url="https://example.com/news2",
            published_at=datetime.utcnow(),
            category="market",
            related_stocks=["AAPL"],
            relevance_score=0.88,
            fetched_at=datetime.utcnow(),
        ),
    ]


class TestStockQueryE2E:
    """End-to-end tests for stock query flow"""

    def test_webhook_stock_query_valid_signature(
        self, client, stock_webhook_payload, sample_stock, sample_news
    ):
        """Test stock query with valid webhook signature"""
        # Create valid signature
        body = json.dumps(stock_webhook_payload).encode('utf-8')
        settings = get_settings()
        hash_object = hmac.new(
            settings.LINE_CHANNEL_SECRET.encode('utf-8'),
            body,
            hashlib.sha256
        )
        signature = base64.b64encode(hash_object.digest()).decode('utf-8')

        # Mock the handlers
        with patch("src.api.webhooks.handle_stock_query") as mock_handler:
            mock_handler.return_value = {
                "success": True,
                "message": "📈 AAPL - 蘋果公司\n現價: $180.50 ↑0.70%",
                "stock": sample_stock,
                "news_count": 2,
            }

            response = client.post(
                "/webhook/line",
                json=stock_webhook_payload,
                headers={"X-Line-Signature": signature},
            )

            assert response.status_code == 200
            assert response.json() == {"message": "OK"}

    def test_webhook_invalid_stock_code(
        self, client, stock_webhook_payload
    ):
        """Test webhook with invalid stock code"""
        stock_webhook_payload["events"][0]["message"]["text"] = "TOOLONGCODE"
        
        body = json.dumps(stock_webhook_payload).encode('utf-8')
        settings = get_settings()
        hash_object = hmac.new(
            settings.LINE_CHANNEL_SECRET.encode('utf-8'),
            body,
            hashlib.sha256
        )
        signature = base64.b64encode(hash_object.digest()).decode('utf-8')

        response = client.post(
            "/webhook/line",
            json=stock_webhook_payload,
            headers={"X-Line-Signature": signature},
        )

        assert response.status_code == 200


class TestNewsQueryE2E:
    """End-to-end tests for news query flow"""

    def test_webhook_news_query_valid_signature(
        self, client, news_webhook_payload, sample_news
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

        # Mock the handler
        with patch("src.api.webhooks.handle_news_query") as mock_handler:
            mock_handler.return_value = {
                "success": True,
                "message": "📰 最新美國經濟新聞\n\n• 聯準會升息...",
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


class TestStockMessageFormatting:
    """Tests for stock message formatting"""

    def test_format_stock_message(self, sample_stock, sample_news):
        """Test formatting stock data with news"""
        from src.utils.formatters import format_stock_message
        
        message = format_stock_message(sample_stock, sample_news)
        
        # Verify message contains stock code and company info
        assert "AAPL" in message
        assert "蘋果" in message or "Apple" in message
        
        # Verify message contains price info
        assert "180" in message
        assert "0.70" in message or "↑" in message
        
        # Verify news section
        assert "新聞" in message or "iPhone" in message

    def test_format_stock_message_without_news(self, sample_stock):
        """Test formatting stock without news"""
        from src.utils.formatters import format_stock_message
        
        message = format_stock_message(sample_stock)
        
        assert "AAPL" in message
        assert "180.50" in message
        assert "0.70" in message


class TestNewsMessageFormatting:
    """Tests for news message formatting"""

    def test_format_news_message(self, sample_news):
        """Test formatting news articles"""
        from src.utils.formatters import format_news_message
        
        message = format_news_message(sample_news)
        
        # Verify message contains headers
        assert "新聞" in message or "經濟" in message
        
        # Verify articles are included
        assert "iPhone" in message or "Apple" in message

    def test_format_news_message_truncation(self, sample_news):
        """Test that long summaries are truncated"""
        from src.utils.formatters import format_news_message
        
        # Create a news with very long summary
        long_news = [
            NewsArticle(
                id="news_long",
                title="Long Title",
                summary="這是一個非常長的新聞摘要，" * 20,  # Very long
                source="News",
                url="",
                published_at=datetime.utcnow(),
                category="market",
                related_stocks=[],
                relevance_score=0.5,
                fetched_at=datetime.utcnow(),
            )
        ]
        
        message = format_news_message(long_news)
        
        # Message should be reasonable length
        assert len(message) < 2000
