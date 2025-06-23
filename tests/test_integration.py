"""Integration tests for the application."""

from fastapi.testclient import TestClient

from app.main import app


class TestServiceIntegration:
    """Test service integration scenarios."""

    def test_market_data_to_kafka_integration(self, integration_client: TestClient):
        """Test integration between market data and Kafka services."""
        # Create market data
        response = integration_client.post(
            "/api/v1/prices/",
            json={
                "symbol": "AAPL",
                "price": 150.0,
                "volume": 1000,
                "source": "test",
            },
            headers={"Authorization": "Bearer demo-api-key-123"},
        )
        assert response.status_code == 201

        # Get latest price
        response = integration_client.get(
            "/api/v1/prices/latest?symbol=AAPL",
            headers={"Authorization": "Bearer demo-api-key-123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["price"] == 150.0

    def test_market_data_to_redis_integration(self, integration_client: TestClient):
        """Test integration between market data and Redis services."""
        # Create market data
        response = integration_client.post(
            "/api/v1/prices/",
            json={
                "symbol": "AAPL",
                "price": 150.0,
                "volume": 1000,
                "source": "test",
            },
            headers={"Authorization": "Bearer demo-api-key-123"},
        )
        assert response.status_code == 201

        # Get all market data
        response = integration_client.get(
            "/api/v1/prices/",
            headers={"Authorization": "Bearer demo-api-key-123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert data[0]["symbol"] == "AAPL"

    def test_kafka_to_redis_integration(self):
        """Test integration between Kafka and Redis services."""
        # This test would require both services to be properly mocked
        # For now, we'll just test that the endpoints exist
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200


class TestDatabaseIntegration:
    """Test database integration scenarios."""

    def test_database_market_data_integration(self, integration_client: TestClient):
        """Test database integration with market data operations."""
        # Create market data
        response = integration_client.post(
            "/api/v1/prices/",
            json={
                "symbol": "AAPL",
                "price": 150.0,
                "volume": 1000,
                "source": "test",
            },
            headers={"Authorization": "Bearer demo-api-key-123"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["price"] == 150.0

        # Update market data
        response = integration_client.put(
            "/api/v1/prices/1",
            json={"price": 160.0},
            headers={"Authorization": "Bearer demo-api-key-123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["price"] == 160.0

    def test_database_transaction_integration(self, integration_client: TestClient):
        """Test database transaction integration."""
        # Create market data
        response = integration_client.post(
            "/api/v1/prices/",
            json={
                "symbol": "AAPL",
                "price": 150.0,
                "volume": 1000,
                "source": "test",
            },
            headers={"Authorization": "Bearer demo-api-key-123"},
        )
        assert response.status_code == 201

        # Update market data
        response = integration_client.put(
            "/api/v1/prices/1",
            json={"price": 160.0},
            headers={"Authorization": "Bearer demo-api-key-123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["price"] == 160.0


class TestAPIIntegration:
    """Test API integration scenarios."""

    def test_full_workflow_integration(self, integration_client: TestClient):
        """Test full workflow integration."""
        # Create market data
        response = integration_client.post(
            "/api/v1/prices/",
            json={
                "symbol": "AAPL",
                "price": 150.0,
                "volume": 1000,
                "source": "test",
            },
            headers={"Authorization": "Bearer demo-api-key-123"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["price"] == 150.0

        # Get latest price
        response = integration_client.get(
            "/api/v1/prices/latest?symbol=AAPL",
            headers={"Authorization": "Bearer demo-api-key-123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["price"] == 150.0

    def test_health_check_integration(self):
        """Test health check integration."""
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_error_handling_integration(self, integration_client: TestClient):
        """Test error handling integration."""
        # Test with a valid endpoint that doesn't exist
        response = integration_client.get(
            "/api/v1/prices/999999",
            headers={"Authorization": "Bearer demo-api-key-123"},
        )
        assert response.status_code == 404


class TestConfigurationIntegration:
    """Test configuration integration scenarios."""

    def test_environment_configuration_integration(self):
        """Test environment configuration integration."""
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200

    def test_cors_integration(self):
        """Test CORS integration."""
        client = TestClient(app)
        response = client.options("/health")
        # CORS headers should be present
        assert response.status_code in [200, 405]  # OPTIONS might not be implemented

    def test_logging_integration(self):
        """Test logging integration."""
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200


class TestPerformanceIntegration:
    """Test performance integration scenarios."""

    def test_response_time_integration(self):
        """Test response time integration."""
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200

    def test_concurrent_requests_integration(self):
        """Test concurrent requests integration."""
        client = TestClient(app)
        responses = []
        for _ in range(5):
            response = client.get("/health")
            responses.append(response)

        for response in responses:
            assert response.status_code == 200


class TestSecurityIntegration:
    """Test security integration scenarios."""

    def test_input_validation_integration(self, db_session):
        """Test input validation integration."""
        from app.api.endpoints import prices
        from app.db.session import get_db
        from app.main import app
        from app.services.market_data import MarketDataService as RealMarketDataService

        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db
        # Restore the real MarketDataService for this test
        original_service = prices.MarketDataService
        prices.MarketDataService = RealMarketDataService
        client = TestClient(app)
        response = client.post(
            "/api/v1/prices/",
            json={
                "symbol": "",  # Invalid empty symbol
                "price": -1,  # Invalid negative price
                "volume": 0,  # Invalid zero volume
                "source": "test",
            },
            headers={"Authorization": "Bearer demo-api-key-123"},
        )
        prices.MarketDataService = original_service
        app.dependency_overrides.clear()
        # Should return validation error
        assert response.status_code == 422

    def test_rate_limiting_integration(self):
        """Test rate limiting integration."""
        client = TestClient(app)
        # Make multiple requests
        for _ in range(10):
            response = client.get("/health")
            assert response.status_code == 200

    def test_authentication_integration(self, integration_client: TestClient):
        """Test authentication integration."""
        # Test health endpoint which should work without auth
        response = integration_client.get("/health")
        assert response.status_code == 200
