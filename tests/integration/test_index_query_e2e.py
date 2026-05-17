"""
Integration tests for index query end-to-end flow.
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from decimal import Decimal
from datetime import datetime

from src.main import app
from src.models.domain import Index, DataSourceEnum
from src.config import get_settings


@pytest.fixture
def client():
    """TestClient for FastAPI app"""
    return TestClient(app)


@pytest.fixture
def sample_webhook_payload():
    """Sample LINE Webhook payload for index query"""
    return {
        "destination": "xxxxxxxxxx",
        "events": [
            {
                "type": "message",
                "message": {
                    "type": "text",
                    "id": "100001",
                    "text": "美股",
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
def sample_indices():
    """Sample index data"""
    return [
        Index(
            id="^GSPC",
            zh_name="S&P 500",
            current_price=Decimal("4500.25"),
            previous_close=Decimal("4480.00"),
            change_amount=Decimal("20.25"),
            change_percent=Decimal("0.45"),
            high_52w=Decimal("4800.00"),
            low_52w=Decimal("4000.00"),
            last_updated=datetime.utcnow(),
            data_source=DataSourceEnum.YAHOO_FINANCE,
        ),
        Index(
            id="^IXIC",
            zh_name="納斯達克綜合指數",
            current_price=Decimal("14200.50"),
            previous_close=Decimal("14110.00"),
            change_amount=Decimal("90.50"),
            change_percent=Decimal("0.64"),
            high_52w=Decimal("14500.00"),
            low_52w=Decimal("11000.00"),
            last_updated=datetime.utcnow(),
            data_source=DataSourceEnum.YAHOO_FINANCE,
        ),
        Index(
            id="^SOX",
            zh_name="費城半導體指數",
            current_price=Decimal("4100.00"),
            previous_close=Decimal("4050.00"),
            change_amount=Decimal("50.00"),
            change_percent=Decimal("1.23"),
            high_52w=Decimal("4500.00"),
            low_52w=Decimal("3000.00"),
            last_updated=datetime.utcnow(),
            data_source=DataSourceEnum.YAHOO_FINANCE,
        ),
    ]


class TestIndexQueryE2E:
    """End-to-end tests for index query flow"""

    def test_webhook_index_query_valid_signature(
        self, client, sample_webhook_payload, sample_indices
    ):
        """Test index query with valid webhook signature"""
        import hmac
        import hashlib
        import base64
        
        # Create valid signature
        body = json.dumps(sample_webhook_payload).encode('utf-8')
        settings = get_settings()
        hash_object = hmac.new(
            settings.LINE_CHANNEL_SECRET.encode('utf-8'),
            body,
            hashlib.sha256
        )
        signature = base64.b64encode(hash_object.digest()).decode('utf-8')

        # Mock the index handler
        with patch("src.api.webhooks.handle_index_query") as mock_handler:
            mock_handler.return_value = {
                "success": True,
                "message": "📊 美股三大指數\n\nS&P 500: 4500.25 ↑ +0.45%",
                "count": 3,
                "source": "yahoo_finance",
            }

            response = client.post(
                "/webhook/line",
                json=sample_webhook_payload,
                headers={"X-Line-Signature": signature},
            )

            assert response.status_code == 200
            assert response.json() == {"message": "OK"}

    def test_webhook_index_query_invalid_signature(
        self, client, sample_webhook_payload
    ):
        """Test index query with invalid signature"""
        response = client.post(
            "/webhook/line",
            json=sample_webhook_payload,
            headers={"X-Line-Signature": "invalid_signature"},
        )

        assert response.status_code == 401

    def test_webhook_missing_signature_header(
        self, client, sample_webhook_payload
    ):
        """Test webhook without signature header"""
        response = client.post(
            "/webhook/line",
            json=sample_webhook_payload,
        )

        assert response.status_code == 400


class TestIndexMessageFormatting:
    """Tests for index message formatting"""

    def test_format_index_message(self, sample_indices):
        """Test formatting index data to LINE message"""
        from src.utils.formatters import format_index_message
        
        message = format_index_message(sample_indices)
        
        # Verify message contains all indices
        assert "S&P 500" in message or "4500" in message
        assert "納斯達克" in message or "14200" in message
        assert "費城" in message or "4100" in message
        
        # Verify formatting elements
        assert "📈" in message or "↑" in message or "↓" in message

    def test_format_index_message_positive_change(self):
        """Test formatting with positive price change"""
        from src.utils.formatters import format_index_message
        
        indices = [
            Index(
                id="^GSPC",
                zh_name="S&P 500",
                current_price=Decimal("4500.25"),
                previous_close=Decimal("4480.00"),
                change_amount=Decimal("20.25"),
                change_percent=Decimal("0.45"),
                high_52w=Decimal("4800.00"),
                low_52w=Decimal("4000.00"),
                last_updated=datetime.utcnow(),
                data_source=DataSourceEnum.YAHOO_FINANCE,
            ),
        ]
        
        message = format_index_message(indices)
        
        assert "↑" in message or "+0.45" in message
        assert "4500" in message

    def test_format_index_message_negative_change(self):
        """Test formatting with negative price change"""
        from src.utils.formatters import format_index_message
        
        indices = [
            Index(
                id="^IXIC",
                zh_name="納斯達克",
                current_price=Decimal("14000.00"),
                previous_close=Decimal("14200.00"),
                change_amount=Decimal("-200.00"),
                change_percent=Decimal("-1.41"),
                high_52w=Decimal("14500.00"),
                low_52w=Decimal("11000.00"),
                last_updated=datetime.utcnow(),
                data_source=DataSourceEnum.YAHOO_FINANCE,
            ),
        ]
        
        message = format_index_message(indices)
        
        assert "↓" in message or "-1.41" in message
        assert "14000" in message
