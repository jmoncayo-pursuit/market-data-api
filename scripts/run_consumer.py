"""Script to run the market data consumer."""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.db.session import SessionLocal
from app.services.kafka_service import KafkaService
from app.services.market_data import MarketDataService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Run the consumer script."""
    db = SessionLocal()
    try:
        market_data_service = MarketDataService(db)
        kafka_service = KafkaService()

        logger.info("Starting Kafka consumer...")
        await kafka_service.consume_price_events(market_data_service)
    except Exception as e:
        logger.error(f"Error in consumer: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
