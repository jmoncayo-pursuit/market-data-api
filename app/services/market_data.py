"""Market data service module for handling market data operations."""

import asyncio
import logging
from datetime import UTC, datetime
from functools import wraps
from typing import Any, Dict, List, Optional

import requests  # type: ignore[import-untyped]
from sqlalchemy.orm import Session

from app.models.market_data import MarketData
from app.schemas.market_data import MarketDataCreate, MarketDataUpdate
from app.services.redis_service import RedisService

logger = logging.getLogger(__name__)


def retry_on_failure(max_retries=3, delay=1):
    """
    Retry failed operations up to max_retries times with a delay.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds

    Returns:
        Decorated function
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {str(e)}. Retrying..."
                    )
                    await asyncio.sleep(delay)
            return await func(*args, **kwargs)

        return wrapper

    return decorator


class MarketDataService:
    """Service class for handling market data operations."""

    def __init__(self, db: Session):
        """Initialize MarketDataService with database session."""
        self.db = db
        self.redis_service = RedisService()

    @staticmethod
    def get_market_data(
        db: Session, skip: int = 0, limit: int = 100
    ) -> List[MarketData]:
        """
        Retrieve market data records with pagination.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of market data records
        """
        return db.query(MarketData).offset(skip).limit(limit).all()

    @staticmethod
    def get_market_data_by_symbol(
        db: Session, symbol: str, skip: int = 0, limit: int = 100
    ) -> List[MarketData]:
        """
        Retrieve market data for a specific symbol with pagination.

        Args:
            db: Database session
            symbol: Stock symbol
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of market data records for the symbol
        """
        return (
            db.query(MarketData)
            .filter(MarketData.symbol == symbol)
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def create_market_data(db: Session, market_data: MarketDataCreate) -> MarketData:
        """
        Create a new market data record.

        Args:
            db: Database session
            market_data: Market data to create

        Returns:
            Created market data record
        """
        db_obj = MarketData(**market_data.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def update_market_data(
        db: Session, market_data_id: int, market_data: MarketDataUpdate
    ) -> Optional[MarketData]:
        """
        Update an existing market data record.

        Args:
            db: Database session
            market_data_id: ID of market data to update
            market_data: Updated market data

        Returns:
            Updated market data record or None if not found
        """
        db_obj = db.query(MarketData).filter(MarketData.id == market_data_id).first()
        if not db_obj:
            return None
        for field, value in market_data.model_dump(exclude_unset=True).items():
            setattr(db_obj, field, value)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def delete_market_data(db: Session, market_data_id: int) -> bool:
        """
        Delete a market data record.

        Args:
            db: Database session
            market_data_id: ID of market data to delete

        Returns:
            True if deleted, False if not found
        """
        db_obj = db.query(MarketData).filter(MarketData.id == market_data_id).first()
        if not db_obj:
            return False
        db.delete(db_obj)
        db.commit()
        return True

    @staticmethod
    def get_latest_market_data(db: Session, symbol: str) -> Optional[MarketData]:
        """
        Get the latest market data for a specific symbol.

        Args:
            db: Database session
            symbol: Stock symbol

        Returns:
            Latest market data record or None if not found
        """
        return (
            db.query(MarketData)
            .filter(MarketData.symbol == symbol)
            .order_by(MarketData.timestamp.desc())
            .first()
        )

    @staticmethod
    def get_all_symbols(db: Session) -> List[str]:
        """
        Get all unique symbols from market data.

        Args:
            db: Database session

        Returns:
            List of unique symbols
        """
        return [row[0] for row in db.query(MarketData.symbol).distinct().all()]

    @staticmethod
    def calculate_moving_average(
        db: Session, symbol: str, window: int = 5
    ) -> Optional[float]:
        """
        Calculate the moving average for a symbol over a window of records.

        Args:
            db: Database session
            symbol: Stock symbol
            window: Number of records to include in the average

        Returns:
            Moving average or None if insufficient data
        """
        records = (
            db.query(MarketData)
            .filter(MarketData.symbol == symbol)
            .order_by(MarketData.timestamp.desc())
            .limit(window)
            .all()
        )

        if len(records) < window:
            return None

        total_price = sum(record.price for record in records)
        return total_price / len(records)

    @staticmethod
    def get_latest_timestamp(db: Session, symbol: str) -> Optional[datetime]:
        """
        Get the latest timestamp for a specific symbol.

        Args:
            db: Database session
            symbol: Stock symbol

        Returns:
            Latest timestamp or None if not found
        """
        result = (
            db.query(MarketData.timestamp)
            .filter(MarketData.symbol == symbol)
            .order_by(MarketData.timestamp.desc())
            .first()
        )
        return result[0] if result else None

    @retry_on_failure(max_retries=3)
    async def get_latest_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest price for a symbol from cache or external API.

        Args:
            symbol: Stock symbol

        Returns:
            Latest price or None if not found
        """
        price_data = await self.redis_service.get_latest_price(symbol)
        if price_data:
            return price_data

        price_data = await self._fetch_price_from_yahoo(symbol)
        if price_data:
            await self.redis_service.cache_price(symbol, price_data["price"])
        return price_data

    async def create_polling_job(self, symbol: str, interval: int) -> bool:
        """
        Create a new polling job to fetch market data periodically.

        Args:
            symbol: Stock symbol to poll
            interval: Polling interval in seconds

        Returns:
            True if job created successfully
        """
        try:
            job_status = {
                "symbol": symbol,
                "interval": interval,
                "status": "active",
                "created_at": datetime.now(UTC).isoformat(),
            }
            await self.redis_service.store_job_status(symbol, job_status)
            return True
        except Exception as e:
            logger.error(f"Failed to create polling job for {symbol}: {e}")
            return False

    async def get_job_status(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a polling job.

        Args:
            symbol: Stock symbol

        Returns:
            Dictionary with job status or None if not found
        """
        return await self.redis_service.get_job_status(symbol)

    async def delete_job(self, symbol: str) -> bool:
        """
        Delete a polling job.

        Args:
            symbol: Stock symbol

        Returns:
            True if deleted, False if not found or error occurs
        """
        try:
            await self.redis_service.delete_job(symbol)
            return True
        except Exception as e:
            logger.error(f"Failed to delete job for {symbol}: {e}")
            return False

    @staticmethod
    def add_price(
        db, symbol: str, price: float, volume: int = 1000, source: str = "test_source"
    ) -> None:
        """
        Add a price record to the database.

        Args:
            db: Database session
            symbol: Stock symbol
            price: Price value
            volume: Volume value (default 1000)
            source: Source value (default 'test_source')
        """
        market_data = MarketData(
            symbol=symbol,
            price=price,
            volume=volume,
            source=source,
            timestamp=datetime.now(UTC),
        )
        db.add(market_data)
        db.commit()

    async def _fetch_price_from_yahoo(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch price data from Yahoo Finance API.

        Args:
            symbol: Stock symbol

        Returns:
            Dictionary with price data or None
        """
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            result = data.get("chart", {}).get("result", [])
            if not result:
                return None
            meta = result[0].get("meta", {})
            price = meta.get("regularMarketPrice")
            if price is None:
                return None
            price_data = {
                "symbol": symbol,
                "price": price,
                "timestamp": datetime.now(UTC).isoformat(),
            }
            await self.redis_service.cache_price(symbol, price_data["price"])
            return price_data
        except requests.RequestException as e:
            logger.error(f"Failed to fetch data for {symbol}: {e}")
            return None

    async def list_active_jobs(self) -> List[dict]:
        """List all active jobs from Redis."""
        try:
            jobs = await self.redis_service.list_jobs()
            return jobs
        except Exception as e:
            logger.error(f"Failed to list active jobs: {e}")
            return []

    async def delete_all_jobs(self) -> int:
        """
        Delete all polling jobs.

        Returns:
            Number of jobs deleted
        """
        try:
            jobs = await self.redis_service.list_jobs()
            deleted_count = 0
            for job in jobs:
                symbol = job.get("symbol")
                if symbol:
                    await self.redis_service.delete_job(symbol)
                deleted_count += 1
            return deleted_count
        except Exception as e:
            logger.error(f"Failed to delete all jobs: {e}")
            return 0

    @staticmethod
    def get_market_data_by_id(db: Session, market_data_id: int) -> Optional[MarketData]:
        """
        Get a market data record by its ID.

        Args:
            db: Database session
            market_data_id: ID of the market data record

        Returns:
            MarketData object or None if not found
        """
        return db.query(MarketData).filter(MarketData.id == market_data_id).first()
