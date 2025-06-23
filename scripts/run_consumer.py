"""Script to run the market data consumer."""

import asyncio
import logging

from app.db.session import SessionLocal
from app.services.kafka_service import KafkaService
from app.services.market_data import MarketDataService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Run the consumer script."""
    db = SessionLocal()
    try:
        market_data_service = MarketDataService(db)
        kafka_service = KafkaService()

        logger.info("Starting Kafka consumer...")
        kafka_service.consume_price_events(market_data_service)
    except Exception as e:
        logger.error(f"Error in consumer: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
