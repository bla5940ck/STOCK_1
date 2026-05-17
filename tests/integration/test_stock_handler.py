"""
Unit tests for stock handler and news handler.
"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import AsyncMock, patch

from src.models.domain import Stock, NewsArticle, DataSourceEnum
from src.handlers.stock_handler import handle_stock_query
from src.handlers.news_handler import handle_news_query


class TestStockHandler:
    """Tests for stock query handler"""

    @pytest.fixture
    def sample_stock(self):
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
    def sample_news(self):
        """Sample news articles"""
        return [
            NewsArticle(
                id="news_001",
                title="蘋果發佈新 iPhone",
                summary="蘋果公司宣佈發佈新款 iPhone，配備全新 A18 晶片和改進的相機系統...",
                source="科技新聞",
                url="https://example.com/news1",
                published_at=datetime.utcnow(),
                category="earnings",
                related_stocks=["AAPL"],
                relevance_score=0.95,
                fetched_at=datetime.utcnow(),
            ),
        ]

    @pytest.mark.asyncio
    async def test_handle_stock_query_success(self, test_db, sample_stock, sample_news):
        """Test successful stock query"""
        with patch("src.handlers.stock_handler.MarketDataService") as mock_market_service:
            with patch("src.handlers.stock_handler.NewsService") as mock_news_service:
                # Mock market service
                market_service_instance = AsyncMock()
                market_service_instance.get_stock.return_value = {
                    "success": True,
                    "data": sample_stock,
                }
                market_service_instance.close = AsyncMock()
                mock_market_service.return_value = market_service_instance

                # Mock news service
                news_service_instance = AsyncMock()
                news_service_instance.fetch_related_news.return_value = {
                    "success": True,
                    "data": sample_news,
                }
                news_service_instance.close = AsyncMock()
                mock_news_service.return_value = news_service_instance

                result = await handle_stock_query(test_db, "AAPL")

                assert result["success"] is True
                assert "message" in result
                assert result["news_count"] == 1
                assert "AAPL" in result["message"] or "蘋果" in result["message"]

    @pytest.mark.asyncio
    async def test_handle_stock_query_not_found(self, test_db):
        """Test stock not found"""
        with patch("src.handlers.stock_handler.MarketDataService") as mock_market_service:
            with patch("src.handlers.stock_handler.NewsService") as mock_news_service:
                market_service_instance = AsyncMock()
                market_service_instance.get_stock.return_value = {
                    "success": False,
                    "error_code": "E004_STOCK_NOT_FOUND",
                    "error_message": "無法找到該股票",
                }
                market_service_instance.close = AsyncMock()
                mock_market_service.return_value = market_service_instance

                news_service_instance = AsyncMock()
                news_service_instance.close = AsyncMock()
                mock_news_service.return_value = news_service_instance

                result = await handle_stock_query(test_db, "INVALID")

                assert result["success"] is False
                assert "error_code" in result


class TestNewsHandler:
    """Tests for news query handler"""

    @pytest.fixture
    def sample_news(self):
        """Sample news articles"""
        return [
            NewsArticle(
                id="news_econ_001",
                title="聯準會升息決定",
                summary="美國聯邦準備委員會宣佈升息 0.5%，以控制通脹，市場反應積極...",
                source="路透社",
                url="https://example.com/news",
                published_at=datetime.utcnow(),
                category="economic",
                related_stocks=["SPY", "QQQ"],
                relevance_score=0.90,
                fetched_at=datetime.utcnow(),
            ),
        ]

    @pytest.mark.asyncio
    async def test_handle_news_query_success(self, test_db, sample_news):
        """Test successful news query"""
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
            assert "message" in result
            assert result["article_count"] == 1
            assert "新聞" in result["message"] or "升息" in result["message"]

    @pytest.mark.asyncio
    async def test_handle_news_query_failure(self, test_db):
        """Test failed news query"""
        with patch("src.handlers.news_handler.NewsService") as mock_news_service:
            news_service_instance = AsyncMock()
            news_service_instance.fetch_economic_news.return_value = {
                "success": False,
                "error_code": "E003_API_ERROR",
                "error_message": "無法取得新聞數據",
            }
            news_service_instance.close = AsyncMock()
            mock_news_service.return_value = news_service_instance

            result = await handle_news_query(test_db)

            assert result["success"] is False
            assert "error_code" in result


class TestQueryDetection:
    """Tests for query type detection"""

    def test_detect_stock_query(self):
        """Test stock code detection"""
        from src.utils.validators import detect_query_type
        
        assert detect_query_type("AAPL") == "stock"
        assert detect_query_type("TSLA") == "stock"
        assert detect_query_type("GOOG") == "stock"

    def test_detect_news_query(self):
        """Test news keyword detection"""
        from src.utils.validators import detect_query_type
        
        assert detect_query_type("新聞") == "news"
        assert detect_query_type("news") == "news"
        assert detect_query_type("NEWS") == "news"

    def test_detect_index_query(self):
        """Test index keyword detection"""
        from src.utils.validators import detect_query_type
        
        assert detect_query_type("美股") == "index"
        assert detect_query_type("指數") == "index"

    def test_stock_code_validation(self):
        """Test stock code validation"""
        from src.utils.validators import validate_stock_code
        from src.exceptions import ValidationError
        
        assert validate_stock_code("AAPL") == "AAPL"
        assert validate_stock_code("aapl") == "AAPL"
        assert validate_stock_code("tsla") == "TSLA"
        
        with pytest.raises(ValidationError):
            validate_stock_code("TOOLONG")
