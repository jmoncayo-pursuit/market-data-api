"""Tests for database models and schemas."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models.market_data import MarketData
from app.schemas.market_data import (
    DeleteAllResponse,
    ErrorResponse,
    MarketDataCreate,
    MarketDataInDB,
    MarketDataUpdate,
    MovingAverageResponse,
    PollingRequest,
    PollingResponse,
    PriceResponse,
    SymbolsResponse,
)


class TestMarketDataModel:
    """Test cases for MarketData model."""

    def test_market_data_model_creation(self):
        """Test market data model creation."""
        market_data = MarketData(
            symbol="AAPL",
            price=150.0,
            volume=1000,
            source="test_source",
            raw_data="test_data",
            timestamp=datetime.now(),
        )
        assert market_data.symbol == "AAPL"
        assert market_data.price == 150.0
        assert market_data.volume == 1000
        assert market_data.source == "test_source"
        assert market_data.raw_data == "test_data"
        assert market_data.timestamp is not None

    def test_market_data_model_defaults(self):
        """Test market data model with default values."""
        market_data = MarketData(
            symbol="AAPL",
            price=150.0,
            volume=0,
            source="test_source",
            raw_data="test_data",
            timestamp=datetime.now(),
        )
        assert market_data.volume == 0
        assert market_data.timestamp is not None

    def test_market_data_model_repr(self):
        """Test market data model string representation."""
        market_data = MarketData(
            symbol="AAPL",
            price=150.0,
            volume=1000,
            source="test_source",
            raw_data="test_data",
        )

        repr_str = repr(market_data)
        assert "MarketData" in repr_str
        assert "AAPL" in repr_str
        assert "150.0" in repr_str

    def test_market_data_model_str(self):
        """Test MarketData model string conversion."""
        market_data = MarketData(id=1, symbol="AAPL", price=150.0)

        str_repr = str(market_data)
        assert "MarketData" in str_repr
        assert "AAPL" in str_repr

    def test_market_data_model_equality(self):
        """Test market data model equality."""
        market_data1 = MarketData(
            symbol="AAPL",
            price=150.0,
            volume=1000,
            source="test_source",
            raw_data="test_data",
        )
        market_data2 = MarketData(
            symbol="AAPL",
            price=150.0,
            volume=1000,
            source="test_source",
            raw_data="test_data",
        )

        assert market_data1.symbol == market_data2.symbol
        assert market_data1.price == market_data2.price
        assert market_data1.volume == market_data2.volume

    def test_market_data_model_inequality(self):
        """Test MarketData model inequality."""
        market_data1 = MarketData(id=1, symbol="AAPL", price=150.0)

        market_data2 = MarketData(id=2, symbol="GOOGL", price=2500.0)

        assert market_data1 != market_data2

    def test_market_data_model_hash(self):
        """Test MarketData model hash."""
        market_data = MarketData(id=1, symbol="AAPL", price=150.0)

        # Should be hashable
        hash_value = hash(market_data)
        assert isinstance(hash_value, int)

    def test_market_data_model_table_name(self):
        """Test MarketData model table name."""
        assert MarketData.__tablename__ == "market_data"

    def test_market_data_model_columns(self):
        """Test MarketData model columns."""
        columns = MarketData.__table__.columns

        assert "id" in columns
        assert "symbol" in columns
        assert "price" in columns
        assert "volume" in columns
        assert "timestamp" in columns

    def test_market_data_model_primary_key(self):
        """Test MarketData model primary key."""
        primary_key = MarketData.__table__.primary_key
        assert len(primary_key.columns) == 1
        assert "id" in primary_key.columns

    def test_market_data_model_indexes(self):
        """Test MarketData model indexes."""
        indexes = MarketData.__table__.indexes
        # Check if there are any indexes defined
        assert isinstance(indexes, set)

    def test_market_data_model_foreign_keys(self):
        """Test MarketData model foreign keys."""
        foreign_keys = MarketData.__table__.foreign_keys
        # MarketData should not have foreign keys
        assert len(foreign_keys) == 0

    def test_market_data_model_metadata(self):
        """Test MarketData model metadata."""
        assert MarketData.__table__.metadata is not None

    def test_market_data_model_schema(self):
        """Test MarketData model schema."""
        # Test that the model can be serialized
        market_data = MarketData(
            id=1, symbol="AAPL", price=150.0, volume=1000, timestamp=datetime.now()
        )

        # Should be able to access all attributes
        assert hasattr(market_data, "id")
        assert hasattr(market_data, "symbol")
        assert hasattr(market_data, "price")
        assert hasattr(market_data, "volume")
        assert hasattr(market_data, "timestamp")

    def test_market_data_model_validation(self):
        """Test MarketData model validation."""
        # Test with valid data
        market_data = MarketData(symbol="AAPL", price=150.0, volume=1000)
        assert market_data is not None

    def test_market_data_model_invalid_data(self):
        """Test market data model with invalid data."""
        # Test with negative price - this should raise ValidationError from Pydantic
        with pytest.raises(ValidationError):
            MarketDataCreate(
                symbol="AAPL",
                price=-150.0,
                volume=1000,
                source="test_source",
                raw_data="test_data",
            )

    def test_market_data_model_edge_cases(self):
        """Test MarketData model edge cases."""
        # Test with zero price - this should be valid
        market_data = MarketData(
            symbol="AAPL", price=0.0, volume=1, source="test", raw_data="test"
        )
        assert market_data.price == 0.0

        # Test with very large price
        market_data = MarketData(
            symbol="AAPL", price=999999.99, volume=1, source="test", raw_data="test"
        )
        assert market_data.price == 999999.99

        # Test with empty symbol
        market_data = MarketData(
            symbol="", price=150.0, volume=1, source="test", raw_data="test"
        )
        assert market_data.symbol == ""

    def test_market_data_model_timestamp_handling(self):
        """Test market data model timestamp handling."""
        timestamp = datetime.now()
        market_data = MarketData(
            symbol="AAPL",
            price=150.0,
            volume=1000,
            source="test_source",
            raw_data="test_data",
            timestamp=timestamp,
        )

        assert market_data.timestamp == timestamp

    def test_market_data_model_volume_handling(self):
        """Test market data model volume handling."""
        # Test with zero volume - this should raise ValidationError from Pydantic
        with pytest.raises(ValidationError):
            MarketDataCreate(
                symbol="AAPL",
                price=150.0,
                volume=0,
                source="test_source",
                raw_data="test_data",
            )


class TestMarketDataSchemas:
    """Test cases for market data schemas."""

    def test_market_data_create_schema(self):
        """Test market data create schema."""
        data = {
            "symbol": "AAPL",
            "price": 150.0,
            "volume": 1000,
            "source": "test_source",
            "raw_data": "test_data",
        }
        schema = MarketDataCreate(**data)

        assert schema.symbol == "AAPL"
        assert schema.price == 150.0
        assert schema.volume == 1000
        assert schema.source == "test_source"
        assert schema.raw_data == "test_data"

    def test_market_data_create_schema_defaults(self):
        """Test market data create schema with defaults."""
        data = {"symbol": "AAPL", "price": 150.0, "volume": 1, "source": "test_source"}
        schema = MarketDataCreate(**data)

        assert schema.symbol == "AAPL"
        assert schema.price == 150.0
        assert schema.volume == 1
        assert schema.source == "test_source"
        assert schema.raw_data is None

    def test_market_data_create_schema_edge_cases(self):
        """Test market data create schema edge cases."""
        # Test with zero price
        schema = MarketDataCreate(
            symbol="AAPL", price=0.0, volume=1, source="test_source"
        )
        assert schema.price == 0.0

        # Test with very large price
        schema = MarketDataCreate(
            symbol="AAPL", price=999999.99, volume=1000000, source="test_source"
        )
        assert schema.price == 999999.99

    def test_market_data_update_schema(self):
        """Test market data update schema."""
        data = {"price": 160.0, "volume": 2000}
        schema = MarketDataUpdate(**data)

        assert schema.price == 160.0
        assert schema.volume == 2000
        assert schema.symbol is None

    def test_market_data_update_schema_validation(self):
        """Test market data update schema validation."""
        # Test valid data
        valid_data = {
            "symbol": "AAPL",
            "price": 150.0,
            "volume": 1000,
            "source": "test",
        }
        schema = MarketDataUpdate(**valid_data)
        assert schema.symbol == "AAPL"
        assert schema.price == 150.0

        # Test with negative price - should work since MarketDataUpdate doesn't have ge=0 constraint
        schema = MarketDataUpdate(price=-100.0)
        assert schema.price == -100.0

        # Test with zero volume - should work since MarketDataUpdate doesn't have gt=0 constraint
        schema = MarketDataUpdate(volume=0)
        assert schema.volume == 0

    def test_market_data_in_db_schema(self):
        """Test market data in DB schema."""
        timestamp = datetime.now()
        data = {
            "id": 1,
            "symbol": "AAPL",
            "price": 150.0,
            "volume": 1000,
            "timestamp": timestamp,
            "source": "test_source",
            "raw_data": "test_data",
        }
        schema = MarketDataInDB(**data)

        assert schema.id == 1
        assert schema.symbol == "AAPL"
        assert schema.price == 150.0
        assert schema.volume == 1000
        assert schema.timestamp == timestamp

    def test_moving_average_response_schema(self):
        """Test moving average response schema."""
        timestamp = datetime.now()
        data = {
            "symbol": "AAPL",
            "moving_average": 155.5,
            "timestamp": timestamp,
            "window_size": 10,
        }
        schema = MovingAverageResponse(**data)

        assert schema.symbol == "AAPL"
        assert schema.moving_average == 155.5
        assert schema.timestamp == timestamp
        assert schema.window_size == 10

    def test_price_response_schema(self):
        """Test price response schema."""
        data = {
            "symbol": "AAPL",
            "price": 150.0,
            "timestamp": "2023-01-01T00:00:00",
            "provider": "test_provider",
        }
        schema = PriceResponse(**data)

        assert schema.symbol == "AAPL"
        assert schema.price == 150.0
        assert schema.timestamp == "2023-01-01T00:00:00"
        assert schema.provider == "test_provider"

    def test_polling_request_schema(self):
        """Test polling request schema."""
        data = {"symbols": ["AAPL", "GOOGL"], "interval": 60}
        schema = PollingRequest(**data)

        assert schema.symbols == ["AAPL", "GOOGL"]
        assert schema.interval == 60

    def test_polling_response_schema(self):
        """Test polling response schema."""
        data = {
            "job_id": "test_job_123",
            "status": "active",
            "config": {"symbols": ["AAPL", "GOOGL"], "interval": 60},
        }
        schema = PollingResponse(**data)

        assert schema.job_id == "test_job_123"
        assert schema.status == "active"
        assert schema.config.symbols == ["AAPL", "GOOGL"]

    def test_error_response_schema(self):
        """Test error response schema."""
        data = {"detail": "An error occurred"}
        schema = ErrorResponse(**data)

        assert schema.detail == "An error occurred"

    def test_delete_all_response_schema(self):
        """Test delete all response schema."""
        data = {"message": "All data deleted", "deleted_count": 100}
        schema = DeleteAllResponse(**data)

        assert schema.message == "All data deleted"
        assert schema.deleted_count == 100

    def test_symbols_response_schema(self):
        """Test symbols response schema."""
        data = {"symbols": ["AAPL", "GOOGL", "MSFT"]}
        schema = SymbolsResponse(**data)

        assert schema.symbols == ["AAPL", "GOOGL", "MSFT"]

    def test_schema_field_constraints(self):
        """Test schema field constraints."""
        # Test valid constraints
        valid_data = {
            "symbol": "AAPL",
            "price": 150.0,
            "volume": 1000,
            "source": "test",
        }
        schema = MarketDataCreate(**valid_data)
        assert schema.symbol == "AAPL"
        assert schema.price == 150.0
        assert schema.volume == 1000

        # Test invalid price constraint
        with pytest.raises(ValidationError):
            MarketDataCreate(price=-50.0)

        # Test invalid volume constraint
        with pytest.raises(ValidationError):
            MarketDataCreate(volume=0)

    def test_schema_optional_fields(self):
        """Test schema optional fields."""
        # Test MarketDataUpdate with optional fields
        update_schema = MarketDataUpdate()
        assert update_schema.price is None
        assert update_schema.volume is None

        # Test MarketDataCreate with optional raw_data
        create_schema = MarketDataCreate(
            symbol="AAPL", price=150.0, volume=1000, source="test_source"
        )
        assert create_schema.raw_data is None  # Default value

    def test_schema_required_fields(self):
        """Test schema required fields."""
        # Test MarketDataCreate required fields
        with pytest.raises(ValidationError):
            MarketDataCreate()  # Missing symbol, price, volume, and source

        with pytest.raises(ValidationError):
            MarketDataCreate(symbol="AAPL")  # Missing price, volume, and source

        with pytest.raises(ValidationError):
            MarketDataCreate(price=150.0)  # Missing symbol, volume, and source

        # Test MarketDataInDB required fields
        with pytest.raises(ValidationError):
            MarketDataInDB()  # Missing all required fields
