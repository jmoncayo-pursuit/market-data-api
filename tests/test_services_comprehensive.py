"""Comprehensive service tests to improve coverage."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.market_data import MarketData
from app.schemas.market_data import MarketDataCreate, MarketDataUpdate
from app.services.kafka_service import KafkaService
from app.services.market_data import MarketDataService
from app.services.redis_service import RedisService


class TestMarketDataServiceComprehensive:
    """Comprehensive tests for MarketDataService."""

    def test_get_market_data_by_symbol_with_pagination(self):
        """Test get_market_data_by_symbol with pagination."""
        # Mock database session and query
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [
            MarketData(symbol="AAPL", price=150.0, volume=1000, source="test"),
            MarketData(symbol="AAPL", price=151.0, volume=1100, source="test"),
        ]

        result = MarketDataService.get_market_data_by_symbol(
            mock_db, "AAPL", skip=10, limit=5
        )

        assert len(result) == 2
        mock_query.filter.assert_called_once()
        mock_query.offset.assert_called_once_with(10)
        mock_query.limit.assert_called_once_with(5)

    def test_get_market_data_by_symbol_no_results(self):
        """Test get_market_data_by_symbol with no results."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        result = MarketDataService.get_market_data_by_symbol(
            mock_db, "INVALID", skip=0, limit=10
        )

        assert result == []

    def test_get_latest_market_data_success(self):
        """Test get_latest_market_data success."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = MarketData(
            symbol="AAPL", price=150.0, volume=1000, source="test"
        )

        result = MarketDataService.get_latest_market_data(mock_db, "AAPL")

        assert result is not None
        assert result.symbol == "AAPL"
        assert result.price == 150.0

    def test_get_latest_market_data_not_found(self):
        """Test get_latest_market_data when not found."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = None

        result = MarketDataService.get_latest_market_data(mock_db, "INVALID")

        assert result is None

    def test_create_market_data_success(self):
        """Test create_market_data success."""
        mock_db = Mock(spec=Session)
        market_data_create = MarketDataCreate(
            symbol="AAPL", price=150.0, volume=1000, source="test"
        )

        result = MarketDataService.create_market_data(mock_db, market_data_create)

        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_create_market_data_exception(self):
        """Test create_market_data with exception."""
        mock_db = Mock(spec=Session)
        mock_db.commit.side_effect = SQLAlchemyError("Database error")

        market_data_create = MarketDataCreate(
            symbol="AAPL", price=150.0, volume=1000, source="test"
        )

        with pytest.raises(SQLAlchemyError):
            MarketDataService.create_market_data(mock_db, market_data_create)

        # The actual implementation doesn't call rollback on commit failure
        # so we don't expect rollback to be called
        mock_db.add.assert_called_once()

    def test_update_market_data_success(self):
        """Test update_market_data success."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = MarketData(
            id=1, symbol="AAPL", price=150.0, volume=1000, source="test"
        )

        market_data_update = MarketDataUpdate(price=160.0)
        result = MarketDataService.update_market_data(mock_db, 1, market_data_update)

        assert result is not None
        assert result.price == 160.0
        mock_db.commit.assert_called_once()

    def test_update_market_data_not_found(self):
        """Test update_market_data when not found."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        market_data_update = MarketDataUpdate(price=160.0)
        result = MarketDataService.update_market_data(mock_db, 999, market_data_update)

        assert result is None

    def test_delete_market_data_success(self):
        """Test delete_market_data success."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = MarketData(
            id=1, symbol="AAPL", price=150.0, volume=1000, source="test"
        )

        result = MarketDataService.delete_market_data(mock_db, 1)

        assert result is True
        mock_db.delete.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_delete_market_data_not_found(self):
        """Test delete_market_data when not found."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = MarketDataService.delete_market_data(mock_db, 999)

        assert result is False

    def test_calculate_moving_average_success(self):
        """Test calculate_moving_average success."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [
            MarketData(price=150.0),
            MarketData(price=151.0),
            MarketData(price=152.0),
            MarketData(price=153.0),
            MarketData(price=154.0),
        ]

        result = MarketDataService.calculate_moving_average(mock_db, "AAPL", window=5)

        assert result == 152.0  # Average of 150, 151, 152, 153, 154

    def test_calculate_moving_average_insufficient_data(self):
        """Test calculate_moving_average with insufficient data."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [MarketData(price=150.0), MarketData(price=151.0)]

        result = MarketDataService.calculate_moving_average(mock_db, "AAPL", window=5)

        assert result is None

    def test_get_all_symbols_success(self):
        """Test get_all_symbols success."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.all.return_value = [("AAPL",), ("GOOGL",), ("MSFT",)]

        result = MarketDataService.get_all_symbols(mock_db)

        assert result == ["AAPL", "GOOGL", "MSFT"]

    def test_get_latest_timestamp_success(self):
        """Test get_latest_timestamp success."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        # Mock the result as a tuple (timestamp,) since the query selects only timestamp
        mock_query.first.return_value = (datetime.now(),)

        result = MarketDataService.get_latest_timestamp(mock_db, "AAPL")

        assert result is not None
        assert isinstance(result, datetime)

    def test_get_latest_timestamp_not_found(self):
        """Test get_latest_timestamp when not found."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = None

        result = MarketDataService.get_latest_timestamp(mock_db, "INVALID")

        assert result is None


class TestKafkaServiceComprehensive:
    """Comprehensive tests for KafkaService."""

    @pytest.mark.asyncio
    @patch("app.services.kafka_service.AIOKafkaProducer")
    async def test_produce_price_event_success(self, mock_producer):
        """Test produce_price_event success."""
        mock_producer_instance = AsyncMock()
        mock_producer.return_value = mock_producer_instance
        mock_producer_instance.start.return_value = None
        mock_producer_instance.send_and_wait.return_value = None

        kafka_service = KafkaService()
        result = await kafka_service.produce_price_event("AAPL", 150.0)

        assert result is True
        mock_producer_instance.send_and_wait.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.kafka_service.AIOKafkaProducer")
    async def test_produce_price_event_failure(self, mock_producer):
        """Test produce_price_event failure."""
        mock_producer_instance = AsyncMock()
        mock_producer.return_value = mock_producer_instance
        mock_producer_instance.start.return_value = None
        mock_producer_instance.send_and_wait.side_effect = Exception("Kafka error")

        kafka_service = KafkaService()
        result = await kafka_service.produce_price_event("AAPL", 150.0)

        assert result is False

    @pytest.mark.asyncio
    @patch("app.services.kafka_service.AIOKafkaConsumer")
    async def test_consume_messages_success(self, mock_consumer):
        """Test consume_messages success."""
        mock_consumer_instance = AsyncMock()
        mock_consumer.return_value = mock_consumer_instance
        mock_consumer_instance.start.return_value = None
        mock_consumer_instance.getmany.return_value = {
            ("test-topic", 0): [AsyncMock(value=b'{"symbol": "AAPL", "price": 150.0}')]
        }

        kafka_service = KafkaService()
        result = await kafka_service.consume_messages("test-topic")

        assert len(result) == 1
        assert result[0]["symbol"] == "AAPL"

    @pytest.mark.asyncio
    @patch("app.services.kafka_service.AIOKafkaConsumer")
    async def test_consume_messages_exception(self, mock_consumer):
        """Test consume_messages with exception."""
        mock_consumer_instance = AsyncMock()
        mock_consumer.return_value = mock_consumer_instance
        mock_consumer_instance.start.return_value = None
        mock_consumer_instance.getmany.side_effect = Exception("Kafka error")

        kafka_service = KafkaService()
        result = await kafka_service.consume_messages("test-topic")

        assert result == []

    @pytest.mark.asyncio
    async def test_close_success(self):
        """Test close method success."""
        kafka_service = KafkaService()
        # Should not raise any exception
        await kafka_service.close()

    @pytest.mark.asyncio
    @patch("app.services.kafka_service.AIOKafkaProducer")
    async def test_produce_batch_events(self, mock_producer):
        """Test producing multiple events."""
        mock_producer_instance = AsyncMock()
        mock_producer.return_value = mock_producer_instance
        mock_producer_instance.start.return_value = None
        mock_producer_instance.send_and_wait.return_value = None

        kafka_service = KafkaService()
        events = [("AAPL", 150.0), ("GOOGL", 2500.0), ("MSFT", 300.0)]

        for symbol, price in events:
            result = await kafka_service.produce_price_event(symbol, price)
            assert result is True

        assert mock_producer_instance.send_and_wait.call_count == 3

    @pytest.mark.asyncio
    @patch("app.services.kafka_service.AIOKafkaProducer")
    async def test_kafka_service_connection_error(self, mock_producer):
        """Test KafkaService with connection error."""
        mock_producer.side_effect = Exception("Kafka connection failed")

        kafka_service = KafkaService()
        result = await kafka_service.produce_price_event("AAPL", 150.0)

        assert result is False


class TestRedisServiceComprehensive:
    """Comprehensive tests for RedisService."""

    @pytest.mark.asyncio
    @patch("redis.asyncio.Redis.from_url")
    async def test_store_price_data_success(self, mock_redis):
        """Test store_price_data success."""
        mock_redis_instance = AsyncMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.zadd.return_value = 1

        redis_service = RedisService()
        result = await redis_service.store_price_data("AAPL", 150.0, 1234567890)

        assert result is True
        mock_redis_instance.zadd.assert_called_once()

    @pytest.mark.asyncio
    @patch("redis.asyncio.Redis.from_url")
    async def test_store_price_data_failure(self, mock_redis):
        """Test store_price_data failure."""
        mock_redis_instance = AsyncMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.zadd.side_effect = Exception("Redis error")

        redis_service = RedisService()
        result = await redis_service.store_price_data("AAPL", 150.0, 1234567890)

        assert result is False

    @pytest.mark.asyncio
    @patch("redis.asyncio.Redis.from_url")
    async def test_get_price_history_success(self, mock_redis):
        """Test get_price_history success."""
        import time

        now_ms = int(time.time() * 1000)
        ts1 = now_ms - 1000
        ts2 = now_ms - 500
        mock_redis_instance = AsyncMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.keys.return_value = [
            f"price:AAPL:{ts1}",
            f"price:AAPL:{ts2}",
        ]

        async def get_side_effect(key):
            if key == f"price:AAPL:{ts1}":
                return f'{{"price": 150.0, "timestamp": {ts1}}}'.encode()
            elif key == f"price:AAPL:{ts2}":
                return f'{{"price": 151.0, "timestamp": {ts2}}}'.encode()
            return None

        mock_redis_instance.get.side_effect = get_side_effect

        redis_service = RedisService()
        result = await redis_service.get_price_history("AAPL", 3600)

        assert len(result) == 2
        assert result[0]["price"] == 150.0
        assert result[1]["price"] == 151.0

    @pytest.mark.asyncio
    @patch("redis.asyncio.Redis.from_url")
    async def test_get_price_history_empty(self, mock_redis):
        """Test get_price_history with empty result."""
        mock_redis_instance = AsyncMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.keys.return_value = []

        redis_service = RedisService()
        result = await redis_service.get_price_history("AAPL", 3600)

        assert result == []

    @pytest.mark.asyncio
    @patch("redis.asyncio.Redis.from_url")
    async def test_get_latest_price_success(self, mock_redis):
        """Test get_latest_price success."""
        mock_redis_instance = AsyncMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.get.return_value = b"150.0"

        redis_service = RedisService()
        result = await redis_service.get_latest_price("AAPL")

        assert result is not None
        assert result["price"] == 150.0
        assert result["symbol"] == "AAPL"

    @pytest.mark.asyncio
    @patch("redis.asyncio.Redis.from_url")
    async def test_get_latest_price_not_found(self, mock_redis):
        """Test get_latest_price when not found."""
        mock_redis_instance = AsyncMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.get.return_value = None

        redis_service = RedisService()
        result = await redis_service.get_latest_price("AAPL")

        assert result is None

    @pytest.mark.asyncio
    @patch("redis.asyncio.Redis.from_url")
    async def test_delete_price_data_success(self, mock_redis):
        """Test delete_price_data success."""
        mock_redis_instance = AsyncMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.zremrangebyscore.return_value = 5

        redis_service = RedisService()
        result = await redis_service.delete_price_data("AAPL", 3600)

        assert result == 5

    @pytest.mark.asyncio
    @patch("redis.asyncio.Redis.from_url")
    async def test_get_price_statistics_success(self, mock_redis):
        """Test get_price_statistics success."""
        import time

        now_ms = int(time.time() * 1000)
        ts1 = now_ms - 1000
        ts2 = now_ms - 500
        ts3 = now_ms - 250
        mock_redis_instance = AsyncMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.keys.return_value = [
            f"price:AAPL:{ts1}",
            f"price:AAPL:{ts2}",
            f"price:AAPL:{ts3}",
        ]

        async def get_side_effect(key):
            if key == f"price:AAPL:{ts1}":
                return f'{{"price": 150.0, "timestamp": {ts1}}}'.encode()
            elif key == f"price:AAPL:{ts2}":
                return f'{{"price": 151.0, "timestamp": {ts2}}}'.encode()
            elif key == f"price:AAPL:{ts3}":
                return f'{{"price": 152.0, "timestamp": {ts3}}}'.encode()
            return None

        mock_redis_instance.get.side_effect = get_side_effect

        redis_service = RedisService()
        result = await redis_service.get_price_statistics("AAPL", 3600)

        assert result is not None
        assert "min" in result
        assert "max" in result
        assert "avg" in result

    @pytest.mark.asyncio
    @patch("redis.asyncio.Redis.from_url")
    async def test_get_price_statistics_empty(self, mock_redis):
        """Test get_price_statistics with empty data."""
        mock_redis_instance = AsyncMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.keys.return_value = []

        redis_service = RedisService()
        result = await redis_service.get_price_statistics("AAPL", 3600)

        assert result is None

    @pytest.mark.asyncio
    @patch("redis.asyncio.Redis.from_url")
    async def test_clear_all_data_success(self, mock_redis):
        """Test clear_all_data success."""
        mock_redis_instance = AsyncMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.flushdb.return_value = True

        redis_service = RedisService()
        result = await redis_service.clear_all_data()

        assert result is True

    @pytest.mark.asyncio
    @patch("redis.asyncio.Redis.from_url")
    async def test_get_connection_info_success(self, mock_redis):
        """Test get_connection_info success."""
        mock_redis_instance = AsyncMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.info.return_value = {
            "redis_version": "7.0.0",
            "redis_mode": "standalone",
        }

        redis_service = RedisService()
        result = await redis_service.get_connection_info()

        assert result is not None
        assert "status" in result
        assert result["status"] == "connected"

    @pytest.mark.asyncio
    @patch("redis.asyncio.Redis.from_url")
    async def test_ping_success(self, mock_redis):
        """Test ping success."""
        mock_redis_instance = AsyncMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.ping.return_value = True

        redis_service = RedisService()
        result = await redis_service.ping()

        assert result is True

    @pytest.mark.asyncio
    @patch("redis.asyncio.Redis.from_url")
    async def test_ping_failure(self, mock_redis):
        """Test ping failure."""
        mock_redis_instance = AsyncMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.ping.side_effect = Exception("Connection error")

        redis_service = RedisService()
        result = await redis_service.ping()

        assert result is False

    @pytest.mark.asyncio
    @patch("redis.asyncio.Redis.from_url")
    async def test_redis_service_connection_error(self, mock_redis):
        """Test RedisService with connection error."""
        mock_redis.side_effect = Exception("Redis connection failed")

        redis_service = RedisService()
        result = await redis_service.store_price_data("AAPL", 150.0, 1234567890)

        assert result is False


class TestServiceErrorHandling:
    """Test error handling across all services."""

    def test_market_data_service_database_connection_error(self):
        """Test MarketDataService with database connection error."""
        mock_db = Mock(spec=Session)
        mock_db.query.side_effect = SQLAlchemyError("Connection failed")

        with pytest.raises(SQLAlchemyError):
            MarketDataService.get_market_data(mock_db, skip=0, limit=10)

    def test_service_initialization_errors(self):
        """Test service initialization with invalid configurations."""
        # Test with invalid Redis URL
        with patch("app.services.redis_service.settings") as mock_settings:
            mock_settings.REDIS_URL = "invalid://url"
            redis_service = RedisService()
            assert redis_service is not None  # Should handle gracefully

        # Test with invalid Kafka configuration
        with patch("app.services.kafka_service.settings") as mock_settings:
            mock_settings.KAFKA_BOOTSTRAP_SERVERS = "invalid:9092"
            kafka_service = KafkaService()
            assert kafka_service is not None  # Should handle gracefully
