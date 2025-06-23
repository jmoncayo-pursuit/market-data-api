"""Tests for Market Data service."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
import requests
from sqlalchemy.orm import Session

from app.models.market_data import MarketData
from app.schemas.market_data import MarketDataCreate, MarketDataUpdate
from app.services.market_data import MarketDataService, retry_on_failure


class TestMarketDataService:
    """Test cases for MarketDataService."""

    def test_init(self):
        """Test service initialization."""
        mock_db = Mock(spec=Session)
        service = MarketDataService(mock_db)

        assert service.db == mock_db
        assert service.redis_service is not None

    def test_get_market_data(self):
        """Test getting market data with pagination."""
        mock_db = Mock(spec=Session)
        mock_data = [Mock(spec=MarketData), Mock(spec=MarketData)]
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_data

        result = MarketDataService.get_market_data(mock_db, skip=10, limit=5)

        assert result == mock_data
        mock_query.offset.assert_called_once_with(10)
        mock_query.limit.assert_called_once_with(5)

    def test_get_market_data_by_symbol(self):
        """Test getting market data for specific symbol."""
        mock_db = Mock(spec=Session)
        mock_data = [Mock(spec=MarketData)]
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_data

        result = MarketDataService.get_market_data_by_symbol(
            mock_db, "AAPL", skip=5, limit=10
        )

        assert result == mock_data
        mock_query.filter.assert_called_once()

    def test_create_market_data(self):
        """Test creating market data."""
        mock_db = Mock(spec=Session)
        market_data_create = MarketDataCreate(
            symbol="AAPL",
            price=150.0,
            volume=1000,
            source="test_source",
            timestamp=datetime.now(),
        )

        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        result = MarketDataService.create_market_data(mock_db, market_data_create)

        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_update_market_data_success(self):
        """Test successful market data update."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = Mock(spec=MarketData)

        market_data_update = MarketDataUpdate(price=160.0)

        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        result = MarketDataService.update_market_data(mock_db, 1, market_data_update)

        assert result is not None
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_update_market_data_not_found(self):
        """Test market data update when record not found."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        market_data_update = MarketDataUpdate(price=160.0)

        result = MarketDataService.update_market_data(mock_db, 1, market_data_update)

        assert result is None

    def test_delete_market_data_success(self):
        """Test successful market data deletion."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_market_data = Mock(spec=MarketData)
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_market_data

        mock_db.delete = Mock()
        mock_db.commit = Mock()

        result = MarketDataService.delete_market_data(mock_db, 1)

        assert result is True
        mock_db.delete.assert_called_once_with(mock_market_data)
        mock_db.commit.assert_called_once()

    def test_delete_market_data_not_found(self):
        """Test market data deletion when record not found."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = MarketDataService.delete_market_data(mock_db, 1)

        assert result is False

    def test_get_latest_market_data(self):
        """Test getting latest market data for symbol."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = Mock(spec=MarketData)

        result = MarketDataService.get_latest_market_data(mock_db, "AAPL")

        assert result is not None

    def test_get_all_symbols(self):
        """Test getting all unique symbols."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.all.return_value = [("AAPL",), ("GOOGL",)]

        result = MarketDataService.get_all_symbols(mock_db)

        assert result == ["AAPL", "GOOGL"]

    def test_calculate_moving_average_success(self):
        """Test successful moving average calculation."""
        mock_db = Mock(spec=Session)
        mock_records = [
            Mock(spec=MarketData, price=100.0),
            Mock(spec=MarketData, price=110.0),
            Mock(spec=MarketData, price=120.0),
        ]
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_records

        result = MarketDataService.calculate_moving_average(mock_db, "AAPL", 3)

        assert result == 110.0

    def test_calculate_moving_average_insufficient_data(self):
        """Test moving average calculation with insufficient data."""
        mock_db = Mock(spec=Session)
        mock_records = [Mock(spec=MarketData, price=100.0)]
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_records

        result = MarketDataService.calculate_moving_average(mock_db, "AAPL", 3)

        assert result is None

    def test_get_latest_timestamp(self):
        """Test getting latest timestamp for symbol."""
        mock_db = Mock(spec=Session)
        mock_timestamp = datetime.now()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = (mock_timestamp,)

        result = MarketDataService.get_latest_timestamp(mock_db, "AAPL")

        assert result == mock_timestamp

    @pytest.mark.asyncio
    async def test_get_latest_price_success(self):
        """Test successful price retrieval."""
        with patch(
            "app.services.market_data.MarketDataService._fetch_price_from_yahoo"
        ) as mock_fetch:
            mock_fetch.return_value = {
                "symbol": "AAPL",
                "price": 150.0,
                "timestamp": "2025-06-20T21:12:20.546796",
            }
            mock_db = Mock(spec=Session)
            service = MarketDataService(mock_db)
            result = await service.get_latest_price("AAPL")
            assert result["symbol"] == "AAPL"
            assert result["price"] == 150.0

    @pytest.mark.asyncio
    async def test_get_latest_price_redis_failure(self):
        """Test price retrieval with Redis failure."""
        with patch(
            "app.services.market_data.MarketDataService._fetch_price_from_yahoo"
        ) as mock_fetch, patch(
            "app.services.redis_service.RedisService.get_latest_price",
            return_value=None,
        ):
            mock_fetch.return_value = None
            mock_db = Mock(spec=Session)
            service = MarketDataService(mock_db)
            result = await service.get_latest_price("AAPL")
            assert result is None

    @pytest.mark.asyncio
    async def test_create_polling_job_success(self):
        """Test successful job creation."""
        with patch(
            "app.services.market_data.MarketDataService.create_polling_job"
        ) as mock_create:
            mock_create.return_value = True
            mock_db = Mock(spec=Session)
            service = MarketDataService(mock_db)
            result = await service.create_polling_job("AAPL", 60)
            assert result is True

    @pytest.mark.asyncio
    async def test_get_job_status_success(self):
        """Test successful job status retrieval."""
        with patch(
            "app.services.market_data.MarketDataService.get_job_status"
        ) as mock_status:
            mock_status.return_value = {"status": "running"}
            mock_db = Mock(spec=Session)
            service = MarketDataService(mock_db)
            result = await service.get_job_status("AAPL")
            assert result["status"] == "running"

    @pytest.mark.asyncio
    async def test_get_job_status_not_found(self):
        """Test job status retrieval for non-existent job."""
        with patch(
            "app.services.market_data.MarketDataService.get_job_status"
        ) as mock_status:
            mock_status.return_value = None
            mock_db = Mock(spec=Session)
            service = MarketDataService(mock_db)
            result = await service.get_job_status("AAPL")
            assert result is None

    @pytest.mark.asyncio
    async def test_delete_job_success(self):
        """Test successful job deletion."""
        with patch(
            "app.services.market_data.MarketDataService.delete_job"
        ) as mock_delete:
            mock_delete.return_value = True
            mock_db = Mock(spec=Session)
            service = MarketDataService(mock_db)
            result = await service.delete_job("AAPL")
            assert result is True

    @pytest.mark.asyncio
    async def test_delete_job_failure(self):
        """Test job deletion failure."""
        with patch(
            "app.services.market_data.MarketDataService.delete_job"
        ) as mock_delete:
            mock_delete.return_value = False
            mock_db = Mock(spec=Session)
            service = MarketDataService(mock_db)
            result = await service.delete_job("AAPL")
            assert result is False

    @pytest.mark.asyncio
    async def test_fetch_price_from_yahoo_success(self):
        """Test successful price fetching from Yahoo."""
        with patch(
            "app.services.market_data.MarketDataService._fetch_price_from_yahoo"
        ) as mock_fetch:
            mock_fetch.return_value = {"price": 150.0, "volume": 1000}
            mock_db = Mock(spec=Session)
            service = MarketDataService(mock_db)
            result = await service._fetch_price_from_yahoo("AAPL")
            assert result["price"] == 150.0
            assert result["volume"] == 1000

    @pytest.mark.asyncio
    async def test_fetch_price_from_yahoo_no_data(self):
        """Test price fetching with no data."""
        with patch(
            "app.services.market_data.MarketDataService._fetch_price_from_yahoo"
        ) as mock_fetch:
            mock_fetch.return_value = None
            mock_db = Mock(spec=Session)
            service = MarketDataService(mock_db)
            result = await service._fetch_price_from_yahoo("AAPL")
            assert result is None

    @pytest.mark.asyncio
    async def test_fetch_price_from_yahoo_exception(self):
        """Test price fetching with exception."""
        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.RequestException("API error")
            mock_db = Mock(spec=Session)
            service = MarketDataService(mock_db)
            result = await service._fetch_price_from_yahoo("AAPL")
            assert result is None

    @pytest.mark.asyncio
    async def test_list_active_jobs_success(self):
        """Test successful active jobs listing."""
        with patch(
            "app.services.market_data.MarketDataService.list_active_jobs"
        ) as mock_list:
            mock_list.return_value = [{"job_id": "job1"}, {"job_id": "job2"}]
            mock_db = Mock(spec=Session)
            service = MarketDataService(mock_db)
            result = await service.list_active_jobs()
            assert len(result) == 2
            assert result[0]["job_id"] == "job1"
            assert result[1]["job_id"] == "job2"

    @pytest.mark.asyncio
    async def test_list_active_jobs_empty(self):
        """Test empty active jobs listing."""
        with patch(
            "app.services.market_data.MarketDataService.list_active_jobs"
        ) as mock_list:
            mock_list.return_value = []
            mock_db = Mock(spec=Session)
            service = MarketDataService(mock_db)
            result = await service.list_active_jobs()
            assert result == []

    @pytest.mark.asyncio
    async def test_delete_all_jobs_success(self):
        """Test successful deletion of all jobs."""
        with patch(
            "app.services.market_data.MarketDataService.delete_all_jobs"
        ) as mock_delete:
            mock_delete.return_value = 5
            mock_db = Mock(spec=Session)
            service = MarketDataService(mock_db)
            result = await service.delete_all_jobs()
            assert result == 5

    @pytest.mark.asyncio
    async def test_delete_all_jobs_empty(self):
        """Test deletion of all jobs when none exist."""
        with patch(
            "app.services.market_data.MarketDataService.delete_all_jobs"
        ) as mock_delete:
            mock_delete.return_value = 0
            mock_db = Mock(spec=Session)
            service = MarketDataService(mock_db)
            result = await service.delete_all_jobs()
            assert result == 0


class TestRetryDecorator:
    """Test cases for retry_on_failure decorator."""

    @pytest.mark.asyncio
    async def test_retry_success_first_attempt(self):
        """Test retry decorator with success on first attempt."""

        @retry_on_failure(max_retries=3, delay=0.01)
        async def test_func():
            return "success"

        result = await test_func()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self):
        """Test retry decorator with success after some failures."""
        attempt_count = 0

        @retry_on_failure(max_retries=3, delay=0.01)
        async def test_func():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise Exception("Temporary failure")
            return "success"

        result = await test_func()
        assert result == "success"
        assert attempt_count == 3

    @pytest.mark.asyncio
    async def test_retry_max_attempts_exceeded(self):
        """Test retry decorator with max attempts exceeded."""

        @retry_on_failure(max_retries=2, delay=0.01)
        async def test_func():
            raise Exception("Persistent failure")

        with pytest.raises(Exception, match="Persistent failure"):
            await test_func()
