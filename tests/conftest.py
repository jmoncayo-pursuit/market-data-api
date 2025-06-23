"""Test configuration and fixtures."""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.rate_limit import init_rate_limiter
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.market_data import MarketData
from app.schemas.market_data import MarketDataCreate

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function", autouse=True)
def initialize_rate_limiter(event_loop):
    """Initialize rate limiter for all tests."""
    redis_url = "redis://localhost:6379/0"
    try:
        # Use a shorter timeout for tests
        event_loop.run_until_complete(
            asyncio.wait_for(init_rate_limiter(redis_url), timeout=5.0)
        )
        print("Rate limiter initialized in session fixture")
    except asyncio.TimeoutError:
        print("Warning: Rate limiter initialization timed out in session fixture")
    except Exception as e:
        print(f"Warning: Could not initialize rate limiter in session fixture: {e}")


@pytest.fixture(scope="function", autouse=True)
def ensure_rate_limiter_initialized():
    """Ensure rate limiter is initialized for each test function."""
    try:
        from app.core.rate_limit import get_rate_limiter

        result = get_rate_limiter()
        if result is None:
            # If not initialized, try to initialize it with timeout
            import asyncio

            from app.core.rate_limit import init_rate_limiter

            redis_url = "redis://localhost:6379/0"
            try:
                asyncio.run(asyncio.wait_for(init_rate_limiter(redis_url), timeout=2.0))
                print("Rate limiter initialized in function fixture")
            except asyncio.TimeoutError:
                print(
                    "Warning: Rate limiter initialization timed out in function fixture"
                )
            except Exception as e:
                print(
                    f"Warning: Could not initialize rate limiter in function fixture: {e}"
                )
    except Exception as e:
        print(f"Warning: Could not ensure rate limiter initialization: {e}")


# Disabled: Top-level event loop initialization breaks pytest-asyncio
# try:
#     redis_url = "redis://localhost:6379/0"
#     asyncio.run(asyncio.wait_for(init_rate_limiter(redis_url), timeout=3.0))
#     print("Rate limiter initialized on conftest import")
# except asyncio.TimeoutError:
#     print("Warning: Rate limiter initialization timed out on conftest import")
# except Exception as e:
#     print(f"Warning: Could not initialize rate limiter on conftest import: {e}")


class DummyMarketDataService:
    """Dummy market data service for integration tests."""

    @staticmethod
    def create_market_data(db, market_data: MarketDataCreate):
        """Create dummy market data with validation."""
        # Simulate validation error
        if not market_data.symbol or market_data.price < 0 or market_data.volume <= 0:
            raise ValueError("Invalid market data input")

        # Create the market data object
        db_obj = MarketData(
            id=1,
            symbol=str(market_data.symbol),
            price=market_data.price,
            volume=market_data.volume,
            source=str(market_data.source) if market_data.source else "test",
            raw_data=str(market_data.raw_data) if market_data.raw_data else None,
            timestamp=datetime.now(timezone.utc),
        )

        # Add to database session and commit
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def update_market_data(db, market_data_id: int, market_data):
        """Update dummy market data."""
        # Find the existing record
        db_obj = db.query(MarketData).filter(MarketData.id == market_data_id).first()
        if not db_obj:
            return None

        # Update the fields - handle Pydantic model properly
        if market_data.price is not None:
            db_obj.price = market_data.price
        if market_data.volume is not None:
            db_obj.volume = market_data.volume
        if market_data.source is not None:
            db_obj.source = market_data.source
        if market_data.raw_data is not None:
            db_obj.raw_data = market_data.raw_data
        if market_data.symbol is not None:
            db_obj.symbol = market_data.symbol

        # Commit the changes
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def get_market_data(db, skip: int = 0, limit: int = 100):
        """Get dummy market data."""
        return [
            MarketData(
                id=1,
                symbol="AAPL",
                price=150.0,
                volume=1000,
                source="test",
                raw_data=None,
                timestamp=datetime.now(timezone.utc),
            )
        ]

    @staticmethod
    def get_latest_market_data(db, symbol: str):
        """Get dummy latest market data."""
        return MarketData(
            id=1,
            symbol=symbol,
            price=150.0,
            volume=1000,
            source="test",
            raw_data=None,
            timestamp=datetime.now(timezone.utc),
        )

    @staticmethod
    def get_market_data_by_id(db, market_data_id: int):
        """Return None for unknown IDs to simulate 404."""
        if market_data_id == 1:
            return MarketData(
                id=1,
                symbol="AAPL",
                price=150.0,
                volume=1000,
                source="test",
                raw_data=None,
                timestamp=datetime.now(timezone.utc),
            )
        return None

    @staticmethod
    def get_all_symbols(db):
        """Get all symbols."""
        return ["AAPL", "GOOGL"]


class DummyRedisService:
    """Dummy Redis service for integration tests."""

    async def get_latest_price(self, symbol: str):
        """Get dummy latest price."""
        return {
            "symbol": symbol,
            "price": 150.0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def get_price_history(self, symbol: str, window: int = 3600):
        """Get dummy price history."""
        return [
            {
                "symbol": symbol,
                "price": 150.0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ]


class DummyKafkaService:
    """Dummy Kafka service for integration tests."""

    async def produce_price_event(self, symbol: str, price: float):
        """Produce dummy price event."""
        return True

    async def consume_price_events(self, topic: str, limit: int = 10):
        """Consume dummy price events."""
        return [
            {
                "symbol": "AAPL",
                "price": 150.0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ]


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database session."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def integration_client(db_session):
    """Create a test client with dummy services for integration tests."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Override services with dummy implementations
    from app.api.endpoints import prices

    # Store original services
    original_market_data_service = prices.MarketDataService

    # Replace with dummy services
    prices.MarketDataService = DummyMarketDataService

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)

    # Restore original services
    prices.MarketDataService = original_market_data_service
    app.dependency_overrides.clear()


@pytest.fixture
def sample_market_data():
    """Sample market data for testing."""
    return {
        "symbol": "AAPL",
        "price": 150.0,
        "volume": 1000,
        "source": "test",
        "raw_data": None,
    }


@pytest.fixture
def sample_market_data_list():
    """Sample list of market data for testing."""
    return [
        {
            "id": 1,
            "symbol": "AAPL",
            "price": 150.0,
            "volume": 1000,
            "source": "test",
            "raw_data": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": 2,
            "symbol": "GOOGL",
            "price": 2500.0,
            "volume": 500,
            "source": "test",
            "raw_data": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    ]


@pytest.fixture
def mock_redis_service():
    """Mock Redis service for testing."""
    mock_service = AsyncMock()
    mock_service.get_latest_price.return_value = {
        "symbol": "AAPL",
        "price": 150.0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    mock_service.get_price_history.return_value = [
        {
            "symbol": "AAPL",
            "price": 150.0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    ]
    return mock_service


@pytest.fixture
def mock_kafka_service():
    """Mock Kafka service for testing."""
    mock_service = AsyncMock()
    mock_service.produce_price_event.return_value = True
    mock_service.consume_price_events.return_value = []
    mock_service.produce_message.return_value = True
    mock_service.consume_messages.return_value = []
    return mock_service


@pytest.fixture
async def kafka_producer():
    """Create and manage a Kafka producer with proper cleanup."""
    try:
        from aiokafka import AIOKafkaProducer

        producer = AIOKafkaProducer(bootstrap_servers="localhost:9092")
        await producer.start()
        yield producer
    except Exception:
        # If Kafka is not available, yield a mock
        mock_producer = AsyncMock()
        mock_producer.send_and_wait = AsyncMock(return_value=None)
        yield mock_producer
    finally:
        try:
            if hasattr(producer, "stop"):
                await producer.stop()
        except Exception:
            pass


@pytest.fixture
async def kafka_consumer():
    """Create and manage a Kafka consumer with proper cleanup."""
    try:
        from aiokafka import AIOKafkaConsumer

        consumer = AIOKafkaConsumer("test-topic", bootstrap_servers="localhost:9092")
        await consumer.start()
        yield consumer
    except Exception:
        # If Kafka is not available, yield a mock
        mock_consumer = AsyncMock()
        mock_consumer.getmany = AsyncMock(return_value={})
        yield mock_consumer
    finally:
        try:
            if hasattr(consumer, "stop"):
                await consumer.stop()
        except Exception:
            pass


@pytest.fixture
def market_data_service(mock_redis_service, mock_kafka_service):
    """Create a MarketDataService instance with mocked dependencies."""
    from app.services.market_data import MarketDataService

    service = MarketDataService()
    service.redis_service = mock_redis_service
    service.kafka_service = mock_kafka_service
    return service


@pytest.fixture(scope="session")
async def kafka_topics():
    """Create required Kafka topics for testing."""
    try:
        from aiokafka import AIOKafkaProducer

        # Create topics using aiokafka
        producer = AIOKafkaProducer(bootstrap_servers="localhost:9092")
        await producer.start()

        # Create topics by sending messages to them (this will auto-create them)
        topics = ["price-events", "test-topic"]
        for topic in topics:
            try:
                await producer.send_and_wait(topic, b"init", key=b"init")
            except Exception:
                # Topic creation might fail, but that's okay for tests
                pass

        await producer.stop()
    except Exception:
        # If Kafka is not available, skip topic creation
        pass
    yield
