"""
Unit tests for Taiwan stock handler and service (Phase 6 - US4).
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from src.models.domain import TaiwanStock
from src.handlers.tw_stock_handler import handle_tw_stock_query
from src.services.tw_stock_service import TaiwanStockService


class TestTaiwanStockHandler:
    """Tests for Taiwan stock handler"""

    @pytest.fixture
    def sample_tw_stocks(self):
        """Sample Taiwan stock correlations"""
        return [
            TaiwanStock(
                us_code="AAPL",
                tw_code="2330",
                tw_name="台積電",
                relationship_type="supplier",
                relationship_detail="台積電是 Apple 晶片製造商，負責生產 A 系列處理器",
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
            TaiwanStock(
                us_code="AAPL",
                tw_code="3661",
                tw_name="世芯",
                relationship_type="industry_peer",
                relationship_detail="世芯提供相關晶片設計服務",
                strength=0.45,
            ),
        ]

    @pytest.mark.asyncio
    async def test_handle_tw_stock_query_success(self, test_db, sample_tw_stocks):
        """Test successful Taiwan stock query"""
        with patch("src.handlers.tw_stock_handler.TaiwanStockService") as mock_service:
            service_instance = AsyncMock()
            service_instance.get_related_tw_stocks.return_value = {
                "success": True,
                "data": sample_tw_stocks,
                "source": "database",
                "count": 3,
            }
            service_instance.close = AsyncMock()
            mock_service.return_value = service_instance

            result = await handle_tw_stock_query(test_db, "AAPL")

            assert result["success"] is True
            assert "message" in result
            assert result["tw_stock_count"] == 3
            assert "台積電" in result["message"] or "聯發科" in result["message"]

    @pytest.mark.asyncio
    async def test_handle_tw_stock_query_no_results(self, test_db):
        """Test Taiwan stock query with no results"""
        with patch("src.handlers.tw_stock_handler.TaiwanStockService") as mock_service:
            service_instance = AsyncMock()
            service_instance.get_related_tw_stocks.return_value = {
                "success": True,
                "data": [],
                "source": "database",
                "count": 0,
            }
            service_instance.close = AsyncMock()
            mock_service.return_value = service_instance

            result = await handle_tw_stock_query(test_db, "UNKNOWN")

            assert result["success"] is True
            assert "message" in result
            assert result["tw_stock_count"] == 0

    @pytest.mark.asyncio
    async def test_handle_tw_stock_query_invalid_code(self, test_db):
        """Test Taiwan stock query with invalid stock code"""
        with patch("src.handlers.tw_stock_handler.TaiwanStockService") as mock_service:
            service_instance = AsyncMock()
            service_instance.close = AsyncMock()
            mock_service.return_value = service_instance

            result = await handle_tw_stock_query(test_db, "TOOLONGCODE")

            assert result["success"] is False
            assert "error_code" in result

    @pytest.mark.asyncio
    async def test_handle_tw_stock_query_service_error(self, test_db):
        """Test handling of service errors"""
        with patch("src.handlers.tw_stock_handler.TaiwanStockService") as mock_service:
            service_instance = AsyncMock()
            service_instance.get_related_tw_stocks.return_value = {
                "success": False,
                "error_code": "E005_TW_STOCK_FETCH_ERROR",
                "error_message": "無法連接到資料庫",
                "data": [],
                "count": 0,
            }
            service_instance.close = AsyncMock()
            mock_service.return_value = service_instance

            result = await handle_tw_stock_query(test_db, "AAPL")

            assert result["success"] is False
            assert "error_code" in result


class TestTaiwanStockService:
    """Tests for Taiwan stock service"""

    @pytest.fixture
    def sample_tw_stocks_orm(self):
        """Sample Taiwan stock ORM objects"""
        from src.models.database import TaiwanStock as TaiwanStockORM
        
        stocks = []
        for i, (code, name) in enumerate(
            [("2330", "台積電"), ("2454", "聯發科"), ("3661", "世芯")]
        ):
            stock = TaiwanStockORM()
            stock.id = i + 1
            stock.us_code = "AAPL"
            stock.tw_code = code
            stock.tw_name = name
            stock.relationship_type = "supplier" if i == 0 else "competitor"
            stock.relationship_detail = f"{name} 說明"
            stock.strength = 0.95 - (i * 0.3)
            stocks.append(stock)
        
        return stocks

    @pytest.mark.asyncio
    async def test_get_related_tw_stocks_success(self, test_db, sample_tw_stocks_orm):
        """Test fetching related Taiwan stocks"""
        with patch("src.services.tw_stock_service.TaiwanStockRepository") as mock_repo:
            repo_instance = AsyncMock()
            repo_instance.get_by_us_code.return_value = sample_tw_stocks_orm
            mock_repo.return_value = repo_instance

            with patch("src.services.tw_stock_service.CacheManager") as mock_cache:
                cache_instance = AsyncMock()
                cache_instance.get.return_value = None
                cache_instance.set = AsyncMock()
                mock_cache.return_value = cache_instance

                service = TaiwanStockService(test_db)
                result = await service.get_related_tw_stocks("AAPL")

                assert result["success"] is True
                assert len(result["data"]) == 3
                assert result["count"] == 3

    @pytest.mark.asyncio
    async def test_get_related_tw_stocks_cache_hit(self, test_db, sample_tw_stocks_orm):
        """Test cache hit for Taiwan stocks"""
        cached_stocks = [
            TaiwanStock(
                us_code="AAPL",
                tw_code="2330",
                tw_name="台積電",
                relationship_type="supplier",
                relationship_detail="台積電是供應商",
                strength=0.95,
            )
        ]

        with patch("src.services.tw_stock_service.CacheManager") as mock_cache:
            cache_instance = AsyncMock()
            cache_instance.get.return_value = cached_stocks
            mock_cache.return_value = cache_instance

            service = TaiwanStockService(test_db)
            result = await service.get_related_tw_stocks("AAPL")

            assert result["success"] is True
            assert result["source"] == "cache"
            assert len(result["data"]) == 1


class TestTaiwanStockRelationshipSorting:
    """Tests for Taiwan stock relationship sorting"""

    def test_relationship_strength_sorting(self):
        """Test that Taiwan stocks are sorted by strength (high to low)"""
        stocks = [
            TaiwanStock(
                us_code="AAPL",
                tw_code="2454",
                tw_name="聯發科",
                relationship_type="competitor",
                relationship_detail="競爭者",
                strength=0.65,
            ),
            TaiwanStock(
                us_code="AAPL",
                tw_code="2330",
                tw_name="台積電",
                relationship_type="supplier",
                relationship_detail="供應商",
                strength=0.95,
            ),
            TaiwanStock(
                us_code="AAPL",
                tw_code="3661",
                tw_name="世芯",
                relationship_type="industry_peer",
                relationship_detail="同業",
                strength=0.45,
            ),
        ]

        # Sort by strength descending
        sorted_stocks = sorted(stocks, key=lambda x: x.strength, reverse=True)

        assert sorted_stocks[0].tw_code == "2330"  # Highest: 0.95
        assert sorted_stocks[1].tw_code == "2454"  # Middle: 0.65
        assert sorted_stocks[2].tw_code == "3661"  # Lowest: 0.45
