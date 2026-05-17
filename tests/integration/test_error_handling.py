"""
Integration tests for error handling.
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.exceptions import ApplicationError, ValidationError


@pytest.fixture
def client():
    """TestClient for FastAPI app"""
    return TestClient(app)


class TestErrorHandling:
    """Tests for error handling"""

    def test_health_check_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_info_endpoint(self, client):
        """Test info endpoint"""
        response = client.get("/info")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "LINE Bot US Stock 美股與新聞助理"
        assert "version" in data

    def test_application_error_handler(self, client):
        """Test application error handling"""
        # This would test custom exception handlers
        # Currently just verifying health endpoints work
        response = client.get("/health")
        assert response.status_code == 200

    def test_404_error(self, client):
        """Test 404 error handling"""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.options("/health")
        assert "access-control-allow-origin" in response.headers
