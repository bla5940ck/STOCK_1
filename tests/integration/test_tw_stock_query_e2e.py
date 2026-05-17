"""
End-to-end integration tests for Taiwan stock queries (Phase 6 - US4).
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
from src.models.domain import TaiwanStock
from src.config import get_settings


@pytest.fixture
def client():
    """TestClient for FastAPI app"""
    return TestClient(app)


@pytest.fixture
def tw_stock_postback_payload():
    """Sample LINE Webhook postback payload for Taiwan stock query"""
    return {
        "destination": "xxxxxxxxxx",
        "events": [
            {
                "type": "postback",
                "postback": {
                    "data": "action=tw_stock_query&code=AAPL",
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
def tw_stock_skip_postback_payload():
    """Sample postback payload for skipping Taiwan stock query"""
    return {
        "destination": "xxxxxxxxxx",
        "events": [
            {
                "type": "postback",
                "postback": {
                    "data": "action=skip&code=AAPL",
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
def sample_tw_stocks():
    """Sample Taiwan stock correlations"""
    return [
        TaiwanStock(
            us_code="AAPL",
            tw_code="2330",
            tw_name="台積電",
            relationship_type="supplier",
            relationship_detail="台積電是 Apple 晶片製造商",
            strength=0.95,
        ),
        TaiwanStock(
            us_code="AAPL",
            tw_code="2454",
            tw_name="聯發科",
            relationship_type="competitor",
            relationship_detail="聯發科在行動晶片領域與蘋果競爭",
            strength=0.65,
        ),
    ]


class TestTaiwanStockQueryE2E:
    """End-to-end tests for Taiwan stock query (Phase 6)"""

    def test_webhook_tw_stock_postback_valid_signature(
        self, client, tw_stock_postback_payload, sample_tw_stocks
    ):
        """Test Taiwan stock query postback with valid webhook signature"""
        body = json.dumps(tw_stock_postback_payload).encode('utf-8')
        settings = get_settings()
        hash_object = hmac.new(
            settings.LINE_CHANNEL_SECRET.encode('utf-8'),
            body,
            hashlib.sha256
        )
        signature = base64.b64encode(hash_object.digest()).decode('utf-8')

        with patch("src.api.webhooks.handle_tw_stock_query") as mock_handler:
            mock_handler.return_value = {
                "success": True,
                "message": "🔗 與 AAPL 相關的台股標的\n\n• 台積電 (2330) - 供應商\n...",
                "tw_stock_count": 2,
                "source": "database",
            }

            response = client.post(
                "/webhook/line",
                json=tw_stock_postback_payload,
                headers={"X-Line-Signature": signature},
            )

            assert response.status_code == 200
            assert response.json() == {"message": "OK"}

    def test_webhook_tw_stock_skip_postback(
        self, client, tw_stock_skip_postback_payload
    ):
        """Test skipping Taiwan stock query"""
        body = json.dumps(tw_stock_skip_postback_payload).encode('utf-8')
        settings = get_settings()
        hash_object = hmac.new(
            settings.LINE_CHANNEL_SECRET.encode('utf-8'),
            body,
            hashlib.sha256
        )
        signature = base64.b64encode(hash_object.digest()).decode('utf-8')

        response = client.post(
            "/webhook/line",
            json=tw_stock_skip_postback_payload,
            headers={"X-Line-Signature": signature},
        )

        # Should return OK even if no response is sent
        assert response.status_code == 200

    def test_webhook_tw_stock_invalid_signature(
        self, client, tw_stock_postback_payload
    ):
        """Test Taiwan stock postback with invalid signature"""
        invalid_signature = "invalid_signature_here"

        response = client.post(
            "/webhook/line",
            json=tw_stock_postback_payload,
            headers={"X-Line-Signature": invalid_signature},
        )

        assert response.status_code == 403


class TestTaiwanStockMessageFormatting:
    """Tests for Taiwan stock message formatting (Phase 6)"""

    def test_format_tw_stock_message(self, sample_tw_stocks):
        """Test formatting Taiwan stock correlation message"""
        from src.utils.formatters import format_tw_stock_message
        
        message = format_tw_stock_message("AAPL", sample_tw_stocks)
        
        # Verify message structure
        assert "AAPL" in message
        assert "台股" in message or "台灣" in message
        
        # Verify all stocks are included
        assert "台積電" in message
        assert "聯發科" in message
        assert "2330" in message
        assert "2454" in message

    def test_tw_stock_message_contains_relationship_type(self, sample_tw_stocks):
        """Test that relationship types are included in message"""
        from src.utils.formatters import format_tw_stock_message
        
        message = format_tw_stock_message("AAPL", sample_tw_stocks)
        
        # Verify relationship types are translated
        assert "供應商" in message
        assert "競爭者" in message

    def test_tw_stock_message_contains_strength(self, sample_tw_stocks):
        """Test that strength indicators are included in message"""
        from src.utils.formatters import format_tw_stock_message
        
        message = format_tw_stock_message("AAPL", sample_tw_stocks)
        
        # Verify strength is shown
        assert "相關度" in message or "95" in message or "65" in message

    def test_tw_stock_message_with_empty_list(self):
        """Test formatting when no Taiwan stocks are provided"""
        from src.utils.formatters import format_tw_stock_message
        
        message = format_tw_stock_message("UNKNOWN", [])
        
        # Should still return valid message
        assert isinstance(message, str)
        assert "台股" in message or "相關" in message

    def test_tw_stock_message_respects_line_limit(self, sample_tw_stocks):
        """Test that Taiwan stock message respects LINE character limit"""
        from src.utils.formatters import format_tw_stock_message
        
        message = format_tw_stock_message("AAPL", sample_tw_stocks)
        
        # LINE message limit is 2000 characters
        assert len(message) <= 2000


class TestTaiwanStockPostbackParsing:
    """Tests for postback data parsing (Phase 6)"""

    def test_parse_tw_stock_postback_data(self):
        """Test parsing Taiwan stock postback data"""
        postback_data = "action=tw_stock_query&code=AAPL"
        
        params = {}
        for param in postback_data.split("&"):
            if "=" in param:
                key, value = param.split("=", 1)
                params[key] = value
        
        assert params["action"] == "tw_stock_query"
        assert params["code"] == "AAPL"

    def test_parse_skip_postback_data(self):
        """Test parsing skip postback data"""
        postback_data = "action=skip&code=AAPL"
        
        params = {}
        for param in postback_data.split("&"):
            if "=" in param:
                key, value = param.split("=", 1)
                params[key] = value
        
        assert params["action"] == "skip"
        assert params["code"] == "AAPL"


class TestTaiwanStockCodeValidation:
    """Tests for Taiwan stock code validation"""

    def test_validate_us_stock_code_for_tw_lookup(self):
        """Test that US stock codes are validated for Taiwan lookup"""
        from src.utils.validators import validate_stock_code
        
        # Valid codes
        assert validate_stock_code("AAPL") == "AAPL"
        assert validate_stock_code("aapl") == "AAPL"
        assert validate_stock_code("TSLA") == "TSLA"
        
        # Invalid codes
        from src.exceptions import ValidationError
        with pytest.raises(ValidationError):
            validate_stock_code("TOOLONGCODE")
