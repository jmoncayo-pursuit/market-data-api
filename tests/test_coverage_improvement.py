"""Tests for improving test coverage."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.market_data import MarketDataCreate, MarketDataUpdate
from app.services.kafka_service import KafkaService
from app.services.market_data import MarketDataService
from app.services.redis_service import RedisService


class TestRedisServiceCoverage:
    """Tests to improve RedisService coverage."""

    @pytest.mark.asyncio
    async def test_redis_connection_success(self):
        """Test successful Redis connection."""
        with patch("redis.asyncio.Redis.from_url") as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping.return_value = True
            mock_from_url.return_value = mock_redis

            service = RedisService()
            result = await service._get_redis_client()
            assert result is not None
            mock_from_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_connection_failure(self):
        """Test Redis connection failure."""
        mock_redis = AsyncMock()
        mock_redis.ping.side_effect = Exception("Connection failed")

        with patch("redis.asyncio.Redis.from_url", return_value=mock_redis):
            service = RedisService()
            result = await service._get_redis_client()
            assert result is None

    @pytest.mark.asyncio
    async def test_get_cached_price_with_connection(self):
        """Test getting cached price with connection."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = "150.0"

        with patch(
            "app.services.redis_service.RedisService._get_redis_client",
            new_callable=AsyncMock,
        ) as mock_get_redis:
            mock_get_redis.return_value = mock_redis
            service = RedisService()
            result = await service.get_cached_price("AAPL")
            assert result == 150.0

    @pytest.mark.asyncio
    async def test_get_cached_price_no_connection(self):
        """Test getting cached price without connection."""
        with patch(
            "app.services.redis_service.RedisService._get_redis_client",
            new_callable=AsyncMock,
        ) as mock_get_redis:
            mock_get_redis.return_value = None
            service = RedisService()
            result = await service.get_cached_price("AAPL")
            assert result is None

    @pytest.mark.asyncio
    async def test_cache_price_with_connection(self):
        """Test caching price with connection."""
        mock_redis = AsyncMock()
        mock_redis.setex.return_value = True

        with patch(
            "app.services.redis_service.RedisService._get_redis_client",
            new_callable=AsyncMock,
        ) as mock_get_redis:
            mock_get_redis.return_value = mock_redis
            service = RedisService()
            result = await service.cache_price("AAPL", 150.0)
            assert result is True

    @pytest.mark.asyncio
    async def test_cache_price_no_connection(self):
        """Test caching price without connection."""
        with patch(
            "app.services.redis_service.RedisService._get_redis_client",
            new_callable=AsyncMock,
        ) as mock_get_redis:
            mock_get_redis.return_value = None
            service = RedisService()
            result = await service.cache_price("AAPL", 150.0)
            assert result is False

    @pytest.mark.asyncio
    async def test_store_price_with_connection(self):
        """Test storing price with connection."""
        mock_redis = AsyncMock()
        mock_redis.set.return_value = True

        with patch(
            "app.services.redis_service.RedisService._get_redis_client",
            new_callable=AsyncMock,
        ) as mock_get_redis:
            mock_get_redis.return_value = mock_redis
            service = RedisService()
            result = await service.store_price("AAPL", 150.0)
            assert result is True

    @pytest.mark.asyncio
    async def test_store_price_no_connection(self):
        """Test storing price without connection."""
        with patch(
            "app.services.redis_service.RedisService._get_redis_client",
            new_callable=AsyncMock,
        ) as mock_get_redis:
            mock_get_redis.return_value = None
            service = RedisService()
            result = await service.store_price("AAPL", 150.0)
            assert result is False

    @pytest.mark.asyncio
    async def test_get_price_with_connection(self):
        """Test getting price with connection."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = "150.0"

        with patch(
            "app.services.redis_service.RedisService._get_redis_client",
            new_callable=AsyncMock,
        ) as mock_get_redis:
            mock_get_redis.return_value = mock_redis
            service = RedisService()
            result = await service.get_price("AAPL")
            assert result == 150.0

    @pytest.mark.asyncio
    async def test_get_price_no_connection(self):
        """Test getting price without connection."""
        with patch(
            "app.services.redis_service.RedisService._get_redis_client",
            new_callable=AsyncMock,
        ) as mock_get_redis:
            mock_get_redis.return_value = None
            service = RedisService()
            result = await service.get_price("AAPL")
            assert result is None

    @pytest.mark.asyncio
    async def test_set_price_with_connection(self):
        """Test setting price with connection."""
        mock_redis = AsyncMock()
        mock_redis.set.return_value = True

        with patch(
            "app.services.redis_service.RedisService._get_redis_client",
            new_callable=AsyncMock,
        ) as mock_get_redis:
            mock_get_redis.return_value = mock_redis
            service = RedisService()
            result = await service.set_price("AAPL", 150.0)
            assert result is True

    @pytest.mark.asyncio
    async def test_set_price_no_connection(self):
        """Test setting price without connection."""
        with patch(
            "app.services.redis_service.RedisService._get_redis_client",
            new_callable=AsyncMock,
        ) as mock_get_redis:
            mock_get_redis.return_value = None
            service = RedisService()
            result = await service.set_price("AAPL", 150.0)
            assert result is False

    @pytest.mark.asyncio
    async def test_delete_price_with_connection(self):
        """Test deleting price with connection."""
        mock_redis = AsyncMock()
        mock_redis.delete.return_value = 1

        with patch(
            "app.services.redis_service.RedisService._get_redis_client",
            new_callable=AsyncMock,
        ) as mock_get_redis:
            mock_get_redis.return_value = mock_redis
            service = RedisService()
            result = await service.delete_price("AAPL")
            assert result is True

    @pytest.mark.asyncio
    async def test_delete_price_no_connection(self):
        """Test deleting price without connection."""
        with patch(
            "app.services.redis_service.RedisService._get_redis_client",
            new_callable=AsyncMock,
        ) as mock_get_redis:
            mock_get_redis.return_value = None
            service = RedisService()
            result = await service.delete_price("AAPL")
            assert result is False

    @pytest.mark.asyncio
    async def test_get_all_prices_with_connection(self):
        """Test getting all prices with connection."""
        mock_redis = AsyncMock()

        async def mock_scan_iter(pattern):
            yield "price:AAPL"
            yield "price:GOOGL"

        mock_redis.scan_iter = mock_scan_iter
        mock_redis.get.side_effect = ["150.0", "2500.0"]

        with patch(
            "app.services.redis_service.RedisService._get_redis_client",
            new_callable=AsyncMock,
        ) as mock_get_redis:
            mock_get_redis.return_value = mock_redis
            service = RedisService()
            result = await service.get_all_prices()
            assert result == {"AAPL": 150.0, "GOOGL": 2500.0}

    @pytest.mark.asyncio
    async def test_get_all_prices_no_connection(self):
        """Test getting all prices without connection."""
        with patch(
            "app.services.redis_service.RedisService._get_redis_client",
            new_callable=AsyncMock,
        ) as mock_get_redis:
            mock_get_redis.return_value = None
            service = RedisService()
            result = await service.get_all_prices()
            assert result == {}

    @pytest.mark.asyncio
    async def test_clear_prices_with_connection(self):
        """Test clearing prices with connection."""
        mock_redis = AsyncMock()

        async def mock_scan_iter(pattern):
            yield "price:AAPL"
            yield "price:GOOGL"

        mock_redis.scan_iter = mock_scan_iter
        mock_redis.delete.return_value = 1

        with patch(
            "app.services.redis_service.RedisService._get_redis_client",
            new_callable=AsyncMock,
        ) as mock_get_redis:
            mock_get_redis.return_value = mock_redis
            service = RedisService()
            result = await service.clear_prices()
            assert result is True

    @pytest.mark.asyncio
    async def test_clear_prices_no_connection(self):
        """Test clearing prices without connection."""
        with patch(
            "app.services.redis_service.RedisService._get_redis_client",
            new_callable=AsyncMock,
        ) as mock_get_redis:
            mock_get_redis.return_value = None
            service = RedisService()
            result = await service.clear_prices()
            assert result is False

    @pytest.mark.asyncio
    async def test_get_price_history_with_connection(self):
        """Test getting price history with successful connection."""
        with patch(
            "app.services.redis_service.RedisService._get_redis_client",
            new_callable=AsyncMock,
        ) as mock_get_client:
            mock_redis = AsyncMock()
            now = datetime.now()
            current_time = int(now.timestamp() * 1000)
            key = f"price:AAPL:{current_time}"
            mock_redis.keys.return_value = [key]
            mock_redis.get.return_value = (
                '{"price": 150.50, "timestamp": "2023-01-01T00:00:00"}'
            )
            mock_get_client.return_value = mock_redis

            service = RedisService()
            result = await service.get_price_history("AAPL", 3600)
            assert isinstance(result, list)
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_price_history_no_connection(self):
        """Test getting price history without connection."""
        with patch(
            "app.services.redis_service.RedisService._get_redis_client",
            new_callable=AsyncMock,
        ) as mock_get_client:
            mock_get_client.return_value = None

        service = RedisService()
        result = await service.get_price_history("AAPL", 3600)
        assert result == []

    @pytest.mark.asyncio
    async def test_get_latest_price_with_connection(self):
        """Test getting latest price with successful connection."""
        with patch(
            "app.services.redis_service.RedisService._get_redis_client",
            new_callable=AsyncMock,
        ) as mock_get_client:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = "150.50"
            mock_get_client.return_value = mock_redis

            service = RedisService()
            result = await service.get_latest_price("AAPL")

            assert result is not None
            assert result["symbol"] == "AAPL"
            assert result["price"] == 150.50

    @pytest.mark.asyncio
    async def test_store_job_status_with_connection(self):
        """Test storing job status with successful connection."""
        with patch(
            "app.services.redis_service.RedisService._get_redis_client",
            new_callable=AsyncMock,
        ) as mock_get_client:
            mock_redis = AsyncMock()
            mock_redis.set.return_value = True
            mock_get_client.return_value = mock_redis

            service = RedisService()
            job_status = {"progress": 50, "status": "running"}
            result = await service.store_job_status("job_123", job_status)
            assert result is None

    @pytest.mark.asyncio
    async def test_get_job_status_with_connection(self):
        """Test getting job status with successful connection."""
        with patch(
            "app.services.redis_service.RedisService._get_redis_client",
            new_callable=AsyncMock,
        ) as mock_get_client:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = '{"progress": 50, "status": "running"}'
            mock_get_client.return_value = mock_redis

            service = RedisService()
            result = await service.get_job_status("job_123")

            assert result == {"progress": 50, "status": "running"}

    @pytest.mark.asyncio
    async def test_delete_job_with_connection(self):
        """Test deleting job with successful connection."""
        with patch(
            "app.services.redis_service.RedisService._get_redis_client",
            new_callable=AsyncMock,
        ) as mock_get_client:
            mock_redis = AsyncMock()
            mock_redis.delete.return_value = 1
            mock_get_client.return_value = mock_redis

            service = RedisService()
            await service.delete_job("job_123")

            mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_jobs_with_connection(self):
        """Test listing jobs with successful connection."""
        with patch(
            "app.services.redis_service.RedisService._get_redis_client",
            new_callable=AsyncMock,
        ) as mock_get_client:
            mock_redis = AsyncMock()

            # Mock scan_iter as an async generator
            async def mock_scan_iter(pattern):
                yield "job:job1"
                yield "job:job2"

            mock_redis.scan_iter = mock_scan_iter
            # Return JSON with job_id
            mock_redis.get.side_effect = [
                '{"job_id": "job1", "status": "running"}',
                '{"job_id": "job2", "status": "completed"}',
            ]
            mock_get_client.return_value = mock_redis

            service = RedisService()
            result = await service.list_jobs()

            assert len(result) == 2
            assert result[0]["job_id"] == "job1"
            assert result[1]["job_id"] == "job2"


class TestKafkaServiceCoverage:
    """Tests to improve KafkaService coverage."""

    @pytest.mark.asyncio
    async def test_kafka_init_success(self):
        """Test successful Kafka initialization."""
        with patch(
            "app.services.kafka_service.AIOKafkaProducer"
        ) as mock_producer_class:
            mock_producer = AsyncMock()
            mock_producer.start = AsyncMock()
            mock_producer_class.return_value = mock_producer

            service = KafkaService()
            producer = await service._get_producer()
            assert producer is not None
            mock_producer.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_produce_price_event_success(self):
        """Test successful price event production."""
        with patch(
            "app.services.kafka_service.KafkaService._get_producer",
            new_callable=AsyncMock,
        ) as mock_get_producer:
            mock_producer = AsyncMock()
            mock_producer.send_and_wait = AsyncMock()
            mock_get_producer.return_value = mock_producer
            service = KafkaService()
            result = await service.produce_price_event("AAPL", 150.0)
            assert result is True

    @pytest.mark.asyncio
    async def test_produce_message_success(self):
        """Test successful message production."""
        with patch(
            "app.services.kafka_service.KafkaService._get_producer",
            new_callable=AsyncMock,
        ) as mock_get_producer:
            mock_producer = AsyncMock()
            mock_producer.send_and_wait = AsyncMock()
            mock_get_producer.return_value = mock_producer
            service = KafkaService()
            result = await service.produce_message(
                "test-topic", "test-key", {"test": "data"}
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_consume_messages_success(self):
        """Test successful message consumption."""
        with patch(
            "app.services.kafka_service.KafkaService._get_consumer",
            new_callable=AsyncMock,
        ) as mock_get_consumer:
            mock_consumer = AsyncMock()
            # Mock getmany to return a dictionary mapping topic partitions to message lists
            mock_message = AsyncMock()
            mock_message.value = b'{"test": "data"}'
            mock_consumer.getmany.return_value = {("test-topic", 0): [mock_message]}
            mock_get_consumer.return_value = mock_consumer
            service = KafkaService()
            result = await service.consume_messages("test-topic")
            assert result == [{"test": "data"}]

    @pytest.mark.asyncio
    async def test_consume_messages_no_messages(self):
        """Test message consumption with no messages."""
        with patch(
            "app.services.kafka_service.KafkaService._get_consumer",
            new_callable=AsyncMock,
        ) as mock_get_consumer:
            mock_consumer = AsyncMock()
            # Mock getmany to return empty dictionary for no messages
            mock_consumer.getmany.return_value = {}
            mock_get_consumer.return_value = mock_consumer
            service = KafkaService()
            result = await service.consume_messages("test-topic")
            assert result == []

    @pytest.mark.asyncio
    async def test_consume_messages_exception(self):
        """Test message consumption with exception."""
        with patch(
            "app.services.kafka_service.KafkaService._get_consumer",
            new_callable=AsyncMock,
        ) as mock_get_consumer:
            mock_consumer = AsyncMock()
            mock_consumer.getmany.side_effect = Exception("Connection failed")
            mock_get_consumer.return_value = mock_consumer
        service = KafkaService()
        result = await service.consume_messages("test-topic")
        assert result == []

    @pytest.mark.asyncio
    async def test_close_connections(self):
        """Test closing Kafka connections."""
        with patch(
            "app.services.kafka_service.KafkaService._get_producer",
            new_callable=AsyncMock,
        ) as mock_get_producer:
            mock_producer = AsyncMock()
            mock_producer.stop = AsyncMock()
            mock_get_producer.return_value = mock_producer
            service = KafkaService()
            await service._get_producer()
            service.producer = mock_producer  # Ensure producer is set
            await service.close()
            mock_producer.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_connections_with_none(self):
        """Test closing Kafka connections when they are None."""
        service = KafkaService()
        # Should not raise any exception
        await service.close()


class TestMarketDataServiceCoverage:
    """Tests to improve MarketDataService coverage."""

    def test_create_market_data_success(self):
        """Test successful market data creation."""
        mock_db = Mock()
        mock_market_data = Mock()
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        market_data_create = MarketDataCreate(
            symbol="AAPL",
            price=150.0,
            volume=1000,
            source="test",
            raw_data="{}",
        )

        with patch(
            "app.services.market_data.MarketData", return_value=mock_market_data
        ):
            result = MarketDataService.create_market_data(mock_db, market_data_create)
            assert result == mock_market_data

    def test_create_market_data_exception(self):
        """Test market data creation with exception."""
        mock_db = Mock()
        mock_db.add.side_effect = Exception("Database error")

        market_data_create = MarketDataCreate(
            symbol="AAPL",
            price=150.0,
            volume=1000,
            source="test",
            raw_data="{}",
        )

        with patch("app.services.market_data.MarketData"):
            with pytest.raises(Exception):
                MarketDataService.create_market_data(mock_db, market_data_create)

    def test_get_market_data_success(self):
        """Test successful market data retrieval."""
        mock_db = Mock()
        mock_market_data = Mock()
        mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = [
            mock_market_data
        ]

        result = MarketDataService.get_market_data(mock_db)
        assert result == [mock_market_data]

    def test_get_market_data_by_symbol_success(self):
        """Test successful market data retrieval by symbol."""
        mock_db = Mock()
        mock_market_data = Mock()
        mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = [
            mock_market_data
        ]

        result = MarketDataService.get_market_data_by_symbol(mock_db, "AAPL")
        assert result == [mock_market_data]

    def test_get_latest_market_data_success(self):
        """Test successful latest market data retrieval."""
        mock_db = Mock()
        mock_market_data = Mock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
            mock_market_data
        )

        result = MarketDataService.get_latest_market_data(mock_db, "AAPL")
        assert result == mock_market_data

    def test_get_latest_market_data_not_found(self):
        """Test latest market data retrieval when not found."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
            None
        )

        result = MarketDataService.get_latest_market_data(mock_db, "AAPL")
        assert result is None

    def test_update_market_data_success(self):
        """Test successful market data update."""
        mock_db = Mock()
        mock_market_data = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_market_data
        )
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        market_data_update = MarketDataUpdate(price=160.0)

        result = MarketDataService.update_market_data(mock_db, 1, market_data_update)
        assert result == mock_market_data

    def test_update_market_data_not_found(self):
        """Test market data update when not found."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        market_data_update = MarketDataUpdate(price=160.0)

        result = MarketDataService.update_market_data(mock_db, 1, market_data_update)
        assert result is None

    def test_delete_market_data_success(self):
        """Test successful market data deletion."""
        mock_db = Mock()
        mock_market_data = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_market_data
        )
        mock_db.delete.return_value = None
        mock_db.commit.return_value = None

        result = MarketDataService.delete_market_data(mock_db, 1)
        assert result is True

    def test_delete_market_data_not_found(self):
        """Test market data deletion when not found."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = MarketDataService.delete_market_data(mock_db, 1)
        assert result is False

    def test_get_all_symbols_success(self):
        """Test successful symbols retrieval."""
        mock_db = Mock()
        # Should return a list of tuples
        mock_db.query.return_value.distinct.return_value.all.return_value = [
            ("AAPL",),
            ("GOOGL",),
        ]

        result = MarketDataService.get_all_symbols(mock_db)
        assert result == ["AAPL", "GOOGL"]

    def test_calculate_moving_average_success(self):
        """Test successful moving average calculation."""
        mock_db = Mock()
        # Should return a list of objects with .price attribute
        record1 = Mock()
        record1.price = 150.0
        record2 = Mock()
        record2.price = 160.0
        record3 = Mock()
        record3.price = 170.0
        record4 = Mock()
        record4.price = 180.0
        record5 = Mock()
        record5.price = 190.0
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            record1,
            record2,
            record3,
            record4,
            record5,
        ]

        result = MarketDataService.calculate_moving_average(mock_db, "AAPL", window=5)
        assert result == 170.0

    def test_calculate_moving_average_no_data(self):
        """Test moving average calculation with no data."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            []
        )

        result = MarketDataService.calculate_moving_average(mock_db, "AAPL", window=5)
        assert result is None

    def test_get_latest_timestamp_success(self):
        """Test successful latest timestamp retrieval."""
        mock_db = Mock()
        dt = datetime.now()
        # Should return a tuple
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
            dt,
        )

        result = MarketDataService.get_latest_timestamp(mock_db, "AAPL")
        assert result == dt

    def test_get_latest_timestamp_not_found(self):
        """Test latest timestamp retrieval when not found."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
            None
        )

        result = MarketDataService.get_latest_timestamp(mock_db, "AAPL")
        assert result is None


class TestAPICoverage:
    """Tests to improve API endpoint coverage."""

    def test_get_market_data_with_symbol_filter(self):
        """Test getting market data with symbol filter."""
        with patch(
            "app.api.endpoints.prices.MarketDataService.get_market_data_by_symbol"
        ) as mock_get:
            mock_market_data = Mock()
            mock_market_data.id = 1
            mock_market_data.symbol = "AAPL"
            mock_market_data.price = 150.0
            mock_market_data.volume = 1000
            mock_market_data.timestamp = datetime.now()
            mock_market_data.source = "test"
            mock_market_data.raw_data = None
            mock_get.return_value = [mock_market_data]

            client = TestClient(app)
            response = client.get(
                "/api/v1/prices/?symbol=AAPL",
                headers={"Authorization": "Bearer demo-api-key-123"},
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["symbol"] == "AAPL"

    def test_get_market_data_with_pagination(self):
        """Test getting market data with pagination."""
        with patch(
            "app.api.endpoints.prices.MarketDataService.get_market_data"
        ) as mock_get:
            mock_market_data = Mock()
            mock_market_data.id = 1
            mock_market_data.symbol = "AAPL"
            mock_market_data.price = 150.0
            mock_market_data.volume = 1000
            mock_market_data.timestamp = datetime.now()
            mock_market_data.source = "test"
            mock_market_data.raw_data = None
            mock_get.return_value = [mock_market_data]

            client = TestClient(app)
            response = client.get(
                "/api/v1/prices/?skip=0&limit=5",
                headers={"Authorization": "Bearer demo-api-key-123"},
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1

    def test_get_market_data_database_error(self):
        """Test getting market data with database error."""
        with patch(
            "app.api.endpoints.prices.MarketDataService.get_market_data"
        ) as mock_get:
            mock_get.side_effect = Exception("Database error")

            client = TestClient(app)
            response = client.get(
                "/api/v1/prices/",
                headers={"Authorization": "Bearer demo-api-key-123"},
            )

            assert response.status_code == 500
            assert "Error retrieving market data" in response.json()["detail"]

    def test_create_market_data_database_error(self):
        """Test creating market data with database error."""
        with patch(
            "app.api.endpoints.prices.MarketDataService.create_market_data"
        ) as mock_create:
            mock_create.side_effect = Exception("Database error")

            client = TestClient(app)
            response = client.post(
                "/api/v1/prices/",
                json={
                    "symbol": "AAPL",
                    "price": 150.0,
                    "volume": 1000,
                    "source": "test",
                },
                headers={"Authorization": "Bearer demo-api-key-123"},
            )

            assert response.status_code == 500
            assert "Error creating market data" in response.json()["detail"]

    def test_update_market_data_database_error(self):
        """Test updating market data with database error."""
        with patch(
            "app.api.endpoints.prices.MarketDataService.update_market_data"
        ) as mock_update:
            mock_update.side_effect = Exception("Database error")

            client = TestClient(app)
            response = client.put(
                "/api/v1/prices/1",
                json={"price": 160.0},
                headers={"Authorization": "Bearer demo-api-key-123"},
            )

            assert response.status_code == 500
            assert "Error updating market data" in response.json()["detail"]

    def test_delete_market_data_database_error(self):
        """Test deleting market data with database error."""
        with patch(
            "app.api.endpoints.prices.MarketDataService.delete_market_data"
        ) as mock_delete:
            mock_delete.side_effect = Exception("Database error")

            client = TestClient(app)
            response = client.delete(
                "/api/v1/prices/1",
                headers={"Authorization": "Bearer admin-api-key-456"},
            )

            assert response.status_code == 500
            assert "Error deleting market data" in response.json()["detail"]

    def test_get_latest_price_database_error(self):
        """Test getting latest price with database error."""
        with patch(
            "app.api.endpoints.prices.MarketDataService.get_latest_market_data"
        ) as mock_get:
            mock_get.side_effect = Exception("Database error")

            client = TestClient(app)
            response = client.get(
                "/api/v1/prices/latest?symbol=AAPL",
                headers={"Authorization": "Bearer demo-api-key-123"},
            )

            assert response.status_code == 500
            assert "Error retrieving latest price" in response.json()["detail"]
