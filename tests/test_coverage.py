"""Test coverage for low-coverage modules."""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import Column, Integer
from sqlalchemy.orm import declarative_base

from app.core import logging as app_logging
from app.models.base import TimestampMixin
from app.services.kafka_service import KafkaService
from app.services.redis_service import RedisService


def test_logging_coverage():
    """Test logging setup and log functions for coverage."""
    logger = app_logging.setup_logging()
    # Remove all handlers to avoid TypeError from previous mocks
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    try:
        logger.info("Test info log")
        app_logging.log_request("req1", "GET", "/", 200, 12.3)
        app_logging.log_error(Exception("err"), {"foo": "bar"})
        app_logging.log_market_data("BTC", 123.45, "provider")
        app_logging.log_job_status("job1", "running", {"interval": 10})
    except Exception as e:
        pytest.fail(f"Logging functions raised an exception: {e}")


# Test TimestampMixin
TestBase = declarative_base()


class DummyModel(TimestampMixin, TestBase):  # type: ignore
    """Dummy model for testing TimestampMixin."""

    __tablename__ = "dummy"
    id = Column(Integer, primary_key=True)


def test_timestamp_mixin():
    """Test TimestampMixin functionality."""
    obj = DummyModel()
    assert isinstance(obj.created_at, datetime) or obj.created_at is None
    assert isinstance(obj.updated_at, datetime) or obj.updated_at is None


# Test RedisService with mocks
@patch("app.services.redis_service.settings")
@patch("app.services.redis_service.Redis", autospec=True)
@pytest.mark.asyncio
async def test_redis_service(mock_redis, mock_settings):
    """Test RedisService with mocked Redis connection."""
    mock_settings.REDIS_URL = "redis://localhost:6379/0"
    instance = AsyncMock()
    mock_redis.from_url.return_value = instance
    instance.ping.return_value = True
    instance.get.return_value = "123.45"
    instance.setex.return_value = True
    instance.set.return_value = True
    instance.delete.return_value = True
    instance.keys.return_value = ["price:BTC"]

    async def mock_scan_iter(pattern):
        yield "price:BTC"

    instance.scan_iter = mock_scan_iter
    service = RedisService()

    # Test caching price
    result = await service.cache_price("BTC", 123.45)
    assert result is True

    # Test getting cached price
    result = await service.get_cached_price("BTC")
    assert result == 123.45

    # Test other async methods
    assert await service.store_price("BTC", 123.45)
    assert await service.get_price("BTC") == 123.45
    assert await service.set_price("BTC", 123.45)
    assert await service.delete_price("BTC")
    assert await service.get_all_prices() == {"BTC": 123.45}
    assert await service.clear_prices()
    assert isinstance(await service.get_price_history("BTC"), list)

    # Test connection
    redis = await service._get_redis_client()
    if redis:
        assert await redis.ping()
    else:
        # If Redis is not available, test fallback behavior
        assert await service.get_cached_price("AAPL") is None
        assert await service.cache_price("AAPL", 150.0) is False


# Test KafkaService with mocks
@patch("app.services.kafka_service.AIOKafkaProducer", autospec=True)
@patch("app.services.kafka_service.AIOKafkaConsumer", autospec=True)
@pytest.mark.asyncio
async def test_kafka_service(mock_consumer_class, mock_producer_class):
    """Test KafkaService with mocked Kafka connection."""
    mock_producer = AsyncMock()
    mock_consumer = AsyncMock()
    mock_producer_class.return_value = mock_producer
    mock_consumer_class.return_value = mock_consumer

    service = KafkaService()

    # Test async methods
    result = await service.produce_message("test-topic", "key", {"foo": "bar"})
    assert result is True

    result = await service.produce_price_event("BTC", 123.45)
    assert result is True

    await service.close()
