"""
Unit tests for message formatters.
"""

import pytest
from datetime import datetime
from decimal import Decimal

from src.utils.formatters import (
    truncate_summary,
    format_price_change,
    format_index_message,
    format_stock_message,
    format_news_message,
    format_error_message,
)
from src.models.domain import (
    Index, Stock, NewsArticle, DataSourceEnum
)


class TestTruncateSummary:
    """Tests for truncate_summary"""

    def test_short_summary_not_truncated(self):
        """Test short summaries are not truncated"""
        text = "這是一個短摘要"
        assert truncate_summary(text) == text

    def test_long_summary_truncated(self):
        """Test long summaries are truncated to 150 chars"""
        text = "這" * 200  # 200 characters
        result = truncate_summary(text, max_length=150)
        assert len(result) <= 150

    def test_sentence_boundary_preservation(self):
        """Test sentence boundaries are preserved"""
        text = "第一句。第二句。第三句。" * 20
        result = truncate_summary(text, max_length=100)
        # Should end with sentence marker if possible
        assert result.endswith("。") or result.endswith("…")


class TestFormatPriceChange:
    """Tests for format_price_change"""

    def test_positive_change(self):
        """Test positive price change"""
        result = format_price_change(Decimal("100.50"), Decimal("1.50"), "↑")
        assert "100.50" in result
        assert "↑" in result
        assert "+1.50%" in result

    def test_negative_change(self):
        """Test negative price change"""
        result = format_price_change(Decimal("100.50"), Decimal("-1.50"), "↓")
        assert "100.50" in result
        assert "↓" in result
        assert "-1.50%" in result

    def test_zero_change(self):
        """Test zero price change"""
        result = format_price_change(Decimal("100.50"), Decimal("0.00"), "→")
        assert "100.50" in result
        assert "→" in result


class TestFormatIndexMessage:
    """Tests for format_index_message"""

    @pytest.fixture
    def sample_indices(self):
        """Sample index objects"""
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
                zh_name="那斯達克",
                current_price=Decimal("14200.50"),
                previous_close=Decimal("14110.00"),
                change_amount=Decimal("90.50"),
                change_percent=Decimal("0.64"),
                high_52w=Decimal("14500.00"),
                low_52w=Decimal("11000.00"),
                last_updated=datetime.utcnow(),
                data_source=DataSourceEnum.YAHOO_FINANCE,
            ),
        ]

    def test_index_message_format(self, sample_indices):
        """Test index message formatting"""
        result = format_index_message(sample_indices)
        assert "美股三大指數" in result
        assert "S&P 500" in result
        assert "那斯達克" in result
        assert "yahoo_finance" in result

    def test_index_message_contains_direction_symbols(self, sample_indices):
        """Test message contains direction symbols"""
        result = format_index_message(sample_indices)
        assert "↑" in result or "↓" in result or "→" in result

    def test_index_message_contains_prices(self, sample_indices):
        """Test message contains price information"""
        result = format_index_message(sample_indices)
        assert "4500" in result  # S&P price
        assert "14200" in result  # NASDAQ price


class TestFormatErrorMessage:
    """Tests for format_error_message"""

    def test_error_message_format(self):
        """Test error message formatting"""
        result = format_error_message(
            "E001_TIMEOUT",
            "API 響應超時，請稍後重試。"
        )
        assert "查詢出錯" in result
        assert "API 響應超時" in result
        assert "請稍後重試" in result

    def test_error_message_with_request_id(self):
        """Test error message with request ID"""
        result = format_error_message(
            "E006_STOCK_NOT_FOUND",
            "無法找到該股票",
            request_id="req_12345"
        )
        assert "req_12345" in result


class TestSuggestionMessage:
    """Tests for suggestion message"""

    def test_suggestion_contains_commands(self):
        """Test suggestion message contains available commands"""
        from src.utils.formatters import format_suggestion_message
        result = format_suggestion_message()
        assert "美股" in result
        assert "新聞" in result
        assert "AAPL" in result
