"""
Unit tests for input validators.
"""

import pytest
from src.utils.validators import (
    validate_stock_code,
    validate_tw_stock_code,
    validate_query_text,
    is_index_keyword,
    is_news_keyword,
    detect_query_type,
)
from src.exceptions import ValidationError


class TestValidateStockCode:
    """Tests for validate_stock_code"""

    def test_valid_stock_codes(self):
        """Test valid stock codes"""
        assert validate_stock_code("AAPL") == "AAPL"
        assert validate_stock_code("aapl") == "AAPL"
        assert validate_stock_code("ApPl") == "AAPL"
        assert validate_stock_code("A") == "A"
        assert validate_stock_code("TSLA") == "TSLA"
        assert validate_stock_code("BRK") == "BRK"

    def test_code_conversion_to_uppercase(self):
        """Test lowercase codes are converted to uppercase"""
        assert validate_stock_code("goog") == "GOOG"
        assert validate_stock_code("MmM") == "MMM"

    def test_code_with_whitespace(self):
        """Test codes with leading/trailing whitespace are trimmed"""
        assert validate_stock_code("  AAPL  ") == "AAPL"
        assert validate_stock_code("\tTSLA\n") == "TSLA"

    def test_invalid_codes_too_long(self):
        """Test codes with >5 characters raise error"""
        with pytest.raises(ValidationError):
            validate_stock_code("TOOLONG")
        with pytest.raises(ValidationError):
            validate_stock_code("123456")

    def test_invalid_codes_non_alphabetic(self):
        """Test codes with numbers or special chars raise error"""
        with pytest.raises(ValidationError):
            validate_stock_code("123")
        with pytest.raises(ValidationError):
            validate_stock_code("AA-B")
        with pytest.raises(ValidationError):
            validate_stock_code("AA.B")

    def test_empty_code(self):
        """Test empty code raises error"""
        with pytest.raises(ValidationError):
            validate_stock_code("")
        with pytest.raises(ValidationError):
            validate_stock_code("   ")

    def test_none_code(self):
        """Test None code raises error"""
        with pytest.raises(ValidationError):
            validate_stock_code(None)


class TestValidateTwStockCode:
    """Tests for validate_tw_stock_code"""

    def test_valid_tw_codes(self):
        """Test valid Taiwan stock codes"""
        assert validate_tw_stock_code("2330") == "2330"
        assert validate_tw_stock_code("0050") == "0050"
        assert validate_tw_stock_code("1234") == "1234"

    def test_code_with_whitespace(self):
        """Test codes with whitespace are trimmed"""
        assert validate_tw_stock_code("  2330  ") == "2330"

    def test_invalid_codes_wrong_length(self):
        """Test codes with != 4 digits raise error"""
        with pytest.raises(ValidationError):
            validate_tw_stock_code("233")
        with pytest.raises(ValidationError):
            validate_tw_stock_code("23300")

    def test_invalid_codes_non_numeric(self):
        """Test codes with letters raise error"""
        with pytest.raises(ValidationError):
            validate_tw_stock_code("233A")
        with pytest.raises(ValidationError):
            validate_tw_stock_code("2A30")

    def test_empty_code(self):
        """Test empty code raises error"""
        with pytest.raises(ValidationError):
            validate_tw_stock_code("")


class TestValidateQueryText:
    """Tests for validate_query_text"""

    def test_valid_query_texts(self):
        """Test valid query texts"""
        assert validate_query_text("美股") == "美股"
        assert validate_query_text("AAPL") == "AAPL"
        assert validate_query_text("新聞") == "新聞"

    def test_whitespace_trimming(self):
        """Test whitespace is trimmed"""
        assert validate_query_text("  美股  ") == "美股"
        assert validate_query_text("\nAApl\t") == "AApl"

    def test_length_validation(self):
        """Test length constraints"""
        assert validate_query_text("a") == "a"
        assert validate_query_text("a" * 100) == "a" * 100

    def test_text_too_long(self):
        """Test texts > 100 chars raise error"""
        with pytest.raises(ValidationError):
            validate_query_text("a" * 101)

    def test_empty_text(self):
        """Test empty text raises error"""
        with pytest.raises(ValidationError):
            validate_query_text("")
        with pytest.raises(ValidationError):
            validate_query_text("   ")


class TestKeywordDetection:
    """Tests for keyword detection"""

    def test_index_keywords(self):
        """Test index keywords"""
        assert is_index_keyword("美股")
        assert is_index_keyword("指數")
        assert is_index_keyword("index")
        assert is_index_keyword("INDEX")
        assert not is_index_keyword("新聞")

    def test_news_keywords(self):
        """Test news keywords"""
        assert is_news_keyword("新聞")
        assert is_news_keyword("news")
        assert is_news_keyword("NEWS")
        assert is_news_keyword("經濟新聞")
        assert not is_news_keyword("美股")


class TestQueryTypeDetection:
    """Tests for query type detection"""

    def test_index_query_detection(self):
        """Test index query detection"""
        assert detect_query_type("美股") == "index"
        assert detect_query_type("指數") == "index"
        assert detect_query_type("INDEX") == "index"

    def test_news_query_detection(self):
        """Test news query detection"""
        assert detect_query_type("新聞") == "news"
        assert detect_query_type("NEWS") == "news"

    def test_stock_query_detection(self):
        """Test stock query detection"""
        assert detect_query_type("AAPL") == "stock"
        assert detect_query_type("aapl") == "stock"
        assert detect_query_type("TSLA") == "stock"

    def test_unrecognized_query(self):
        """Test unrecognized queries"""
        assert detect_query_type("不存在的查詢") is None
        assert detect_query_type("TOOLONGCODE") is None
        assert detect_query_type("123") is None
