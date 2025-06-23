"""Tests for API coverage."""

from unittest.mock import ANY, Mock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.main import app
from app.models.market_data import MarketData
from app.schemas.market_data import MarketDataCreate
from app.services.market_data import MarketDataService


def get_auth_headers():
    """Get authentication headers for API tests."""
    return {"Authorization": "Bearer demo-api-key-123"}


def get_admin_auth_headers():
    """Get admin authentication headers for API tests."""
    return {"Authorization": "Bearer admin-api-key-456"}


class TestAPIPricesEndpointComprehensive:
    """Comprehensive tests for prices API endpoints."""

    def test_get_prices_with_pagination(self):
        """Test GET /api/v1/prices/ with pagination."""
        with patch(
            "app.api.endpoints.prices.MarketDataService.get_market_data"
        ) as mock_get:
            mock_get.return_value = [
                {
                    "id": 1,
                    "symbol": "AAPL",
                    "price": 150.0,
                    "volume": 1000,
                    "source": "test",
                    "timestamp": "2023-01-01T00:00:00Z",
                },
                {
                    "id": 2,
                    "symbol": "GOOGL",
                    "price": 2500.0,
                    "volume": 500,
                    "source": "test",
                    "timestamp": "2023-01-01T00:00:00Z",
                },
            ]
            client = TestClient(app)
            response = client.get(
                "/api/v1/prices/?skip=10&limit=5", headers=get_auth_headers()
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            mock_get.assert_called_once_with(ANY, 10, 5)

    def test_get_prices_with_symbol_filter(self):
        """Test GET /api/v1/prices/ with symbol filter."""
        with patch(
            "app.api.endpoints.prices.MarketDataService.get_market_data_by_symbol"
        ) as mock_get:
            mock_get.return_value = [
                {
                    "id": 1,
                    "symbol": "AAPL",
                    "price": 150.0,
                    "volume": 1000,
                    "source": "test",
                    "timestamp": "2023-01-01T00:00:00Z",
                }
            ]
            client = TestClient(app)
            response = client.get(
                "/api/v1/prices/?symbol=AAPL", headers=get_auth_headers()
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["symbol"] == "AAPL"
            mock_get.assert_called_once_with(ANY, "AAPL", 0, 100)

    def test_get_prices_database_error(self):
        """Test GET /api/v1/prices/ with database error."""
        with patch(
            "app.api.endpoints.prices.MarketDataService.get_market_data"
        ) as mock_get:
            mock_get.side_effect = SQLAlchemyError("Database error")
            client = TestClient(app)
            response = client.get("/api/v1/prices/", headers=get_auth_headers())
            assert response.status_code == 500
            mock_get.assert_called_once_with(ANY, 0, 100)

    def test_get_latest_price_success(self):
        """Test GET /api/v1/prices/latest with success."""
        with patch(
            "app.api.endpoints.prices.MarketDataService.get_latest_price_static"
        ) as mock_get:
            from datetime import datetime, timezone
            mock_get.return_value = MarketData(
                id=1,
                symbol="AAPL",
                price=150.0,
                volume=1000,
                source="test",
                timestamp=datetime.now(timezone.utc),
            )
            client = TestClient(app)
            response = client.get(
                "/api/v1/prices/latest?symbol=AAPL", headers=get_auth_headers()
            )
            assert response.status_code == 200
            data = response.json()
            assert data["symbol"] == "AAPL"
            assert data["price"] == 150.0
            mock_get.assert_called_once_with(ANY, "AAPL")

    def test_get_latest_price_not_found(self):
        """Test GET /api/v1/prices/latest when not found."""
        with patch(
            "app.api.endpoints.prices.MarketDataService.get_latest_price_static"
        ) as mock_get:
            mock_get.return_value = None
            client = TestClient(app)
            response = client.get(
                "/api/v1/prices/latest?symbol=INVALID", headers=get_auth_headers()
            )
            assert response.status_code == 404
            mock_get.assert_called_once_with(ANY, "INVALID")

    def test_get_latest_price_missing_symbol(self):
        """Test GET /api/v1/prices/latest without symbol parameter."""
        client = TestClient(app)
        response = client.get("/api/v1/prices/latest", headers=get_auth_headers())

        assert response.status_code == 422

    def test_create_price_success(self):
        """Test POST /api/v1/prices/ with success."""
        with patch(
            "app.api.endpoints.prices.MarketDataService.create_market_data"
        ) as mock_create:
            mock_create.return_value = MarketData(
                id=1,
                symbol="AAPL",
                price=150.0,
                volume=1000,
                source="test",
                timestamp="2023-01-01T00:00:00Z",
            )
            client = TestClient(app)
            response = client.post(
                "/api/v1/prices/",
                json={
                    "symbol": "AAPL",
                    "price": 150.0,
                    "volume": 1000,
                    "source": "test",
                },
                headers=get_auth_headers(),
            )
            assert response.status_code == 201
            data = response.json()
            assert data["symbol"] == "AAPL"
            assert data["price"] == 150.0
            mock_create.assert_called_once_with(
                ANY,
                MarketDataCreate(
                    symbol="AAPL", price=150.0, volume=1000, source="test"
                ),
            )

    def test_create_price_validation_error(self):
        """Test validation error when creating price with invalid data."""
        from pydantic import ValidationError

        invalid_cases = [
            {"symbol": "AAPL", "price": -1.0, "volume": 1000, "source": "test"},
            {"symbol": "", "price": 150.0, "volume": 1000, "source": "test"},
            {"symbol": "AAPL", "price": 150.0, "volume": 0, "source": "test"},
        ]
        for case in invalid_cases:
            with pytest.raises(ValidationError):
                MarketDataCreate(**case)

    def test_create_price_database_error(self):
        """Test POST /api/v1/prices/ with database error."""
        with patch(
            "app.api.endpoints.prices.MarketDataService.create_market_data"
        ) as mock_create:
            mock_create.side_effect = SQLAlchemyError("Database error")
            client = TestClient(app)
            response = client.post(
                "/api/v1/prices/",
                json={
                    "symbol": "AAPL",
                    "price": 150.0,
                    "volume": 1000,
                    "source": "test",
                },
                headers=get_auth_headers(),
            )
            assert response.status_code == 500
            mock_create.assert_called_once_with(
                ANY,
                MarketDataCreate(
                    symbol="AAPL", price=150.0, volume=1000, source="test"
                ),
            )

    def test_get_price_by_id_success(self):
        """Test GET /api/v1/prices/{price_id} with success."""
        with patch(
            "app.api.endpoints.prices.MarketDataService.get_market_data_by_id"
        ) as mock_get:
            mock_get.return_value = MarketData(
                id=1,
                symbol="AAPL",
                price=150.0,
                volume=1000,
                source="test",
                timestamp="2023-01-01T00:00:00Z",
            )
            client = TestClient(app)
            response = client.get("/api/v1/prices/1", headers=get_auth_headers())
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["symbol"] == "AAPL"
            mock_get.assert_called_once_with(ANY, 1)

    def test_get_price_by_id_not_found(self):
        """Test GET /api/v1/prices/{price_id} when not found."""
        with patch(
            "app.api.endpoints.prices.MarketDataService.get_market_data_by_id"
        ) as mock_get:
            mock_get.return_value = None
            client = TestClient(app)
            response = client.get("/api/v1/prices/999", headers=get_auth_headers())
            assert response.status_code == 404
            mock_get.assert_called_once_with(ANY, 999)

    def test_update_price_success(self):
        """Test PUT /api/v1/prices/{price_id} with success."""
        with patch(
            "app.api.endpoints.prices.MarketDataService.update_market_data"
        ) as mock_update:
            mock_update.return_value = MarketData(
                id=1,
                symbol="AAPL",
                price=160.0,
                volume=1000,
                source="test",
                timestamp="2023-01-01T00:00:00Z",
            )
            client = TestClient(app)
            response = client.put(
                "/api/v1/prices/1",
                json={
                    "symbol": "AAPL",
                    "price": 160.0,
                    "volume": 1000,
                    "source": "test",
                },
                headers=get_auth_headers(),
            )
            assert response.status_code == 200
            data = response.json()
            assert data["price"] == 160.0
            mock_update.assert_called_once_with(ANY, 1, ANY)

    def test_update_price_not_found(self):
        """Test PUT /api/v1/prices/{price_id} when not found."""
        with patch(
            "app.api.endpoints.prices.MarketDataService.update_market_data"
        ) as mock_update:
            mock_update.return_value = None
            client = TestClient(app)
            response = client.put(
                "/api/v1/prices/999", json={"price": 160.0}, headers=get_auth_headers()
            )
            assert response.status_code == 404
            mock_update.assert_called_once_with(ANY, 999, ANY)

    def test_update_price_validation_error(self):
        """Test PUT /api/v1/prices/{price_id} with validation error."""
        with patch(
            "app.api.endpoints.prices.MarketDataService.update_market_data"
        ) as mock_update:
            mock_update.side_effect = HTTPException(
                status_code=422, detail="Validation error"
            )
            client = TestClient(app)
            response = client.put(
                "/api/v1/prices/1", json={"price": -1.0}, headers=get_auth_headers()
            )
            assert response.status_code == 422
            mock_update.assert_called_once_with(ANY, 1, ANY)

    def test_delete_price_success(self):
        """Test DELETE /api/v1/prices/{price_id} with success."""
        with patch(
            "app.api.endpoints.prices.MarketDataService.delete_market_data"
        ) as mock_delete:
            mock_delete.return_value = True
            client = TestClient(app)
            response = client.delete(
                "/api/v1/prices/1", headers=get_admin_auth_headers()
            )
            assert response.status_code == 200 or response.status_code == 204
            mock_delete.assert_called_once_with(ANY, 1)

    def test_delete_price_not_found(self):
        """Test DELETE /api/v1/prices/{price_id} when not found."""
        with patch(
            "app.api.endpoints.prices.MarketDataService.delete_market_data"
        ) as mock_delete:
            mock_delete.return_value = False
            client = TestClient(app)
            response = client.delete(
                "/api/v1/prices/999", headers=get_admin_auth_headers()
            )
            assert response.status_code == 404
            mock_delete.assert_called_once_with(ANY, 999)

    def test_get_moving_average_success(self, client, db_session):
        """Test successful moving average calculation."""
        # Add test data
        MarketDataService.add_price(
            db_session, "AAPL", 150.0, volume=1000, source="test_source"
        )
        MarketDataService.add_price(
            db_session, "AAPL", 151.0, volume=1000, source="test_source"
        )
        MarketDataService.add_price(
            db_session, "AAPL", 152.0, volume=1000, source="test_source"
        )
        MarketDataService.add_price(
            db_session, "AAPL", 153.0, volume=1000, source="test_source"
        )
        MarketDataService.add_price(
            db_session, "AAPL", 154.0, volume=1000, source="test_source"
        )
        db_session.commit()

        response = client.get(
            "/api/v1/prices/AAPL/moving-average?window=5", headers=get_auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        assert data["value"] == 152.0
        assert data["symbol"] == "AAPL"
        assert data["window_size"] == 5

    def test_get_moving_average_insufficient_data(self):
        """Test GET /api/v1/prices/{symbol}/moving-average with insufficient data."""
        with patch(
            "app.api.endpoints.prices.MarketDataService.calculate_moving_average"
        ) as mock_calc:
            mock_calc.return_value = None
            client = TestClient(app)
            response = client.get(
                "/api/v1/prices/AAPL/moving-average?window=5",
                headers=get_auth_headers(),
            )
            assert response.status_code == 404
            mock_calc.assert_called_once_with(ANY, "AAPL", 5)

    def test_get_moving_average_invalid_window(self):
        """Test GET /api/v1/prices/{symbol}/moving-average with invalid window."""
        client = TestClient(app)
        response = client.get(
            "/api/v1/prices/AAPL/moving-average?window=0", headers=get_auth_headers()
        )
        assert response.status_code == 422

    def test_get_symbols_success(self):
        """Test GET /api/v1/prices/symbols with success."""
        mock_db = Mock()

        def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        try:
            with patch(
                "app.api.endpoints.prices.MarketDataService.get_all_symbols"
            ) as mock_get:
                mock_get.return_value = ["AAPL", "GOOGL", "MSFT"]
                client = TestClient(app)
                response = client.get(
                    "/api/v1/prices/symbols", headers=get_auth_headers()
                )
                if response.status_code != 200:
                    print("Response content:", response.content)
                assert response.status_code == 200
                data = response.json()
                assert data["symbols"] == ["AAPL", "GOOGL", "MSFT"]
                mock_get.assert_called_once_with(ANY)
        finally:
            app.dependency_overrides = {}

    def test_get_symbols_database_error(self):
        """Test GET /api/v1/prices/symbols with database error."""
        mock_db = Mock()

        def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        try:
            with patch(
                "app.api.endpoints.prices.MarketDataService.get_all_symbols"
            ) as mock_get:
                mock_get.side_effect = Exception("Database error")
                client = TestClient(app)
                response = client.get(
                    "/api/v1/prices/symbols", headers=get_auth_headers()
                )
                if response.status_code != 500:
                    print("Response content:", response.content)
                assert response.status_code == 500
                mock_get.assert_called_once_with(ANY)
        finally:
            app.dependency_overrides = {}


class TestAPIErrorHandling:
    """Test API error handling scenarios."""

    def test_invalid_json_request(self):
        """Test API with invalid JSON request."""
        client = TestClient(app)
        response = client.post(
            "/api/v1/prices/", data="invalid json", headers=get_auth_headers()
        )

        assert response.status_code == 422

    def test_missing_required_fields(self):
        """Test API with missing required fields."""
        client = TestClient(app)
        response = client.post(
            "/api/v1/prices/",
            json={
                "symbol": "AAPL"
                # Missing price, volume, source
            },
            headers=get_auth_headers(),
        )

        assert response.status_code == 422

    def test_invalid_price_id_format(self):
        """Test API with invalid price ID format."""
        client = TestClient(app)
        response = client.get("/api/v1/prices/invalid", headers=get_auth_headers())

        assert response.status_code == 422

    def test_method_not_allowed(self):
        """Test API with method not allowed."""
        client = TestClient(app)
        response = client.patch(
            "/api/v1/prices/1", headers=get_auth_headers()
        )  # PATCH not implemented

        assert response.status_code == 405

    def test_invalid_query_parameters(self):
        """Test API with invalid query parameters."""
        client = TestClient(app)
        response = client.get("/api/v1/prices/?skip=-1", headers=get_auth_headers())

        assert response.status_code == 422


class TestAPIPerformance:
    """Test API performance scenarios."""

    def test_large_dataset_handling(self):
        """Test API with large dataset."""
        with patch("app.api.endpoints.prices.get_db") as mock_get_db:
            mock_db = Mock(spec=Session)
            mock_get_db.return_value = mock_db

            with patch("app.api.endpoints.prices.MarketDataService") as mock_service:
                mock_service_instance = Mock()
                mock_service.return_value = mock_service_instance
                # Simulate large dataset
                large_dataset = [
                    MarketData(
                        symbol="AAPL", price=150.0 + i, volume=1000, source="test"
                    )
                    for i in range(1000)
                ]
                mock_service_instance.get_market_data.return_value = large_dataset

                client = TestClient(app)
                response = client.get(
                    "/api/v1/prices/?limit=100", headers=get_auth_headers()
                )

                assert response.status_code == 200
                data = response.json()
                assert len(data) <= 100  # Should respect limit


class TestAPIPollingJobs:
    """Test polling job endpoints for better coverage."""

    def test_create_polling_job_success(self):
        """Test creating a polling job successfully."""
        config = {"symbols": ["AAPL", "GOOGL"], "interval": 60}
        client = TestClient(app)
        response = client.post(
            "/api/v1/prices/poll", json=config, headers=get_admin_auth_headers()
        )
        assert response.status_code == 201
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "created"
        assert data["config"]["symbols"] == config["symbols"]
        assert data["config"]["interval"] == config["interval"]

    def test_list_polling_jobs(self):
        """Test listing polling jobs."""
        client = TestClient(app)
        response = client.get("/api/v1/prices/poll", headers=get_admin_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_polling_job_status_success(self):
        """Test getting polling job status successfully."""
        client = TestClient(app)
        # First create a job
        config = {"symbols": ["AAPL"], "interval": 30}
        create_response = client.post(
            "/api/v1/prices/poll", json=config, headers=get_admin_auth_headers()
        )
        job_id = create_response.json()["job_id"]

        # Then get its status
        response = client.get(
            f"/api/v1/prices/poll/{job_id}", headers=get_admin_auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == job_id
        assert data["status"] == "created"

    def test_get_polling_job_status_not_found(self):
        """Test getting status of non-existent polling job."""
        client = TestClient(app)
        response = client.get(
            "/api/v1/prices/poll/nonexistent", headers=get_admin_auth_headers()
        )
        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]

    def test_delete_polling_job_success(self):
        """Test deleting a polling job successfully."""
        client = TestClient(app)
        # First create a job
        config = {"symbols": ["AAPL"], "interval": 30}
        create_response = client.post(
            "/api/v1/prices/poll", json=config, headers=get_admin_auth_headers()
        )
        job_id = create_response.json()["job_id"]

        # Then delete it
        response = client.delete(
            f"/api/v1/prices/poll/{job_id}", headers=get_admin_auth_headers()
        )
        assert response.status_code == 200
        assert "message" in response.json()

    def test_delete_polling_job_not_found(self):
        """Test deleting non-existent polling job."""
        client = TestClient(app)
        response = client.delete(
            "/api/v1/prices/poll/nonexistent", headers=get_admin_auth_headers()
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_delete_all_polling_jobs(self):
        """Test deleting all polling jobs."""
        client = TestClient(app)
        # Create some jobs first
        config1 = {"symbols": ["AAPL"], "interval": 30}
        config2 = {"symbols": ["GOOGL"], "interval": 60}
        client.post(
            "/api/v1/prices/poll", json=config1, headers=get_admin_auth_headers()
        )
        client.post(
            "/api/v1/prices/poll", json=config2, headers=get_admin_auth_headers()
        )

        # Delete all jobs
        response = client.post(
            "/api/v1/prices/delete-all-polling-jobs", headers=get_admin_auth_headers()
        )
        assert response.status_code == 200
        assert "message" in response.json()
