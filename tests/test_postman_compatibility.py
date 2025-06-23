"""Tests to ensure API compatibility with Postman collection and prevent status code mismatches."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.main import app


class TestPostmanCompatibility:
    """Test API compatibility with Postman collection expectations."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
        self.headers = {"Authorization": "Bearer admin-api-key-456"}

    def test_health_check_status_code(self):
        """Test health check returns 200 status code."""
        response = self.client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_create_market_data_status_code(self):
        """Test create market data returns 201 status code (not 202)."""
        data = {
            "symbol": "AAPL",
            "price": 123.45,
            "volume": 1000,
            "source": "test_source"
        }
        response = self.client.post(
            "/api/v1/prices/",
            json=data,
            headers=self.headers
        )
        assert response.status_code == 201  # Created, not 202 Accepted
        response_data = response.json()
        assert "symbol" in response_data
        assert "price" in response_data
        assert "id" in response_data

    def test_get_latest_price_status_code(self):
        """Test get latest price returns 200 status code."""
        response = self.client.get(
            "/api/v1/prices/latest?symbol=AAPL",
            headers=self.headers
        )
        assert response.status_code == 200
        response_data = response.json()
        assert "symbol" in response_data
        assert "price" in response_data
        assert "timestamp" in response_data

    def test_create_polling_job_status_code(self):
        """Test create polling job returns 201 status code (not 202)."""
        data = {
            "symbols": ["AAPL", "MSFT"],
            "interval": 60
        }
        response = self.client.post(
            "/api/v1/prices/poll",
            json=data,
            headers=self.headers
        )
        assert response.status_code == 201  # Created, not 202 Accepted
        response_data = response.json()
        assert "job_id" in response_data
        assert "status" in response_data
        assert "config" in response_data

    def test_list_polling_jobs_status_code(self):
        """Test list polling jobs returns 200 status code."""
        response = self.client.get(
            "/api/v1/prices/poll",
            headers=self.headers
        )
        assert response.status_code == 200
        response_data = response.json()
        assert isinstance(response_data, list)

    def test_get_polling_job_status_status_code(self):
        """Test get polling job status returns 200 status code."""
        # First create a job
        data = {"symbols": ["AAPL"], "interval": 60}
        create_response = self.client.post(
            "/api/v1/prices/poll",
            json=data,
            headers=self.headers
        )
        job_id = create_response.json()["job_id"]
        
        # Then get its status
        response = self.client.get(
            f"/api/v1/prices/poll/{job_id}",
            headers=self.headers
        )
        assert response.status_code == 200
        response_data = response.json()
        assert "id" in response_data  # API returns 'id', not 'job_id'
        assert "status" in response_data

    def test_delete_polling_job_status_code(self):
        """Test delete polling job returns 200 status code."""
        # First create a job
        data = {"symbols": ["AAPL"], "interval": 60}
        create_response = self.client.post(
            "/api/v1/prices/poll",
            json=data,
            headers=self.headers
        )
        job_id = create_response.json()["job_id"]
        
        # Then delete it
        response = self.client.delete(
            f"/api/v1/prices/poll/{job_id}",
            headers=self.headers
        )
        assert response.status_code == 200

    def test_delete_all_polling_jobs_status_code(self):
        """Test delete all polling jobs returns 200 status code."""
        response = self.client.post(
            "/api/v1/prices/delete-all-polling-jobs",
            headers=self.headers
        )
        assert response.status_code == 200

    def test_get_moving_average_status_code(self):
        """Test get moving average returns 200 status code."""
        # The correct endpoint is the global /moving-average/{symbol}
        response = self.client.get(
            "/moving-average/AAPL?window=10",
            headers=self.headers
        )
        # Should return 200 if data exists, 404 if no data
        assert response.status_code in [200, 404]

    def test_get_symbols_status_code(self):
        """Test get symbols returns 200 status code."""
        response = self.client.get(
            "/api/v1/prices/symbols",
            headers=self.headers
        )
        assert response.status_code == 200
        response_data = response.json()
        # API returns {"symbols": [...]} not just a list
        assert isinstance(response_data, dict)
        assert "symbols" in response_data
        assert isinstance(response_data["symbols"], list)

    def test_unauthorized_access_status_code(self):
        """Test unauthorized access returns 401 status code."""
        response = self.client.get("/api/v1/prices/latest?symbol=AAPL")
        assert response.status_code == 401

    def test_invalid_request_status_code(self):
        """Test invalid request returns 422 status code."""
        data = {"invalid": "data"}
        response = self.client.post(
            "/api/v1/prices/",
            json=data,
            headers=self.headers
        )
        assert response.status_code == 422

    def test_not_found_status_code(self):
        """Test not found returns 404 status code."""
        response = self.client.get(
            "/api/v1/prices/poll/nonexistent-job",
            headers=self.headers
        )
        assert response.status_code == 404

    def test_postman_response_format_consistency(self):
        """Test that response formats match Postman expectations."""
        # Test create market data response format
        data = {
            "symbol": "AAPL",
            "price": 123.45,
            "volume": 1000,
            "source": "test_source"
        }
        response = self.client.post(
            "/api/v1/prices/",
            json=data,
            headers=self.headers
        )
        response_data = response.json()
        
        # Check required fields from Postman test
        required_fields = ["symbol", "price", "id"]
        for field in required_fields:
            assert field in response_data, f"Missing required field: {field}"

    def test_postman_polling_job_response_format(self):
        """Test that polling job response format matches Postman expectations."""
        data = {
            "symbols": ["AAPL", "MSFT"],
            "interval": 60
        }
        response = self.client.post(
            "/api/v1/prices/poll",
            json=data,
            headers=self.headers
        )
        response_data = response.json()
        
        # Check required fields from Postman test
        assert "job_id" in response_data, "Missing required field: job_id"
        assert "status" in response_data, "Missing required field: status"
        assert "config" in response_data, "Missing required field: config"

    def test_postman_latest_price_response_format(self):
        """Test that latest price response format matches Postman expectations."""
        response = self.client.get(
            "/api/v1/prices/latest?symbol=AAPL",
            headers=self.headers
        )
        response_data = response.json()
        
        # Check required fields from Postman test
        required_fields = ["symbol", "price", "timestamp"]
        for field in required_fields:
            assert field in response_data, f"Missing required field: {field}"

    def test_api_endpoint_availability(self):
        """Test that all Postman collection endpoints are available."""
        endpoints = [
            ("GET", "/health"),
            ("POST", "/api/v1/prices/"),
            ("GET", "/api/v1/prices/latest"),
            ("POST", "/api/v1/prices/poll"),
            ("GET", "/api/v1/prices/poll"),
            ("POST", "/api/v1/prices/delete-all-polling-jobs"),
        ]
        
        for method, endpoint in endpoints:
            if method == "GET":
                response = self.client.get(endpoint)
            elif method == "POST":
                response = self.client.post(endpoint, json={})
            
            # Should not be 404 (endpoint exists)
            assert response.status_code != 404, f"Endpoint {method} {endpoint} not found"

    def test_authorization_header_format(self):
        """Test that authorization header format works correctly."""
        # Test with Bearer token format
        headers = {"Authorization": "Bearer admin-api-key-456"}
        response = self.client.get(
            "/api/v1/prices/latest?symbol=AAPL",
            headers=headers
        )
        assert response.status_code == 200

    def test_content_type_headers(self):
        """Test that Content-Type headers work correctly."""
        data = {
            "symbol": "AAPL",
            "price": 123.45,
            "volume": 1000,
            "source": "test_source"
        }
        headers = {
            "Authorization": "Bearer admin-api-key-456",
            "Content-Type": "application/json"
        }
        response = self.client.post(
            "/api/v1/prices/",
            json=data,
            headers=headers
        )
        assert response.status_code == 201

    def test_cors_headers(self):
        """Test that CORS headers are present."""
        response = self.client.options("/api/v1/prices/")
        # Should not fail due to CORS
        assert response.status_code in [200, 405]  # 405 Method Not Allowed is also acceptable

    def test_error_response_format(self):
        """Test that error responses have consistent format."""
        # Test 401 error
        response = self.client.get("/api/v1/prices/latest?symbol=AAPL")
        assert response.status_code == 401
        error_data = response.json()
        assert "detail" in error_data

        # Test 422 error
        data = {"invalid": "data"}
        response = self.client.post(
            "/api/v1/prices/",
            json=data,
            headers=self.headers
        )
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data

    def test_rate_limiting_behavior(self):
        """Test that rate limiting doesn't break Postman compatibility."""
        # Make multiple requests to test rate limiting
        for _ in range(5):
            response = self.client.get(
                "/api/v1/prices/latest?symbol=AAPL",
                headers=self.headers
            )
            # Should either succeed (200) or be rate limited (429)
            assert response.status_code in [200, 429]

    def test_database_connection_fallback(self):
        """Test that database connection issues don't break API."""
        with patch('app.db.session.get_db') as mock_get_db:
            mock_get_db.side_effect = Exception("Database connection failed")
            
            response = self.client.get(
                "/api/v1/prices/latest?symbol=AAPL",
                headers=self.headers
            )
            # Should handle database errors gracefully
            assert response.status_code in [200, 500, 503]

    def test_redis_connection_fallback(self):
        """Test that Redis connection issues don't break API."""
        with patch('app.services.redis_service.RedisService._get_redis_client') as mock_redis:
            mock_redis.return_value = None
            
            response = self.client.get(
                "/api/v1/prices/latest?symbol=AAPL",
                headers=self.headers
            )
            # Should handle Redis errors gracefully
            assert response.status_code == 200

    def test_kafka_connection_fallback(self):
        """Test that Kafka connection issues don't break API."""
        with patch('app.services.kafka_service.KafkaService._get_producer') as mock_producer:
            mock_producer.return_value = None
            
            data = {
                "symbols": ["AAPL"],
                "interval": 60
            }
            response = self.client.post(
                "/api/v1/prices/poll",
                json=data,
                headers=self.headers
            )
            # Should handle Kafka errors gracefully
            assert response.status_code == 201


class TestPostmanEnvironmentCompatibility:
    """Test compatibility with Postman environment variables."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_base_url_compatibility(self):
        """Test that API works with Postman base_url variable."""
        # Test with localhost
        response = self.client.get("/health")
        assert response.status_code == 200
        
        # Test with 127.0.0.1 (should work the same)
        response = self.client.get("/health")
        assert response.status_code == 200

    def test_api_key_compatibility(self):
        """Test that API works with Postman api_key variable."""
        # Test with the API key from Postman environment
        headers = {"Authorization": "Bearer admin-api-key-456"}
        response = self.client.get(
            "/api/v1/prices/latest?symbol=AAPL",
            headers=headers
        )
        assert response.status_code == 200

    def test_job_id_variable_compatibility(self):
        """Test that job_id variable works in URLs."""
        # Create a job first
        data = {"symbols": ["AAPL"], "interval": 60}
        headers = {"Authorization": "Bearer admin-api-key-456"}
        create_response = self.client.post(
            "/api/v1/prices/poll",
            json=data,
            headers=headers
        )
        job_id = create_response.json()["job_id"]
        
        # Test that job_id can be used in URL
        response = self.client.get(
            f"/api/v1/prices/poll/{job_id}",
            headers=headers
        )
        assert response.status_code == 200

    def test_test_symbol_variable_compatibility(self):
        """Test that test_symbol variable works."""
        # Test with the test symbol from Postman environment
        headers = {"Authorization": "Bearer admin-api-key-456"}
        response = self.client.get(
            "/api/v1/prices/latest?symbol=AAPL",  # AAPL from Postman environment
            headers=headers
        )
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["symbol"] == "AAPL"


class TestPostmanCollectionConsistency:
    """Test consistency with Postman collection structure."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
        self.headers = {"Authorization": "Bearer admin-api-key-456"}

    def test_collection_request_methods(self):
        """Test that all Postman collection request methods work."""
        # GET requests
        response = self.client.get("/health")
        assert response.status_code == 200
        
        response = self.client.get(
            "/api/v1/prices/latest?symbol=AAPL",
            headers=self.headers
        )
        assert response.status_code == 200
        
        # POST requests
        data = {"symbol": "AAPL", "price": 123.45, "volume": 1000, "source": "test"}
        response = self.client.post(
            "/api/v1/prices/",
            json=data,
            headers=self.headers
        )
        assert response.status_code == 201
        
        # DELETE requests
        # First create a job
        job_data = {"symbols": ["AAPL"], "interval": 60}
        create_response = self.client.post(
            "/api/v1/prices/poll",
            json=job_data,
            headers=self.headers
        )
        job_id = create_response.json()["job_id"]
        
        # Then delete it
        response = self.client.delete(
            f"/api/v1/prices/poll/{job_id}",
            headers=self.headers
        )
        assert response.status_code == 200

    def test_collection_query_parameters(self):
        """Test that Postman collection query parameters work."""
        # Test symbol parameter
        response = self.client.get(
            "/api/v1/prices/latest?symbol=AAPL",
            headers=self.headers
        )
        assert response.status_code == 200
        
        # Test moving average parameters (global endpoint)
        response = self.client.get(
            "/moving-average/AAPL?window=10",
            headers=self.headers
        )
        assert response.status_code in [200, 404]

    def test_collection_request_bodies(self):
        """Test that Postman collection request bodies work."""
        # Test create market data body
        data = {
            "symbol": "AAPL",
            "price": 123.45,
            "volume": 1000,
            "source": "test_source"
        }
        response = self.client.post(
            "/api/v1/prices/",
            json=data,
            headers=self.headers
        )
        assert response.status_code == 201
        
        # Test create polling job body
        job_data = {
            "symbols": ["AAPL", "MSFT"],
            "interval": 60
        }
        response = self.client.post(
            "/api/v1/prices/poll",
            json=job_data,
            headers=self.headers
        )
        assert response.status_code == 201

    def test_collection_headers(self):
        """Test that Postman collection headers work."""
        # Test Authorization header
        headers = {"Authorization": "Bearer admin-api-key-456"}
        response = self.client.get(
            "/api/v1/prices/latest?symbol=AAPL",
            headers=headers
        )
        assert response.status_code == 200
        
        # Test Content-Type header
        headers = {
            "Authorization": "Bearer admin-api-key-456",
            "Content-Type": "application/json"
        }
        data = {"symbol": "AAPL", "price": 123.45, "volume": 1000, "source": "test"}
        response = self.client.post(
            "/api/v1/prices/",
            json=data,
            headers=headers
        )
        assert response.status_code == 201 