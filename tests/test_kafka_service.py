"""Tests for Kafka service."""

import asyncio
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.kafka_service import KafkaService


class TestKafkaService:
    """Test cases for KafkaService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.kafka_service = KafkaService()

    def teardown_method(self):
        """Clean up test fixtures."""
        # Let pytest-asyncio handle event loop lifecycle. No manual cleanup needed.
        pass

    @pytest.mark.asyncio
    async def test_produce_message_success(self):
        """Test successful message production."""
        with patch(
            "app.services.kafka_service.AIOKafkaProducer"
        ) as mock_producer_class:
            mock_producer = AsyncMock()
            mock_producer_class.return_value = mock_producer
            mock_producer.start = AsyncMock()
            mock_producer.send_and_wait = AsyncMock()

            result = await self.kafka_service.produce_message(
                "test-topic", "test-key", {"test": "data"}
            )

            assert result is True
            mock_producer.send_and_wait.assert_called_once()

    @pytest.mark.asyncio
    async def test_produce_message_failure(self):
        """Test message production failure."""
        with patch(
            "app.services.kafka_service.AIOKafkaProducer"
        ) as mock_producer_class:
            mock_producer_class.side_effect = Exception("Connection failed")

            result = await self.kafka_service.produce_message(
                "test-topic", "test-key", {"test": "data"}
            )

        assert result is False

    @pytest.mark.asyncio
    async def test_consume_messages_success(self):
        """Test successful message consumption."""
        with patch(
            "app.services.kafka_service.AIOKafkaConsumer"
        ) as mock_consumer_class:
            mock_consumer = AsyncMock()
            mock_consumer_class.return_value = mock_consumer
            mock_consumer.start = AsyncMock()
            mock_consumer.getmany = AsyncMock()

            # Mock message data
            mock_msg = MagicMock()
            mock_msg.value = json.dumps({"test": "data"}).encode()
            mock_consumer.getmany.return_value = {("test-topic", 0): [mock_msg]}

            result = await self.kafka_service.consume_messages("test-topic")

            assert len(result) == 1
            assert result[0]["test"] == "data"

    @pytest.mark.asyncio
    async def test_consume_messages_with_error(self):
        """Test message consumption with error."""
        with patch(
            "app.services.kafka_service.AIOKafkaConsumer"
        ) as mock_consumer_class:
            mock_consumer = AsyncMock()
            mock_consumer_class.return_value = mock_consumer
            mock_consumer.start = AsyncMock()
            mock_consumer.getmany = AsyncMock(side_effect=Exception("Consumer error"))

            result = await self.kafka_service.consume_messages("test-topic")

            assert result == []

    @pytest.mark.asyncio
    async def test_consume_messages_json_error(self):
        """Test message consumption with JSON decode error."""
        with patch(
            "app.services.kafka_service.AIOKafkaConsumer"
        ) as mock_consumer_class:
            mock_consumer = AsyncMock()
            mock_consumer_class.return_value = mock_consumer
            mock_consumer.start = AsyncMock()
            mock_consumer.getmany = AsyncMock()

            # Mock invalid JSON message
            mock_msg = MagicMock()
            mock_msg.value = b"invalid json"
            mock_consumer.getmany.return_value = {("test-topic", 0): [mock_msg]}

            result = await self.kafka_service.consume_messages("test-topic")

            assert result == []

    @pytest.mark.asyncio
    async def test_consume_messages_exception(self):
        """Test message consumption with general exception."""
        with patch(
            "app.services.kafka_service.AIOKafkaConsumer"
        ) as mock_consumer_class:
            mock_consumer_class.side_effect = Exception("Connection failed")

            result = await self.kafka_service.consume_messages("test-topic")

            assert result == []

    @pytest.mark.asyncio
    async def test_delivery_report_success(self):
        """Test successful delivery report."""
        with patch(
            "app.services.kafka_service.AIOKafkaProducer"
        ) as mock_producer_class:
            mock_producer = AsyncMock()
            mock_producer_class.return_value = mock_producer
            mock_producer.start = AsyncMock()
            mock_producer.send_and_wait = AsyncMock()

            result = await self.kafka_service.produce_price_event("AAPL", 150.0)

            assert result is True
            mock_producer.send_and_wait.assert_called_once()

    @pytest.mark.asyncio
    async def test_delivery_report_error(self):
        """Test delivery report with error."""
        with patch(
            "app.services.kafka_service.AIOKafkaProducer"
        ) as mock_producer_class:
            mock_producer = AsyncMock()
            mock_producer_class.return_value = mock_producer
            mock_producer.start = AsyncMock()
            mock_producer.send_and_wait = AsyncMock(
                side_effect=Exception("Send failed")
            )

            result = await self.kafka_service.produce_price_event("AAPL", 150.0)

            assert result is False

    @pytest.mark.asyncio
    async def test_produce_price_event_no_producer(self):
        """Test price event production with no producer."""
        with patch(
            "app.services.kafka_service.AIOKafkaProducer"
        ) as mock_producer_class:
            mock_producer_class.side_effect = Exception("Connection failed")

            result = await self.kafka_service.produce_price_event("AAPL", 150.0)

        assert result is False

    @pytest.mark.asyncio
    async def test_produce_price_event_exception(self):
        """Test price event production with exception."""
        with patch(
            "app.services.kafka_service.AIOKafkaProducer"
        ) as mock_producer_class:
            mock_producer = AsyncMock()
            mock_producer_class.return_value = mock_producer
            mock_producer.start = AsyncMock()
            mock_producer.send_and_wait = AsyncMock(
                side_effect=Exception("Send failed")
            )

            result = await self.kafka_service.produce_price_event("AAPL", 150.0)

        assert result is False

    @pytest.mark.asyncio
    async def test_consume_price_events_success(self):
        """Test successful price events consumption."""
        with patch(
            "app.services.kafka_service.AIOKafkaConsumer"
        ) as mock_consumer_class:
            mock_consumer = AsyncMock()
            mock_consumer_class.return_value = mock_consumer
            mock_consumer.start = AsyncMock()
            mock_consumer.getmany = AsyncMock()

            # Mock price event message
            mock_msg = MagicMock()
            mock_msg.value = json.dumps({"symbol": "AAPL", "price": 150.0}).encode()
            mock_consumer.getmany.return_value = {("price-events", 0): [mock_msg]}

            result = await self.kafka_service.consume_messages("price-events")

            assert len(result) == 1
            assert result[0]["symbol"] == "AAPL"
            assert result[0]["price"] == 150.0

    @pytest.mark.asyncio
    async def test_consume_price_events_no_consumer(self):
        """Test price events consumption with no consumer."""
        with patch(
            "app.services.kafka_service.AIOKafkaConsumer"
        ) as mock_consumer_class:
            mock_consumer_class.side_effect = Exception("Connection failed")

            result = await self.kafka_service.consume_messages("price-events")

            assert result == []

    @pytest.mark.asyncio
    async def test_consume_price_events_partition_eof(self):
        """Test price events consumption with partition EOF."""
        with patch(
            "app.services.kafka_service.AIOKafkaConsumer"
        ) as mock_consumer_class:
            mock_consumer = AsyncMock()
            mock_consumer_class.return_value = mock_consumer
            mock_consumer.start = AsyncMock()
            mock_consumer.getmany = AsyncMock(return_value={})

            result = await self.kafka_service.consume_messages("price-events")

            assert result == []

    @pytest.mark.asyncio
    async def test_consume_price_events_consumer_error(self):
        """Test price events consumption with consumer error."""
        with patch(
            "app.services.kafka_service.AIOKafkaConsumer"
        ) as mock_consumer_class:
            mock_consumer = AsyncMock()
            mock_consumer_class.return_value = mock_consumer
            mock_consumer.start = AsyncMock()
            mock_consumer.getmany = AsyncMock(side_effect=Exception("Consumer error"))

            result = await self.kafka_service.consume_messages("price-events")

            assert result == []

    @pytest.mark.asyncio
    async def test_consume_price_events_json_error(self):
        """Test price events consumption with JSON error."""
        with patch(
            "app.services.kafka_service.AIOKafkaConsumer"
        ) as mock_consumer_class:
            mock_consumer = AsyncMock()
            mock_consumer_class.return_value = mock_consumer
            mock_consumer.start = AsyncMock()
            mock_consumer.getmany = AsyncMock()

            # Mock invalid JSON message
            mock_msg = MagicMock()
            mock_msg.value = b"invalid json"
            mock_consumer.getmany.return_value = {("price-events", 0): [mock_msg]}

            result = await self.kafka_service.consume_messages("price-events")

            assert result == []

    @pytest.mark.asyncio
    async def test_consume_price_events_exception(self):
        """Test price events consumption with exception."""
        with patch(
            "app.services.kafka_service.AIOKafkaConsumer"
        ) as mock_consumer_class:
            mock_consumer = AsyncMock()
            mock_consumer_class.return_value = mock_consumer
            mock_consumer.start = AsyncMock()
            mock_consumer.getmany = AsyncMock(side_effect=Exception("General error"))

            result = await self.kafka_service.consume_messages("price-events")

            assert result == []

    @pytest.mark.skipif(
        os.environ.get("CI") == "true",
        reason="KeyboardInterrupt test not supported in CI",
    )
    @pytest.mark.asyncio
    async def test_consume_price_events_keyboard_interrupt(self):
        """Test price events consumption with keyboard interrupt."""
        with patch(
            "app.services.kafka_service.AIOKafkaConsumer"
        ) as mock_consumer_class:
            mock_consumer = AsyncMock()
            mock_consumer_class.return_value = mock_consumer
            mock_consumer.start = AsyncMock()
            mock_consumer.getmany = AsyncMock(side_effect=KeyboardInterrupt())

            # The method should handle KeyboardInterrupt gracefully
            result = await self.kafka_service.consume_messages("price-events")

            # Should return empty list when interrupted
            assert result == []

    def test_log_error(self):
        """Test error logging."""
        with patch("app.services.kafka_service.logger") as mock_logger:
            test_exception = Exception("Test error")
            self.kafka_service._log_error("Test message", test_exception)
            mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_success(self):
        """Test successful connection closure."""
        with patch(
            "app.services.kafka_service.AIOKafkaProducer"
        ) as mock_producer_class:
            mock_producer = AsyncMock()
            mock_producer_class.return_value = mock_producer
            mock_producer.start = AsyncMock()
            mock_producer.stop = AsyncMock()

            # Create producer first
            await self.kafka_service._get_producer()

            # Then close
            await self.kafka_service.close()

            mock_producer.stop.assert_called_once()
