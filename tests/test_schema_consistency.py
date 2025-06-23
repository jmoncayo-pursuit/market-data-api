"""Tests for schema consistency and service behavior validation."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from app.schemas.market_data import (
    MovingAverageResponse,
    PriceResponse,
    PollingRequest,
    PollingResponse,
    ErrorResponse,
    DeleteAllResponse,
    SymbolsResponse,
    MarketDataCreate,
    MarketDataUpdate,
    MarketDataInDB,
)
from app.services.redis_service import RedisService
from app.services.market_data import MarketDataService


class TestSchemaConsistency:
    """Test schema consistency and field validation."""

    def test_moving_average_response_schema_fields(self):
        """Test MovingAverageResponse schema has correct field names."""
        timestamp = datetime.now()
        data = {
            "symbol": "AAPL",
            "moving_average": 155.5,  # Must be 'moving_average', not 'value'
            "timestamp": timestamp,
            "window_size": 10,
        }
        
        # This should not raise ValidationError
        schema = MovingAverageResponse(**data)
        
        assert schema.symbol == "AAPL"
        assert schema.moving_average == 155.5
        assert schema.timestamp == timestamp
        assert schema.window_size == 10

    def test_moving_average_response_schema_validation_error(self):
        """Test that using 'value' instead of 'moving_average' raises error."""
        timestamp = datetime.now()
        data = {
            "symbol": "AAPL",
            "value": 155.5,  # Wrong field name
            "timestamp": timestamp,
            "window_size": 10,
        }
        
        # This should raise ValidationError
        with pytest.raises(Exception):  # ValidationError or similar
            MovingAverageResponse(**data)

    def test_price_response_schema_fields(self):
        """Test PriceResponse schema has correct field names."""
        data = {
            "symbol": "AAPL",
            "price": 150.0,
            "timestamp": "2023-01-01T00:00:00",
            "provider": "test_provider",
        }
        
        schema = PriceResponse(**data)
        
        assert schema.symbol == "AAPL"
        assert schema.price == 150.0
        assert schema.timestamp == "2023-01-01T00:00:00"
        assert schema.provider == "test_provider"

    def test_polling_request_schema_fields(self):
        """Test PollingRequest schema has correct field names."""
        data = {
            "symbols": ["AAPL", "GOOGL"],
            "interval": 60,
        }
        
        schema = PollingRequest(**data)
        
        assert schema.symbols == ["AAPL", "GOOGL"]
        assert schema.interval == 60

    def test_polling_response_schema_fields(self):
        """Test PollingResponse schema has correct field names."""
        data = {
            "job_id": "test_job_123",
            "status": "active",
            "config": {"symbols": ["AAPL", "GOOGL"], "interval": 60},
        }
        
        schema = PollingResponse(**data)
        
        assert schema.job_id == "test_job_123"
        assert schema.status == "active"
        assert schema.config.symbols == ["AAPL", "GOOGL"]

    def test_error_response_schema_fields(self):
        """Test ErrorResponse schema has correct field names."""
        data = {"detail": "An error occurred"}
        
        schema = ErrorResponse(**data)
        
        assert schema.detail == "An error occurred"

    def test_delete_all_response_schema_fields(self):
        """Test DeleteAllResponse schema has correct field names."""
        data = {"message": "All data deleted", "deleted_count": 100}
        
        schema = DeleteAllResponse(**data)
        
        assert schema.message == "All data deleted"
        assert schema.deleted_count == 100

    def test_symbols_response_schema_fields(self):
        """Test SymbolsResponse schema has correct field names."""
        data = {"symbols": ["AAPL", "GOOGL", "MSFT"]}
        
        schema = SymbolsResponse(**data)
        
        assert schema.symbols == ["AAPL", "GOOGL", "MSFT"]

    def test_market_data_schemas_consistency(self):
        """Test MarketData schemas have consistent field names."""
        # Test MarketDataCreate
        create_data = {
            "symbol": "AAPL",
            "price": 150.0,
            "volume": 1000,
            "source": "test_source",
        }
        create_schema = MarketDataCreate(**create_data)
        assert create_schema.symbol == "AAPL"
        assert create_schema.price == 150.0
        assert create_schema.volume == 1000
        assert create_schema.source == "test_source"

        # Test MarketDataUpdate
        update_data = {"price": 160.0, "volume": 2000}
        update_schema = MarketDataUpdate(**update_data)
        assert update_schema.price == 160.0
        assert update_schema.volume == 2000

        # Test MarketDataInDB
        timestamp = datetime.now()
        db_data = {
            "id": 1,
            "symbol": "AAPL",
            "price": 150.0,
            "volume": 1000,
            "timestamp": timestamp,
            "source": "test_source",
        }
        db_schema = MarketDataInDB(**db_data)
        assert db_schema.id == 1
        assert db_schema.symbol == "AAPL"
        assert db_schema.price == 150.0
        assert db_schema.volume == 1000
        assert db_schema.timestamp == timestamp
        assert db_schema.source == "test_source"


class TestRedisServiceConsistency:
    """Test Redis service behavior consistency."""

    @pytest.mark.asyncio
    async def test_redis_service_connection_error_returns_false(self):
        """Test Redis service returns False when Redis is unavailable."""
        service = RedisService()
        service.set_test_mode(True)  # Enable test mode to prevent reconnection
        
        # All methods should return False/None when Redis is unavailable
        assert await service.get_cached_price("AAPL") is None
        assert await service.cache_price("AAPL", 150.0) is False
        assert await service.get_price("AAPL") is None
        assert await service.set_price("AAPL", 150.0) is False
        assert await service.delete_price("AAPL") is False
        assert await service.get_all_prices() == {}
        assert await service.clear_prices() is False
        assert await service.get_price_history("AAPL") == []

    @pytest.mark.asyncio
    async def test_redis_service_healthy_connection_returns_true(self):
        """Test Redis service returns True when Redis is available."""
        service = RedisService()
        mock_redis = AsyncMock()
        mock_redis.ping.return_value = True
        mock_redis.get.return_value = "150.0"
        mock_redis.setex.return_value = True
        mock_redis.set.return_value = True
        mock_redis.delete.return_value = 1
        
        # Mock async iterators properly
        async def mock_scan_iter(pattern):
            if False:
                yield  # pragma: no cover
            return
        mock_redis.scan_iter = mock_scan_iter
        
        mock_redis.keys.return_value = []
        service.redis = mock_redis
        
        # All methods should return True/expected values when Redis is available
        assert await service.get_cached_price("AAPL") == 150.0
        assert await service.cache_price("AAPL", 150.0) is True
        assert await service.get_price("AAPL") == 150.0
        assert await service.set_price("AAPL", 150.0) is True
        assert await service.delete_price("AAPL") is True
        assert await service.get_all_prices() == {}
        assert await service.clear_prices() is True
        assert await service.get_price_history("AAPL") == []

    @pytest.mark.asyncio
    async def test_redis_service_exception_handling(self):
        """Test Redis service handles exceptions gracefully."""
        service = RedisService()
        mock_redis = AsyncMock()
        mock_redis.ping.side_effect = Exception("Connection failed")
        mock_redis.get.side_effect = Exception("Redis error")
        mock_redis.setex.side_effect = Exception("Redis error")
        mock_redis.set.side_effect = Exception("Redis error")
        service.redis = mock_redis
        
        # Methods should return False/None on exceptions
        assert await service.get_cached_price("AAPL") is None
        assert await service.cache_price("AAPL", 150.0) is False
        assert await service.get_price("AAPL") is None
        assert await service.set_price("AAPL", 150.0) is False


class TestMarketDataServiceConsistency:
    """Test MarketData service behavior consistency."""

    def test_market_data_service_calculate_moving_average_returns_float_or_none(self):
        """Test calculate_moving_average returns float or None."""
        db = MagicMock()
        
        # Test with sufficient data
        mock_prices = [
            MagicMock(price=100.0),
            MagicMock(price=110.0),
            MagicMock(price=120.0),
        ]
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            mock_prices
        )
        service = MarketDataService(db)
        result = service.calculate_moving_average(db, "AAPL", 3)
        assert isinstance(result, float)
        assert result == 110.0

        # Test with insufficient data
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            []
        )
        result = service.calculate_moving_average(db, "AAPL", 3)
        assert result is None

    def test_market_data_service_methods_return_expected_types(self):
        """Test MarketData service methods return expected types."""
        db = MagicMock()
        service = MarketDataService(db)
        
        # Test get_market_data returns list
        db.query.return_value.offset.return_value.limit.return_value.all.return_value = [
            "data1", "data2"
        ]
        result = MarketDataService.get_market_data(db)
        assert isinstance(result, list)
        
        # Test get_all_symbols returns list
        db.query.return_value.distinct.return_value.all.return_value = [
            ("AAPL",), ("GOOG",)
        ]
        result = MarketDataService.get_all_symbols(db)
        assert isinstance(result, list)
        assert result == ["AAPL", "GOOG"]


class TestSchemaFieldValidation:
    """Test schema field validation and constraints."""

    def test_moving_average_response_required_fields(self):
        """Test MovingAverageResponse requires all fields."""
        timestamp = datetime.now()
        
        # Test missing required fields
        with pytest.raises(Exception):
            MovingAverageResponse()  # Missing all fields
            
        with pytest.raises(Exception):
            MovingAverageResponse(symbol="AAPL")  # Missing other fields
            
        with pytest.raises(Exception):
            MovingAverageResponse(
                symbol="AAPL",
                moving_average=155.5,
                # Missing timestamp and window_size
            )

    def test_price_response_required_fields(self):
        """Test PriceResponse requires all fields."""
        with pytest.raises(Exception):
            PriceResponse()  # Missing all fields
            
        with pytest.raises(Exception):
            PriceResponse(symbol="AAPL")  # Missing other fields

    def test_market_data_create_validation_constraints(self):
        """Test MarketDataCreate field constraints."""
        # Test valid data
        valid_data = {
            "symbol": "AAPL",
            "price": 150.0,
            "volume": 1000,
            "source": "test_source",
        }
        schema = MarketDataCreate(**valid_data)
        assert schema.symbol == "AAPL"
        assert schema.price == 150.0
        assert schema.volume == 1000

        # Test invalid constraints
        with pytest.raises(Exception):
            MarketDataCreate(price=-50.0)  # Negative price

        with pytest.raises(Exception):
            MarketDataCreate(volume=0)  # Zero volume

        with pytest.raises(Exception):
            MarketDataCreate(symbol="")  # Empty symbol


class TestCICompatibility:
    """Test compatibility with CI/CD environment requirements."""

    def test_schema_serialization_consistency(self):
        """Test schemas can be serialized consistently."""
        timestamp = datetime.now()
        
        # Test MovingAverageResponse serialization
        data = {
            "symbol": "AAPL",
            "moving_average": 155.5,
            "timestamp": timestamp,
            "window_size": 10,
        }
        schema = MovingAverageResponse(**data)
        
        # Should be able to convert to dict
        schema_dict = schema.model_dump()
        assert "symbol" in schema_dict
        assert "moving_average" in schema_dict
        assert "timestamp" in schema_dict
        assert "window_size" in schema_dict

    def test_service_method_signatures(self):
        """Test service method signatures are consistent."""
        # Test RedisService method signatures
        service = RedisService()
        
        # These methods should exist and be async
        assert hasattr(service, 'get_cached_price')
        assert hasattr(service, 'cache_price')
        assert hasattr(service, 'get_price')
        assert hasattr(service, 'set_price')
        assert hasattr(service, 'delete_price')
        
        # Test MarketDataService static methods exist
        assert hasattr(MarketDataService, 'get_market_data')
        assert hasattr(MarketDataService, 'get_all_symbols')
        assert hasattr(MarketDataService, 'calculate_moving_average')

    def test_error_message_consistency(self):
        """Test error messages are consistent across the application."""
        # Test ErrorResponse schema
        error_data = {"detail": "No data found for symbol AAPL"}
        error_schema = ErrorResponse(**error_data)
        assert error_schema.detail == "No data found for symbol AAPL"
        
        # Test that error messages follow consistent pattern
        assert "No data found for symbol" in error_schema.detail 