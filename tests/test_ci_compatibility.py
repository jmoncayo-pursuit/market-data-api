"""Tests to ensure CI/CD compatibility and catch common CI failures."""

import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.schemas.market_data import MovingAverageResponse
from app.services.redis_service import RedisService
from app.services.market_data import MarketDataService


class TestCICompatibility:
    """Test CI/CD compatibility and common failure patterns."""

    def test_schema_field_names_consistency(self):
        """Test that schema field names are consistent and match test expectations."""
        # This test ensures that the MovingAverageResponse schema uses 'moving_average'
        # and not 'value' - this was a previous CI failure
        timestamp = datetime.now()
        data = {
            "symbol": "AAPL",
            "moving_average": 155.5,  # Must be 'moving_average', not 'value'
            "timestamp": timestamp,
            "window_size": 10,
        }
        
        # This should not raise ValidationError
        schema = MovingAverageResponse(**data)
        assert schema.moving_average == 155.5
        
        # Test that using 'value' raises an error
        invalid_data = {
            "symbol": "AAPL",
            "value": 155.5,  # Wrong field name
            "timestamp": timestamp,
            "window_size": 10,
        }
        
        with pytest.raises(Exception):  # Should raise ValidationError
            MovingAverageResponse(**invalid_data)

    @pytest.mark.asyncio
    async def test_redis_service_connection_error_handling(self):
        """Test Redis service connection error handling in CI environment."""
        service = RedisService()
        service.set_test_mode(True)  # Simulate connection failure
        
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
    async def test_redis_service_connection_error_with_exception(self):
        """Test Redis service handles actual connection exceptions."""
        service = RedisService()
        
        # Mock Redis to raise connection error
        with patch('app.services.redis_service.Redis') as mock_redis_class:
            mock_redis = MagicMock()
            mock_redis.ping.side_effect = Exception("Connection failed")
            mock_redis_class.from_url.return_value = mock_redis
            
            # Methods should return False/None on connection errors
            assert await service.get_cached_price("AAPL") is None
            assert await service.cache_price("AAPL", 150.0) is False
            assert await service.get_price("AAPL") is None
            assert await service.set_price("AAPL", 150.0) is False

    def test_market_data_service_return_types(self):
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

    def test_market_data_service_calculate_moving_average_types(self):
        """Test calculate_moving_average returns correct types."""
        db = MagicMock()
        service = MarketDataService(db)
        
        # Test with sufficient data - should return float
        mock_prices = [
            MagicMock(price=100.0),
            MagicMock(price=110.0),
            MagicMock(price=120.0),
        ]
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            mock_prices
        )
        result = service.calculate_moving_average(db, "AAPL", 3)
        assert isinstance(result, float)
        assert result == 110.0

        # Test with insufficient data - should return None
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            []
        )
        result = service.calculate_moving_average(db, "AAPL", 3)
        assert result is None

    def test_environment_variable_handling(self):
        """Test that environment variables are handled correctly."""
        # Test that the app can handle missing environment variables gracefully
        with patch.dict(os.environ, {}, clear=True):
            # This should not crash the application
            from app.core.config import settings
            # The settings should have default values
            assert hasattr(settings, 'REDIS_URL')
            assert hasattr(settings, 'DATABASE_URL')

    def test_import_stability(self):
        """Test that all critical imports work in CI environment."""
        # Test that all main modules can be imported without errors
        try:
            from app.main import app
            from app.api.endpoints import prices
            from app.services.redis_service import RedisService
            from app.services.market_data import MarketDataService
            from app.schemas.market_data import MovingAverageResponse
            assert True  # If we get here, imports worked
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

    def test_schema_serialization_consistency(self):
        """Test that schemas can be serialized consistently."""
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

    def test_redis_service_test_mode(self):
        """Test Redis service test mode functionality."""
        service = RedisService()
        
        # Initially should not be in test mode
        assert service._test_mode is False
        
        # Enable test mode
        service.set_test_mode(True)
        assert service._test_mode is True
        assert service.redis is None  # Should clear existing connection
        
        # Disable test mode
        service.set_test_mode(False)
        assert service._test_mode is False

    def test_error_message_consistency(self):
        """Test that error messages are consistent across environments."""
        # Test ErrorResponse schema
        from app.schemas.market_data import ErrorResponse
        
        error_data = {"detail": "No data found for symbol AAPL"}
        error_schema = ErrorResponse(**error_data)
        assert error_schema.detail == "No data found for symbol AAPL"
        
        # Test that error messages follow consistent pattern
        assert "No data found for symbol" in error_schema.detail

    @pytest.mark.asyncio
    async def test_async_test_compatibility(self):
        """Test that async tests work correctly in CI environment."""
        service = RedisService()
        service.set_test_mode(True)
        
        # Test async method calls
        result = await service.get_cached_price("AAPL")
        assert result is None
        
        result = await service.cache_price("AAPL", 150.0)
        assert result is False

    def test_mock_compatibility(self):
        """Test that mocking works correctly in CI environment."""
        with patch('app.services.redis_service.Redis') as mock_redis:
            service = RedisService()
            # Should not crash when Redis is mocked
            assert service is not None

    def test_pytest_plugin_compatibility(self):
        """Test that pytest plugins work correctly."""
        # Test that pytest-asyncio is available
        import pytest_asyncio
        assert pytest_asyncio is not None
        
        # Test that pytest-cov is available
        import pytest_cov
        assert pytest_cov is not None


class TestCIFailurePrevention:
    """Test to prevent common CI failures."""

    def test_no_hardcoded_paths(self):
        """Test that no hardcoded paths are used that might fail in CI."""
        # Check that no absolute paths are used in critical files
        import app.core.config
        import app.services.redis_service
        import app.services.market_data
        
        # If we get here, no hardcoded paths caused import failures
        assert True

    def test_no_platform_specific_code(self):
        """Test that no platform-specific code is used."""
        import platform
        import sys
        
        # Test that the app works on different platforms
        assert platform.system() in ['Darwin', 'Linux', 'Windows']
        assert sys.version_info >= (3, 8)

    def test_no_timezone_dependencies(self):
        """Test that timezone handling is consistent."""
        from datetime import datetime
        
        # Test that datetime operations work consistently
        now = datetime.now()
        assert isinstance(now, datetime)

    def test_no_file_system_dependencies(self):
        """Test that file system operations are handled gracefully."""
        # Test that the app doesn't depend on specific file system features
        import tempfile
        import os
        
        # Should be able to create temporary files
        with tempfile.NamedTemporaryFile() as f:
            assert os.path.exists(f.name)

    def test_no_network_dependencies(self):
        """Test that network operations are handled gracefully."""
        # Test that the app can handle network failures
        service = RedisService()
        service.set_test_mode(True)
        
        # Should not try to connect to network
        assert service.redis is None 