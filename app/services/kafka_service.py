"""Kafka service module for handling Kafka operations."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaError

from app.core.config import settings
from app.services.market_data import MarketDataService

logger = logging.getLogger(__name__)


class KafkaService:
    """Service class for handling Kafka operations."""

    def __init__(self) -> None:
        """Initialize Kafka service without immediate connection."""
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumer: Optional[AIOKafkaConsumer] = None
        self._lock = asyncio.Lock()

    async def _get_producer(self) -> Optional[AIOKafkaProducer]:
        """Get the Kafka producer, creating it if it doesn't exist."""
        async with self._lock:
            if self.producer is None:
                try:
                    self.producer = AIOKafkaProducer(
                        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS
                    )
                    await self.producer.start()
                except Exception as e:
                    logger.error(f"Error connecting to Kafka producer: {e}")
                    self.producer = None
                    return None
        return self.producer

    async def _get_consumer(self, topic: str) -> Optional[AIOKafkaConsumer]:
        """Get the Kafka consumer, creating it if it doesn't exist."""
        async with self._lock:
            if self.consumer is None:
                try:
                    self.consumer = AIOKafkaConsumer(
                        topic,
                        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                        group_id=settings.KAFKA_CONSUMER_GROUP,
                    )
                    await self.consumer.start()
                except Exception as e:
                    logger.error(f"Error connecting to Kafka consumer: {e}")
                    self.consumer = None
                    return None
        return self.consumer

    async def produce_message(
        self, topic: str, key: str, value: Dict[str, Any]
    ) -> bool:
        """Produce a message to Kafka."""
        producer = await self._get_producer()
        if not producer:
            return False

        try:
            await producer.send_and_wait(
                topic, json.dumps(value).encode(), key=key.encode()
            )
            return True
        except Exception as e:
            self._log_error("Kafka msg err", e)
            return False

    async def consume_messages(
        self, topic: str, timeout: int = 1000
    ) -> List[Dict[str, Any]]:
        """Consume messages from Kafka."""
        consumer = await self._get_consumer(topic)
        if not consumer:
            return []

        try:
            messages = []
            result = await consumer.getmany(timeout_ms=timeout)
            for tp, msgs in result.items():
                for msg in msgs:
                    try:
                        value = json.loads(msg.value.decode("utf-8"))
                        messages.append(value)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to decode message: {msg.value}")
            return messages
        except Exception as e:
            self._log_error("Kafka msg err", e)
            return []

    def _log_error(self, msg: str, exc: Exception) -> None:
        """Log error with proper formatting."""
        logger.error(f"{msg}: {exc}")

    async def close(self) -> None:
        """Close the Kafka producer and consumer."""
        try:
            if self.producer:
                await self.producer.stop()
                self.producer = None
        except Exception as e:
            logger.error(f"Error closing producer: {e}")

        try:
            if self.consumer:
                await self.consumer.stop()
                self.consumer = None
        except Exception as e:
            logger.error(f"Error closing consumer: {e}")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with proper cleanup."""
        await self.close()

    async def produce_price_event(
        self, symbol: str, price: float, topic: str = "price-events"
    ) -> bool:
        """Produce a price event to Kafka."""
        producer = await self._get_producer()
        if not producer:
            return False

        message = {"symbol": symbol, "price": price}
        try:
            await producer.send_and_wait(
                topic, key=symbol.encode(), value=json.dumps(message).encode()
            )
            return True
        except Exception as e:
            self._log_error("Kafka msg err", e)
            return False

    def consume_price_events(self, market_data_service: MarketDataService) -> None:
        """
        Consume price events and calculate moving averages.

        Args:
            market_data_service: Market data service instance
        """
        if not self.consumer:
            # Initialize consumer if not already done
            asyncio.create_task(self._get_consumer("price-events"))
            return

        try:
            while True:
                msg = self.consumer.poll(1.0)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        logger.error(f"Consumer error: {msg.error()}")
                        continue

                try:
                    data = json.loads(msg.value().decode("utf-8"))
                    symbol = data["symbol"]

                    # Calculate moving average
                    ma = market_data_service.calculate_moving_average(
                        market_data_service.db, symbol
                    )
                    if ma is not None:
                        logger.info(f"Calculated moving average for {symbol}: {ma}")

                except Exception as e:
                    self._log_error("Kafka msg err", e)
                    continue

        except KeyboardInterrupt:
            pass
        finally:
            if self.consumer:
                self.consumer.close()

    def some_method(self):
        """Describe what this method does."""
        # ... existing code ...
