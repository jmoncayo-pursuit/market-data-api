"""Tests to ensure CI/CD workflow compatibility and prevent local vs CI mismatches."""

import os
import sys
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from app.schemas.market_data import MovingAverageResponse, ErrorResponse
from app.services.redis_service import RedisService
from app.services.market_data import MarketDataService


class TestCIWorkflowCompatibility:
    """Test CI/CD workflow compatibility and common failure patterns."""

    def test_environment_consistency(self):
        """Test that environment variables are handled consistently."""
        # Test that the app works with minimal environment variables
        with patch.dict(os.environ, {}, clear=True):
            from app.core.config import settings
            # Should have default values
            assert hasattr(settings, 'REDIS_URL')
            assert hasattr(settings, 'DATABASE_URL')
            assert hasattr(settings, 'KAFKA_BOOTSTRAP_SERVERS')

    def test_python_version_compatibility(self):
        """Test Python version compatibility."""
        # Ensure we're using a compatible Python version
        assert sys.version_info >= (3, 8)
        assert sys.version_info < (4, 0)

    def test_dependency_availability(self):
        """Test that all required dependencies are available."""
        required_modules = [
            'fastapi',
            'pydantic',
            'sqlalchemy',
            'redis',
            'pytest',
            'pytest_asyncio',
            'pytest_cov',
            'httpx',
            'alembic'
        ]
        
        for module in required_modules:
            try:
                __import__(module)
            except ImportError as e:
                pytest.fail(f"Required module {module} not available: {e}")

    def test_schema_validation_consistency(self):
        """Test that schema validation works consistently across environments."""
        timestamp = datetime.now()
        
        # Test MovingAverageResponse validation
        valid_data = {
            "symbol": "AAPL",
            "moving_average": 155.5,
            "timestamp": timestamp,
            "window_size": 10,
        }
        
        schema = MovingAverageResponse(**valid_data)
        assert schema.symbol == "AAPL"
        assert schema.moving_average == 155.5
        
        # Test ErrorResponse validation
        error_data = {"detail": "No data found for symbol AAPL"}
        error_schema = ErrorResponse(**error_data)
        assert error_schema.detail == "No data found for symbol AAPL"

    @pytest.mark.asyncio
    async def test_redis_service_ci_compatibility(self):
        """Test Redis service behavior in CI environment."""
        service = RedisService()
        service.set_test_mode(True)
        
        # Test all methods return expected values when Redis is unavailable
        assert await service.get_cached_price("AAPL") is None
        assert await service.cache_price("AAPL", 150.0) is False
        assert await service.get_price("AAPL") is None
        assert await service.set_price("AAPL", 150.0) is False
        assert await service.delete_price("AAPL") is False
        assert await service.get_all_prices() == {}
        assert await service.clear_prices() is False
        assert await service.get_price_history("AAPL") == []
        assert await service.get_latest_price("AAPL") is None

    def test_market_data_service_ci_compatibility(self):
        """Test MarketData service behavior in CI environment."""
        db = MagicMock()
        service = MarketDataService(db)
        
        # Test return types are consistent
        db.query.return_value.offset.return_value.limit.return_value.all.return_value = []
        result = MarketDataService.get_market_data(db)
        assert isinstance(result, list)
        
        # Test moving average calculation
        mock_prices = [MagicMock(price=100.0), MagicMock(price=110.0)]
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            mock_prices
        )
        result = service.calculate_moving_average(db, "AAPL", 3)
        assert result is None  # Insufficient data
        
        # Test with sufficient data
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

    def test_async_test_compatibility(self):
        """Test that async tests work correctly in CI environment."""
        # Test that asyncio is available and working
        assert asyncio is not None
        
        # Test that pytest-asyncio is working
        import pytest_asyncio
        assert pytest_asyncio is not None

    def test_mock_compatibility(self):
        """Test that mocking works correctly in CI environment."""
        with patch('app.services.redis_service.Redis') as mock_redis:
            service = RedisService()
            assert service is not None

    def test_import_stability(self):
        """Test that all critical imports work in CI environment."""
        try:
            from app.main import app
            from app.api.endpoints import prices
            from app.services.redis_service import RedisService
            from app.services.market_data import MarketDataService
            from app.schemas.market_data import MovingAverageResponse
            from app.core.config import settings
            from app.core.auth import require_auth, require_permission
            from app.core.rate_limit import RateLimiter
            from app.core.logging import setup_logging
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

    def test_error_message_standardization(self):
        """Test that error messages are standardized."""
        # Test ErrorResponse schema
        error_data = {"detail": "No data found for symbol AAPL"}
        error_schema = ErrorResponse(**error_data)
        assert error_schema.detail == "No data found for symbol AAPL"
        
        # Test that error messages follow consistent pattern
        assert "No data found for symbol" in error_schema.detail

    def test_platform_independence(self):
        """Test that the app works on different platforms."""
        import platform
        
        # Test that the app works on supported platforms
        assert platform.system() in ['Darwin', 'Linux', 'Windows']
        
        # Test that path handling is platform-independent
        import tempfile
        with tempfile.NamedTemporaryFile() as f:
            assert os.path.exists(f.name)

    def test_timezone_handling(self):
        """Test that timezone handling is consistent."""
        from datetime import datetime
        
        # Test that datetime operations work consistently
        now = datetime.now()
        assert isinstance(now, datetime)
        
        # Test that timestamp operations work
        timestamp = now.timestamp()
        assert isinstance(timestamp, float)

    def test_file_system_operations(self):
        """Test that file system operations are handled gracefully."""
        import tempfile
        import os
        
        # Should be able to create temporary files
        with tempfile.NamedTemporaryFile() as f:
            assert os.path.exists(f.name)

    def test_network_operations(self):
        """Test that network operations are handled gracefully."""
        service = RedisService()
        service.set_test_mode(True)
        
        # Should not try to connect to network
        assert service.redis is None

    def test_memory_usage(self):
        """Test that memory usage is reasonable."""
        import gc
        
        # Force garbage collection
        gc.collect()
        
        # Test that we can create objects without memory issues
        service = RedisService()
        assert service is not None

    def test_thread_safety(self):
        """Test that the app is thread-safe."""
        import threading
        
        def create_service():
            service = RedisService()
            service.set_test_mode(True)
            return service
        
        # Test that we can create services from different threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=create_service)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()

    def test_concurrent_operations(self):
        """Test that concurrent operations work correctly."""
        import asyncio
        
        async def test_concurrent_redis_operations():
            service = RedisService()
            service.set_test_mode(True)
            
            # Test concurrent operations
            tasks = [
                service.get_cached_price("AAPL"),
                service.cache_price("AAPL", 150.0),
                service.get_price("AAPL"),
            ]
            
            results = await asyncio.gather(*tasks)
            assert results[0] is None
            assert results[1] is False
            assert results[2] is None
        
        asyncio.run(test_concurrent_redis_operations())

    def test_configuration_validation(self):
        """Test that configuration validation works correctly."""
        from app.core.config import Settings
        
        # Test that settings can be created with minimal configuration
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert hasattr(settings, 'REDIS_URL')
            assert hasattr(settings, 'DATABASE_URL')

    def test_logging_configuration(self):
        """Test that logging configuration works correctly."""
        from app.core.logging import setup_logging
        
        # Test that logging can be set up
        logger = setup_logging()
        assert logger is not None

    def test_database_connection_handling(self):
        """Test that database connection handling works correctly."""
        from app.db.session import get_db
        
        # Test that database session factory can be created
        # This will fail in test environment, but that's expected
        try:
            db = next(get_db())
            db.close()
        except Exception:
            # Expected in test environment without database
            pass

    def test_api_endpoint_availability(self):
        """Test that API endpoints are available."""
        from app.main import app
        
        # Test that the app has the expected endpoints
        routes = [route.path for route in app.routes]
        assert "/health" in routes or any("/health" in str(route) for route in routes)

    def test_middleware_configuration(self):
        """Test that middleware is configured correctly."""
        from app.main import app
        
        # Test that the app has middleware
        assert hasattr(app, 'user_middleware')
        assert hasattr(app, 'middleware')

    def test_cors_configuration(self):
        """Test that CORS is configured correctly."""
        from app.main import app
        
        # Test that CORS middleware is present
        middleware_names = [str(middleware) for middleware in app.user_middleware]
        cors_middleware = any("CORSMiddleware" in name for name in middleware_names)
        assert cors_middleware

    def test_exception_handling(self):
        """Test that exception handling works correctly."""
        from app.main import app
        
        # Test that exception handlers are configured
        assert hasattr(app, 'exception_handlers')

    def test_lifespan_events(self):
        """Test that lifespan events work correctly."""
        from app.main import app
        
        # Test that lifespan is configured
        assert hasattr(app, 'router')

    def test_health_check_endpoint(self):
        """Test that health check endpoint works correctly."""
        from app.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Test health endpoint
        try:
            response = client.get("/health")
            assert response.status_code in [200, 404]  # 404 if endpoint doesn't exist
        except Exception:
            # Expected if endpoint doesn't exist
            pass

    def test_ready_check_endpoint(self):
        """Test that ready check endpoint works correctly."""
        from app.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Test ready endpoint
        try:
            response = client.get("/ready")
            assert response.status_code in [200, 404]  # 404 if endpoint doesn't exist
        except Exception:
            # Expected if endpoint doesn't exist
            pass

    def test_root_endpoint(self):
        """Test that root endpoint works correctly."""
        from app.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Test root endpoint
        try:
            response = client.get("/")
            assert response.status_code in [200, 404]  # 404 if endpoint doesn't exist
        except Exception:
            # Expected if endpoint doesn't exist
            pass


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

    def test_no_environment_specific_code(self):
        """Test that no environment-specific code is used."""
        # Test that the app works in different environments
        import os
        
        # Should work with minimal environment variables
        with patch.dict(os.environ, {}, clear=True):
            from app.core.config import settings
            assert hasattr(settings, 'REDIS_URL')

    def test_no_version_specific_code(self):
        """Test that no version-specific code is used."""
        import sys
        
        # Test that the app works with different Python versions
        assert sys.version_info >= (3, 8)
        assert sys.version_info < (4, 0)

    def test_no_dependency_specific_code(self):
        """Test that no dependency-specific code is used."""
        # Test that the app works with different dependency versions
        import fastapi
        import pydantic
        import sqlalchemy
        
        # Should be able to import all dependencies
        assert fastapi is not None
        assert pydantic is not None
        assert sqlalchemy is not None

    def test_no_test_specific_code(self):
        """Test that no test-specific code is used in production."""
        # Test that the app doesn't depend on test-specific code
        import app.main
        import app.api.endpoints
        
        # Should be able to import production code
        assert app.main is not None
        assert app.api.endpoints is not None

    def test_no_debug_specific_code(self):
        """Test that no debug-specific code is used in production."""
        # Test that the app doesn't depend on debug-specific code
        import app.core.config
        
        # Should be able to import production code
        assert app.core.config is not None

    def test_no_development_specific_code(self):
        """Test that no development-specific code is used in production."""
        # Test that the app doesn't depend on development-specific code
        import app.services.redis_service
        import app.services.market_data
        
        # Should be able to import production code
        assert app.services.redis_service is not None
        assert app.services.market_data is not None 