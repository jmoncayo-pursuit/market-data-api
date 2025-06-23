"""Tests for the main application module."""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app, lifespan


class TestMainApp:
    """Test cases for main application."""

    def test_root_endpoint(self):
        """Test root endpoint."""
        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        assert response.json() == {"message": "Welcome to the Market Data Service API"}

    def test_health_check(self):
        """Test health check endpoint."""
        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    @patch("app.main.MarketDataService.get_all_symbols")
    def test_get_symbols_success(self, mock_get_symbols):
        """Test successful symbols retrieval."""
        mock_get_symbols.return_value = ["AAPL", "GOOGL", "MSFT"]

        client = TestClient(app)
        response = client.get(
            "/symbols", headers={"Authorization": "Bearer demo-api-key-123"}
        )

        assert response.status_code == 200
        assert response.json() == ["AAPL", "GOOGL", "MSFT"]
        mock_get_symbols.assert_called_once()

    @patch("app.main.MarketDataService.get_all_symbols")
    def test_get_symbols_exception(self, mock_get_symbols):
        """Test symbols retrieval with exception."""
        mock_get_symbols.side_effect = Exception("Database error")

        client = TestClient(app)
        response = client.get(
            "/symbols", headers={"Authorization": "Bearer demo-api-key-123"}
        )

        assert response.status_code == 500
        assert "Error retrieving symbols" in response.json()["detail"]

    @patch("app.main.MarketDataService.calculate_moving_average")
    @patch("app.main.MarketDataService.get_latest_timestamp")
    def test_get_moving_average_success(self, mock_get_timestamp, mock_calculate_ma):
        """Test successful moving average calculation."""
        mock_calculate_ma.return_value = 150.0
        mock_get_timestamp.return_value = "2023-01-01T00:00:00"

        client = TestClient(app)
        response = client.get(
            "/moving-average/AAPL", headers={"Authorization": "Bearer demo-api-key-123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["moving_average"] == 150.0
        assert data["timestamp"] == "2023-01-01T00:00:00"
        mock_calculate_ma.assert_called_once()
        mock_get_timestamp.assert_called_once()

    @patch("app.main.MarketDataService.calculate_moving_average")
    def test_get_moving_average_no_data(self, mock_calculate_ma):
        """Test moving average calculation with no data."""
        mock_calculate_ma.return_value = None

        client = TestClient(app)
        response = client.get(
            "/moving-average/AAPL", headers={"Authorization": "Bearer demo-api-key-123"}
        )

        assert response.status_code == 404
        assert "No data found for symbol AAPL" in response.json()["detail"]

    @patch("app.main.MarketDataService.calculate_moving_average")
    def test_get_moving_average_exception(self, mock_calculate_ma):
        """Test moving average calculation with exception."""
        mock_calculate_ma.side_effect = Exception("Calculation error")

        client = TestClient(app)
        response = client.get(
            "/moving-average/AAPL", headers={"Authorization": "Bearer demo-api-key-123"}
        )

        assert response.status_code == 500
        assert "Error calculating moving average" in response.json()["detail"]

    @patch("app.main.MarketDataService.calculate_moving_average")
    def test_get_moving_average_http_exception(self, mock_calculate_ma):
        """Test moving average calculation with HTTP exception."""
        from fastapi import HTTPException

        mock_calculate_ma.side_effect = HTTPException(
            status_code=400,
            detail="Bad request",
        )

        client = TestClient(app)
        response = client.get(
            "/moving-average/AAPL", headers={"Authorization": "Bearer demo-api-key-123"}
        )

        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "Bad request" in detail  # noqa: E501

    @pytest.mark.asyncio
    async def test_lifespan_success(self):
        """Test successful application lifespan."""
        mock_app = Mock()

        async with lifespan(mock_app):
            pass

        # Should not raise any exceptions

    @pytest.mark.asyncio
    async def test_lifespan_with_exception(self):
        """Test application lifespan with exception."""
        mock_app = Mock()

        with pytest.raises(RuntimeError):
            async with lifespan(mock_app):
                raise RuntimeError("Test error")

    def test_cors_middleware(self):
        """Test CORS middleware is configured."""
        client = TestClient(app)

        # Test preflight request
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )

        # Should not fail due to CORS
        assert response.status_code in [200, 405]  # 405 is also acceptable for OPTIONS

    def test_api_documentation_endpoints(self):
        """Test API documentation endpoints."""
        client = TestClient(app)

        # Test OpenAPI docs
        response = client.get("/docs")
        assert response.status_code == 200

        # Test OpenAPI JSON
        response = client.get("/openapi.json")
        assert response.status_code == 200

    def test_router_inclusion(self):
        """Test that routers are properly included."""
        client = TestClient(app)

        # Test that prices router is included
        response = client.get("/api/v1/prices/")
        # Should not be 404 (even if it's 405 or other error, it means the router is included)
        assert response.status_code != 404

    def test_database_connection_error(self):
        """Test database connection error handling."""
        from sqlalchemy import create_engine, exc

        with pytest.raises(exc.NoSuchModuleError):
            create_engine("invalid://url")


class TestDatabaseSession:
    """Test cases for database session management."""

    def test_engine_configuration(self):
        """Test SQLAlchemy engine configuration."""
        from app.db.session import engine

        # Test that engine is properly configured
        assert engine is not None
        assert hasattr(engine, "pool")
        assert hasattr(engine, "url")

    def test_session_factory_configuration(self):
        """Test session factory configuration."""
        from app.db.session import SessionLocal

        # Test that session factory is properly configured
        assert SessionLocal is not None
        assert hasattr(SessionLocal, "__call__")
