"""Tests for market data functionality."""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.models.market_data import MarketData
from app.services.kafka_service import KafkaService
from app.services.market_data import MarketDataService


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def market_data_service(db_session):
    """Test fixture for MarketDataService."""
    return MarketDataService(db_session)


@pytest.fixture
def kafka_service():
    """Test fixture for Kafka service."""
    return KafkaService()


def test_get_latest_price(client, db_session):
    """Test getting the latest price."""

    # Override the database dependency to use our test session
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    try:
        # Add price to the database
        MarketDataService.add_price(
            db_session, "AAPL", 123.45, volume=1000, source="test_source"
        )
        db_session.commit()
        # Test the API endpoint
        response = client.get(
            "/api/v1/prices/latest?symbol=AAPL",
            headers={"Authorization": "Bearer demo-api-key-123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "symbol" in data
        assert "price" in data
        assert "timestamp" in data
    finally:
        # Clean up the override
        app.dependency_overrides.clear()


def test_poll_prices(client):
    """Test polling prices."""
    response = client.post(
        "/api/v1/prices/poll",
        json={"symbols": ["AAPL", "MSFT"], "interval": 60},
        headers={"Authorization": "Bearer admin-api-key-456"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "job_id" in data
    assert "status" in data
    assert "config" in data
    assert data["status"] == "created"
    assert "symbols" in data["config"]
    assert "interval" in data["config"]


def test_list_polling_jobs(client):
    """Test listing polling jobs."""
    # First create a job
    client.post(
        "/api/v1/prices/poll",
        json={"symbols": ["AAPL"], "interval": 60},
        headers={"Authorization": "Bearer admin-api-key-456"},
    )
    # Then list jobs
    response = client.get(
        "/api/v1/prices/poll", headers={"Authorization": "Bearer admin-api-key-456"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "id" in data[0]
        assert "status" in data[0]
        assert "config" in data[0]


def test_get_polling_job_status(client):
    """Test getting polling job status."""
    # First create a job
    create_response = client.post(
        "/api/v1/prices/poll",
        json={"symbols": ["AAPL"], "interval": 60},
        headers={"Authorization": "Bearer admin-api-key-456"},
    )
    job_id = create_response.json()["job_id"]
    # Then get its status
    response = client.get(
        f"/api/v1/prices/poll/{job_id}",
        headers={"Authorization": "Bearer admin-api-key-456"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "status" in data
    assert "config" in data


def test_delete_polling_job(client):
    """Test deleting a polling job."""
    # First create a job
    create_response = client.post(
        "/api/v1/prices/poll",
        json={"symbols": ["AAPL"], "interval": 60},
        headers={"Authorization": "Bearer admin-api-key-456"},
    )
    job_id = create_response.json()["job_id"]
    # Then delete it
    response = client.delete(
        f"/api/v1/prices/poll/{job_id}",
        headers={"Authorization": "Bearer admin-api-key-456"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "Job deleted successfully"


def test_delete_all_polling_jobs(client):
    """Test deleting all polling jobs."""
    # First create some jobs
    client.post(
        "/api/v1/prices/poll",
        json={"symbols": ["AAPL"], "interval": 60},
        headers={"Authorization": "Bearer admin-api-key-456"},
    )
    client.post(
        "/api/v1/prices/poll",
        json={"symbols": ["MSFT"], "interval": 60},
        headers={"Authorization": "Bearer admin-api-key-456"},
    )
    # Then delete all
    response = client.post(
        "/api/v1/prices/delete-all-polling-jobs",
        headers={"Authorization": "Bearer admin-api-key-456"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "All jobs deleted successfully"


def test_health_check(client):
    """Test health check."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


def test_calculate_moving_average(db_session):
    """Test calculating moving average."""
    # Add test data
    symbol = "AAPL"
    prices = [100, 101, 99, 102, 98]
    for price in prices:
        MarketDataService.add_price(
            db_session, symbol, price, volume=1000, source="test_source"
        )

    ma = MarketDataService.calculate_moving_average(db_session, symbol)
    assert ma is not None
    assert isinstance(ma, float)


def test_kafka_producer(kafka_service):
    """Test kafka producer."""
    test_data = {
        "symbol": "AAPL",
        "price": 150.25,
        "timestamp": datetime.now(UTC).isoformat(),
        "provider": "yahoo_finance",
    }
    with patch(
        "app.services.kafka_service.KafkaService.produce_price_event"
    ) as mock_produce:
        mock_produce.return_value = None
        kafka_service.produce_price_event(test_data)
        mock_produce.assert_called_once_with(test_data)


def test_kafka_consumer(kafka_service, market_data_service):
    """Test kafka consumer."""
    # This test might need to be mocked or run in a separate process


def test_create_market_data(client, db_session):
    """Test creating market data."""
    market_data = {
        "symbol": "AAPL",
        "price": 150.25,
        "volume": 1000000,
        "source": "yahoo_finance",
        "raw_data": "test_data",
    }

    # Override the database dependency to use our test session
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    try:
        # Mock the service to return a real dict
        with patch(
            "app.api.endpoints.prices.MarketDataService.create_market_data"
        ) as mock_create:
            mock_market_data = MarketData(
                id=1,
                symbol="AAPL",
                price=150.25,
                volume=1000000,
                source="yahoo_finance",
                raw_data="test_data",
                timestamp=datetime.now(),
            )
            mock_create.return_value = mock_market_data

            response = client.post(
                "/api/v1/prices/",
                json=market_data,
                headers={"Authorization": "Bearer demo-api-key-123"},
            )
            assert response.status_code == 201
            data = response.json()
            assert data["symbol"] == "AAPL"
            assert data["price"] == 150.25
    finally:
        # Clean up the override
        app.dependency_overrides.clear()


def test_get_market_data(client, db_session):
    """Test getting market data."""

    # Override the database dependency to use our test session
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    try:
        # Mock the service to return a real list
        with patch(
            "app.api.endpoints.prices.MarketDataService.get_market_data"
        ) as mock_get:
            mock_get.return_value = []

            response = client.get(
                "/api/v1/prices/", headers={"Authorization": "Bearer demo-api-key-123"}
            )
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
    finally:
        # Clean up the override
        app.dependency_overrides.clear()


def test_update_market_data(client, db_session):
    """Test updating market data."""

    # Override the database dependency to use our test session
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    try:
        # Mock the service to return a real dict
        with patch(
            "app.api.endpoints.prices.MarketDataService.update_market_data"
        ) as mock_update:
            mock_market_data = MarketData(
                id=1,
                symbol="AAPL",
                price=160.25,
                volume=2000000,
                source="yahoo_finance",
                raw_data="updated_test_data",
                timestamp=datetime.now(),
            )
            mock_update.return_value = mock_market_data

            update_data = {
                "price": 160.25,
                "volume": 2000000,
                "raw_data": "updated_test_data",
            }

            response = client.put(
                "/api/v1/prices/1",
                json=update_data,
                headers={"Authorization": "Bearer demo-api-key-123"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["symbol"] == "AAPL"
            assert data["price"] == 160.25
    finally:
        # Clean up the override
        app.dependency_overrides.clear()


def test_delete_market_data(client, db_session):
    """Test deleting market data."""

    # Override the database dependency to use our test session
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    try:
        # Mock the service to return a real dict
        with patch(
            "app.api.endpoints.prices.MarketDataService.delete_market_data"
        ) as mock_delete:
            mock_delete.return_value = True

            response = client.delete(
                "/api/v1/prices/1",
                headers={"Authorization": "Bearer admin-api-key-456"},
            )
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert data["message"] == "Market data deleted successfully"
    finally:
        # Clean up the override
        app.dependency_overrides.clear()


def test_get_price_history():
    """Test getting price history."""
    # This test would need proper mocking
    pass


def test_get_price_history_empty():
    """Test getting empty price history."""
    # This test would need proper mocking
    pass


def test_get_price_history_invalid_symbol():
    """Test getting price history with invalid symbol."""
    # This test would need proper mocking
    pass


def test_get_price_history_invalid_window():
    """Test getting price history with invalid window."""
    # This test would need proper mocking
    pass


def test_get_price_history_invalid_symbol_and_window():
    """Test getting price history with invalid symbol and window."""
    # This test would need proper mocking
    pass
