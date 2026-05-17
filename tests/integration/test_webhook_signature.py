"""
Integration tests for Webhook signature verification.
"""

import pytest
import hmac
import hashlib
import base64
import json
from fastapi.testclient import TestClient

from src.main import app
from src.config import get_settings


def create_valid_signature(body: bytes, channel_secret: str) -> str:
    """Create valid LINE Webhook signature"""
    hash_object = hmac.new(
        channel_secret.encode('utf-8'),
        body,
        hashlib.sha256
    )
    return base64.b64encode(hash_object.digest()).decode('utf-8')


@pytest.fixture
def client():
    """TestClient for FastAPI app"""
    return TestClient(app)


@pytest.fixture
def sample_webhook_payload():
    """Sample LINE Webhook payload"""
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


class TestWebhookSignatureVerification:
    """Tests for Webhook signature verification"""

    def test_valid_signature(self, client, sample_webhook_payload):
        """Test request with valid signature"""
        body = json.dumps(sample_webhook_payload).encode('utf-8')
        settings = get_settings()
        signature = create_valid_signature(body, settings.LINE_CHANNEL_SECRET)

        response = client.post(
            "/webhook/line",
            content=body,
            headers={"X-Line-Signature": signature},
        )

        # Should not return 401 Unauthorized
        assert response.status_code != 401

    def test_invalid_signature(self, client, sample_webhook_payload):
        """Test request with invalid signature"""
        body = json.dumps(sample_webhook_payload).encode('utf-8')
        invalid_signature = "invalid_signature_12345"

        response = client.post(
            "/webhook/line",
            content=body,
            headers={"X-Line-Signature": invalid_signature},
        )

        assert response.status_code == 401

    def test_missing_signature_header(self, client, sample_webhook_payload):
        """Test request without signature header"""
        body = json.dumps(sample_webhook_payload).encode('utf-8')

        response = client.post(
            "/webhook/line",
            content=body,
        )

        assert response.status_code == 400

    def test_invalid_json_payload(self, client):
        """Test request with invalid JSON"""
        body = b"invalid json {{"
        settings = get_settings()
        signature = create_valid_signature(body, settings.LINE_CHANNEL_SECRET)

        response = client.post(
            "/webhook/line",
            content=body,
            headers={"X-Line-Signature": signature},
        )

        assert response.status_code == 400


class TestWebhookEventHandling:
    """Tests for Webhook event handling"""

    def test_webhook_message_event(self, client, sample_webhook_payload):
        """Test webhook message event processing"""
        body = json.dumps(sample_webhook_payload).encode('utf-8')
        settings = get_settings()
        signature = create_valid_signature(body, settings.LINE_CHANNEL_SECRET)

        response = client.post(
            "/webhook/line",
            content=body,
            headers={"X-Line-Signature": signature},
        )

        assert response.status_code == 200

    def test_webhook_response_format(self, client, sample_webhook_payload):
        """Test webhook response format"""
        body = json.dumps(sample_webhook_payload).encode('utf-8')
        settings = get_settings()
        signature = create_valid_signature(body, settings.LINE_CHANNEL_SECRET)

        response = client.post(
            "/webhook/line",
            content=body,
            headers={"X-Line-Signature": signature},
        )

        assert response.json() == {"message": "OK"}
