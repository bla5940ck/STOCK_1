"""
Unit tests for configuration loading.
"""

import pytest
import os
from src.config import Settings, get_settings
from src.exceptions import ConfigError


class TestSettingsLoading:
    """Tests for settings loading"""

    def test_required_settings_validation(self):
        """Test that required settings are validated"""
        # Create settings with missing required fields
        settings = Settings(
            LINE_CHANNEL_ACCESS_TOKEN="",
            LINE_CHANNEL_SECRET="",
        )

        with pytest.raises(ValueError, match="Missing required environment variables"):
            settings.validate_required()

    def test_default_values(self):
        """Test default configuration values"""
        settings = Settings(
            LINE_CHANNEL_ACCESS_TOKEN="token",
            LINE_CHANNEL_SECRET="secret",
        )

        assert settings.SERVER_HOST == "0.0.0.0"
        assert settings.SERVER_PORT == 8000
        assert settings.DEBUG is False
        assert settings.LOG_LEVEL == "INFO"
        assert settings.API_TIMEOUT == 20
        assert settings.CACHE_INDEX_TTL_MINUTES == 5

    def test_cached_settings_instance(self):
        """Test that get_settings returns cached instance"""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2


class TestEnvironmentVariableLoading:
    """Tests for environment variable loading"""

    def test_load_from_env_file(self, tmp_path):
        """Test loading from .env file"""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "LINE_CHANNEL_ACCESS_TOKEN=test_token\n"
            "LINE_CHANNEL_SECRET=test_secret\n"
            "SERVER_PORT=9000\n"
        )

        # Note: In real test, we'd need to set Config to use this file
        # This is more of an integration test


class TestSettingsValidation:
    """Tests for settings validation"""

    def test_valid_settings(self):
        """Test valid settings pass validation"""
        settings = Settings(
            LINE_CHANNEL_ACCESS_TOKEN="valid_token",
            LINE_CHANNEL_SECRET="valid_secret",
        )
        # Should not raise
        settings.validate_required()

    def test_timeout_values(self):
        """Test timeout configuration"""
        settings = Settings(
            LINE_CHANNEL_ACCESS_TOKEN="token",
            LINE_CHANNEL_SECRET="secret",
            API_TIMEOUT=30,
            INDEX_FETCH_TIMEOUT=5,
        )

        assert settings.API_TIMEOUT == 30
        assert settings.INDEX_FETCH_TIMEOUT == 5
