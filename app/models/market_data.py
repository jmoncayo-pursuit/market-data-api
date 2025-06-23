"""Market data models for the Market Data Service."""

import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy.types import CHAR, TypeDecorator

from app.db.base import Base


# Cross-database UUID type
class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise stores as CHAR(36).
    """

    impl = CHAR

    def load_dialect_impl(self, dialect):
        """Return the appropriate type descriptor for the dialect."""
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        """Convert Python value to a value suitable for the database."""
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        if not isinstance(value, uuid.UUID):
            return str(uuid.UUID(value))
        return str(value)

    def process_result_value(self, value, dialect):
        """Convert database value to a Python UUID object."""
        if value is None:
            return value
        return uuid.UUID(value)


class TimestampMixin:
    """Timestamp mixin for models."""

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class MarketData(Base):
    """Market data model for storing market data records."""

    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    symbol = Column(String, index=True, nullable=False)
    price = Column(Float, nullable=False)
    volume = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    source = Column(String, nullable=True)
    raw_data = Column(String, nullable=True)

    def __repr__(self) -> str:
        """
        Return a string representation of the market data record.

        Returns:
            String representation of the market data record
        """
        return (
            f"<MarketData(symbol='{self.symbol}', "
            f"price={self.price}, volume={self.volume}, "
            f"timestamp='{self.timestamp}')>"
        )


class RawMarketData(Base):
    """Raw market data model for storing unprocessed market data."""

    __tablename__ = "raw_market_data"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    symbol = Column(String, index=True, nullable=False)
    raw_data = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    source = Column(String, nullable=False)
    processed = Column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        """
        Return a string representation of the raw market data record.

        Returns:
            String representation of the raw market data record
        """
        return (
            f"<RawMarketData(symbol='{self.symbol}', "
            f"timestamp='{self.timestamp}', processed={self.processed})>"
        )


class ProcessedPrice(Base):
    """Processed price model for storing processed price data."""

    __tablename__ = "processed_prices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    symbol = Column(String, index=True, nullable=False)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    raw_data_id = Column(Integer, ForeignKey("raw_market_data.id"))
    raw_data = relationship("RawMarketData")

    def __repr__(self) -> str:
        """
        Return a string representation of the processed price record.

        Returns:
            String representation of the processed price record
        """
        return (
            f"<ProcessedPrice(symbol='{self.symbol}', "
            f"price={self.price}, timestamp='{self.timestamp}')>"
        )


class MovingAverage(Base, TimestampMixin):
    """Model for storing moving average calculations."""

    __tablename__ = "moving_averages"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    symbol = Column(String, nullable=False, index=True)
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    window_size = Column(Integer, nullable=False)


class PollingConfig(Base, TimestampMixin):
    """Polling config model."""

    __tablename__ = "polling_configs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    job_id = Column(String, nullable=False, unique=True, index=True)
    symbols = Column(JSON, nullable=False)  # Array of symbols
    interval = Column(Integer, nullable=False)  # Interval in seconds
    status = Column(String, nullable=False)  # active, paused, completed
