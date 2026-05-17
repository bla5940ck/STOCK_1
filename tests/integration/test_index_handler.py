"""
Unit tests for index handler and market data service.
"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from src.models.domain import Index, DataSourceEnum
from src.handlers.index_handler import handle_index_query


class TestIndexHandler:
    """Tests for index query handler"""

    @pytest.fixture
    def sample_indices(self):
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

    @pytest.mark.asyncio
    async def test_handle_index_query_success(self, test_db, sample_indices):
        """Test successful index query"""
        # Mock the market data service
        with patch("src.handlers.index_handler.MarketDataService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            
            mock_service.get_indices.return_value = {
                "success": True,
                "data": sample_indices,
                "source": "yahoo_finance",
            }
            
            result = await handle_index_query(test_db)
            
            assert result["success"] is True
            assert "message" in result
            assert result["count"] == 3
            assert "美股" in result["message"] or "S&P" in result["message"]

    @pytest.mark.asyncio
    async def test_handle_index_query_failure(self, test_db):
        """Test failed index query"""
        with patch("src.handlers.index_handler.MarketDataService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            
            mock_service.get_indices.return_value = {
                "success": False,
                "error_code": "E003_API_ERROR",
                "error_message": "無法取得指數數據",
            }
            
            result = await handle_index_query(test_db)
            
            assert result["success"] is False
            assert "error_code" in result
            assert "❌" in result["message"]

    @pytest.mark.asyncio
    async def test_handle_index_query_exception(self, test_db):
        """Test exception handling"""
        with patch("src.handlers.index_handler.MarketDataService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            
            mock_service.get_indices.side_effect = Exception("Unexpected error")
            
            result = await handle_index_query(test_db)
            
            assert result["success"] is False
            assert "E999_INTERNAL_ERROR" in result["error_code"]


class TestMarketDataService:
    """Tests for market data service"""

    @pytest.mark.asyncio
    async def test_get_indices_from_cache(self, test_db):
        """Test retrieving indices from cache"""
        from src.services.market_data import MarketDataService
        
        service = MarketDataService(test_db)
        
        # Mock cache to return data
        with patch.object(service.cache_manager, "get") as mock_get:
            mock_get.return_value = {
                "indices": [
                    {
                        "id": "^GSPC",
                        "zh_name": "S&P 500",
                        "current_price": "4500.25",
                        "previous_close": "4480.00",
                        "change_amount": "20.25",
                        "change_percent": "0.45",
                        "high_52w": "4800.00",
                        "low_52w": "4000.00",
                        "last_updated": datetime.utcnow().isoformat(),
                        "data_source": "yahoo_finance",
                    }
                ]
            }
            
            result = await service.get_indices()
            
            assert result["success"] is True
            assert result["source"] == "cache"
            assert len(result["data"]) > 0

    @pytest.mark.asyncio
    async def test_get_indices_yahoo_finance_success(self, test_db):
        """Test successful fetch from Yahoo Finance"""
        from src.services.market_data import MarketDataService
        
        service = MarketDataService(test_db)
        
        # Mock cache miss
        with patch.object(service.cache_manager, "get", return_value=None):
            # Mock Yahoo Finance success
            with patch.object(service.yahoo_client, "fetch_indices") as mock_fetch:
                index = Index(
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
                )
                mock_fetch.return_value = {"^GSPC": index}
                
                # Mock cache set
                with patch.object(service.cache_manager, "set", return_value=True):
                    result = await service.get_indices()
                    
                    assert result["success"] is True
                    assert result["source"] == "yahoo_finance"


class TestIndexValidation:
    """Tests for index query validation"""

    def test_index_keyword_detection(self):
        """Test detection of index keywords"""
        from src.utils.validators import is_index_keyword
        
        assert is_index_keyword("美股")
        assert is_index_keyword("指數")
        assert is_index_keyword("index")
        assert is_index_keyword("INDEX")
        assert not is_index_keyword("股票")
        assert not is_index_keyword("news")

    def test_query_text_validation(self):
        """Test query text validation"""
        from src.utils.validators import validate_query_text
        
        assert validate_query_text("美股") == "美股"
        assert validate_query_text("  指數  ") == "指數"
        assert validate_query_text("INDEX") == "INDEX"
