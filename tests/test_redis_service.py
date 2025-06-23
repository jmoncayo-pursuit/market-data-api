"""Tests for Redis service."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.redis_service import RedisService


@pytest.mark.asyncio
class TestRedisService:
    """Test cases for RedisService."""

    @patch("redis.asyncio.Redis.from_url")
    async def test_init_success(self, mock_from_url):
        """Test successful initialization."""
        mock_redis_instance = AsyncMock()
        mock_from_url.return_value = mock_redis_instance

        service = RedisService()
        redis_client = await service._get_redis_client()

        assert redis_client is not None
        mock_from_url.assert_called_once()
        mock_redis_instance.ping.assert_called_once()

    @patch("redis.asyncio.Redis.from_url")
    async def test_init_connection_error(self, mock_from_url):
        """Test initialization with connection error."""
        mock_from_url.side_effect = Exception("Connection failed")

        service = RedisService()
        redis_client = await service._get_redis_client()

        assert redis_client is None
        assert service.redis is None

    async def test_get_cached_price_success(self):
        """Test successful cached price retrieval."""
        service = RedisService()
        mock_redis = AsyncMock()
        mock_redis.get.return_value = "150.50"
        service.redis = mock_redis

        result = await service.get_cached_price("AAPL")

        assert result == 150.50
        mock_redis.get.assert_called_once_with("price:AAPL")

    async def test_get_cached_price_no_data(self):
        """Test cached price retrieval with no data."""
        service = RedisService()
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        service.redis = mock_redis

        result = await service.get_cached_price("AAPL")

        assert result is None

    @patch("app.services.redis_service.RedisService._get_redis_client")
    async def test_get_cached_price_no_redis(self, mock_get_client):
        """Test cached price retrieval when Redis is None."""
        mock_get_client.return_value = None
        service = RedisService()
        result = await service.get_cached_price("AAPL")
        assert result is None

    async def test_get_cached_price_exception(self):
        """Test cached price retrieval with exception."""
        service = RedisService()
        mock_redis = AsyncMock()
        mock_redis.get.side_effect = Exception("Redis error")
        service.redis = mock_redis

        result = await service.get_cached_price("AAPL")

        assert result is None

    async def test_cache_price_success(self):
        """Test successful price caching."""
        service = RedisService()
        mock_redis = AsyncMock()
        service.redis = mock_redis

        result = await service.cache_price("AAPL", 150.50)

        assert result is True
        mock_redis.setex.assert_called_once_with("price:AAPL", 300, "150.5")

    @patch("app.services.redis_service.RedisService._get_redis_client")
    async def test_cache_price_no_redis(self, mock_get_client):
        """Test price caching when Redis is None."""
        mock_get_client.return_value = None
        service = RedisService()
        result = await service.cache_price("AAPL", 150.50)
        assert result is False

    async def test_cache_price_exception(self):
        """Test price caching with exception."""
        service = RedisService()
        mock_redis = AsyncMock()
        mock_redis.setex.side_effect = Exception("Redis error")
        service.redis = mock_redis

        result = await service.cache_price("AAPL", 150.50)

        assert result is False

    async def test_store_price_success(self):
        """Test successful price storage."""
        service = RedisService()
        mock_redis = AsyncMock()
        service.redis = mock_redis

        result = await service.store_price("AAPL", 150.50)

        assert result is True
        mock_redis.set.assert_called_once()

    async def test_get_price_success(self):
        """Test successful price retrieval."""
        service = RedisService()
        mock_redis = AsyncMock()
        mock_redis.get.return_value = "150.50"
        service.redis = mock_redis

        result = await service.get_price("AAPL")

        assert result == 150.50

    async def test_set_price_success(self):
        """Test successful price setting."""
        service = RedisService()
        mock_redis = AsyncMock()
        service.redis = mock_redis

        result = await service.set_price("AAPL", 150.50)

        assert result is True
        mock_redis.set.assert_called_once_with("price:AAPL", "150.5")

    async def test_delete_price_success(self):
        """Test successful price deletion."""
        service = RedisService()
        mock_redis = AsyncMock()
        service.redis = mock_redis

        result = await service.delete_price("AAPL")

        assert result is True
        mock_redis.delete.assert_called_once_with("price:AAPL")

    async def test_get_all_prices_success(self):
        """Test successful retrieval of all prices."""
        service = RedisService()
        mock_redis = AsyncMock()

        async def mock_scan_iter(*args, **kwargs):
            yield "price:AAPL"
            yield "price:GOOGL"

        with patch.object(service, "_get_redis_client", return_value=mock_redis):
            mock_redis.scan_iter = mock_scan_iter
            mock_redis.get.side_effect = ["150.50", "2500.00"]
            result = await service.get_all_prices()
            expected = {"AAPL": 150.50, "GOOGL": 2500.00}
            assert result == expected

    async def test_clear_prices_success(self):
        """Test successful price clearing."""
        service = RedisService()
        mock_redis = AsyncMock()

        async def mock_scan_iter(*args, **kwargs):
            yield "price:AAPL"
            yield "price:GOOGL"

        with patch.object(service, "_get_redis_client", return_value=mock_redis):
            mock_redis.scan_iter = mock_scan_iter
            result = await service.clear_prices()
            assert result is True
            assert mock_redis.delete.await_count == 2

    async def test_get_price_history_success(self):
        """Test successful price history retrieval."""
        service = RedisService()
        mock_redis = AsyncMock()
        mock_redis.keys.return_value = [
            "price:AAPL:1672531200000",
            "price:AAPL:1672534800000",
        ]
        mock_redis.get.side_effect = [
            json.dumps({"price": 150.0, "timestamp": 1672531200000}),
            json.dumps({"price": 151.0, "timestamp": 1672534800000}),
        ]
        service.redis = mock_redis

        # Patch datetime to ensure both keys are within the window
        with patch("app.services.redis_service.datetime") as mock_dt:
            # Set now to just after the latest timestamp (in seconds)
            mock_now = MagicMock()
            mock_now.timestamp.return_value = 1672534800 + 1  # just after latest
            mock_dt.now.return_value = mock_now
            result = await service.get_price_history(
                "AAPL", window=4000
            )  # window covers both

        expected = [
            {"price": 150.0, "timestamp": 1672531200000},
            {"price": 151.0, "timestamp": 1672534800000},
        ]
        assert result == expected

    async def test_get_latest_price_success(self):
        """Test successful latest price retrieval."""
        service = RedisService()
        with patch.object(
            service, "get_price", new_callable=AsyncMock
        ) as mock_get_price:
            mock_get_price.return_value = 155.0
            result = await service.get_latest_price("AAPL")

            assert result["symbol"] == "AAPL"
            assert result["price"] == 155.0
            mock_get_price.assert_awaited_once_with("AAPL")

    async def test_get_latest_price_no_data(self):
        """Test latest price retrieval with no data."""
        service = RedisService()
        with patch.object(
            service, "get_price", new_callable=AsyncMock
        ) as mock_get_price:
            mock_get_price.return_value = None
            result = await service.get_latest_price("AAPL")
            assert result is None

    async def test_store_job_status_success(self):
        """Test successful job status storage."""
        service = RedisService()
        mock_redis = AsyncMock()
        service.redis = mock_redis
        status = {"status": "running"}

        await service.store_job_status("job1", status)

        mock_redis.set.assert_called_once_with("job:job1", json.dumps(status))

    async def test_get_job_status_success(self):
        """Test successful job status retrieval."""
        service = RedisService()
        mock_redis = AsyncMock()
        status = {"status": "completed"}
        mock_redis.get.return_value = json.dumps(status)
        service.redis = mock_redis

        result = await service.get_job_status("job1")

        assert result == status
        mock_redis.get.assert_called_once_with("job:job1")

    async def test_get_job_status_no_data(self):
        """Test job status retrieval with no data."""
        service = RedisService()
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        service.redis = mock_redis

        result = await service.get_job_status("job1")

        assert result is None

    async def test_delete_job_success(self):
        """Test successful job deletion."""
        service = RedisService()
        mock_redis = AsyncMock()
        service.redis = mock_redis

        await service.delete_job("job1")

        mock_redis.delete.assert_called_once_with("job:job1")

    async def test_list_jobs_success(self):
        """Test successful job listing."""
        service = RedisService()
        mock_redis = AsyncMock()
        jobs = [{"id": "job1"}, {"id": "job2"}]

        async def mock_scan_iter(*args, **kwargs):
            yield "job:job1"
            yield "job:job2"

        with patch.object(service, "_get_redis_client", return_value=mock_redis):
            mock_redis.scan_iter = mock_scan_iter
            mock_redis.get.side_effect = [json.dumps(j) for j in jobs]
            result = await service.list_jobs()
            assert result == jobs

    async def test_ping_success(self):
        """Test successful ping."""
        service = RedisService()
        mock_redis = AsyncMock()
        mock_redis.ping.return_value = True
        service.redis = mock_redis

        assert await service.ping() is True

    async def test_get_price_statistics_success(self):
        """Test successful price statistics retrieval."""
        service = RedisService()
        history = [
            {"price": 100, "timestamp": 1},
            {"price": 110, "timestamp": 2},
        ]
        with patch.object(
            service, "get_price_history", new_callable=AsyncMock
        ) as mock_get_history:
            mock_get_history.return_value = history
            result = await service.get_price_statistics("AAPL")
            assert result["avg"] == 105
            assert result["min"] == 100
            assert result["max"] == 110
