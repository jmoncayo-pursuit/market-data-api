"""Market data schemas for the Market Data Service."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PriceResponse(BaseModel):
    """Response model for price data."""

    model_config = ConfigDict(from_attributes=True)
    symbol: str
    price: float
    timestamp: str
    provider: str


class PollingRequest(BaseModel):
    """Polling request model."""

    model_config = ConfigDict(from_attributes=True)
    symbols: List[str]
    interval: int


class PollingJobConfig(BaseModel):
    """Polling job configuration model."""

    model_config = ConfigDict(from_attributes=True)
    symbols: List[str]
    interval: int
    job_id: Optional[str] = None
    status: Optional[str] = None


class PollingResponse(BaseModel):
    """Polling response model."""

    model_config = ConfigDict(from_attributes=True)
    job_id: str
    status: str
    config: PollingRequest


class MovingAverageResponse(BaseModel):
    """Response model for moving average calculations."""

    model_config = ConfigDict(from_attributes=True)
    symbol: str
    moving_average: float
    timestamp: datetime
    window_size: int


class ErrorResponse(BaseModel):
    """Response model for error messages."""

    model_config = ConfigDict(from_attributes=True)
    detail: str


class PollingJobList(BaseModel):
    """List of polling jobs."""

    model_config = ConfigDict(from_attributes=True)
    jobs: List[PollingResponse]


class DeleteAllResponse(BaseModel):
    """Response model for delete all operation."""

    model_config = ConfigDict(from_attributes=True)
    message: str
    deleted_count: int


class MarketDataBase(BaseModel):
    """Base schema for market data."""

    symbol: str = Field(..., min_length=1, description="Stock symbol")
    price: float = Field(..., ge=0, description="Stock price")
    volume: int = Field(..., gt=0, description="Trading volume")
    source: str = Field(..., description="Data source")
    raw_data: Optional[str] = Field(None, description="Raw market data")


class MarketDataCreate(MarketDataBase):
    """Schema for creating market data."""


class MarketDataUpdate(BaseModel):
    """Schema for updating market data."""

    symbol: Optional[str] = Field(None, description="Stock symbol")
    price: Optional[float] = Field(None, description="Stock price")
    volume: Optional[int] = Field(None, description="Trading volume")
    source: Optional[str] = Field(None, description="Data source")
    raw_data: Optional[str] = Field(None, description="Raw market data")


class MarketDataInDB(MarketDataBase):
    """Schema for market data in database."""

    id: int = Field(..., description="Market data ID")
    timestamp: datetime = Field(..., description="Timestamp of the data")

    class Config:
        """Pydantic model configuration."""

        orm_mode = True


class RawMarketDataBase(BaseModel):
    """Base schema for raw market data."""

    symbol: str = Field(..., description="Stock symbol")
    raw_data: str = Field(..., description="Raw market data")
    source: str = Field(..., description="Data source")


class RawMarketDataCreate(RawMarketDataBase):
    """Schema for creating raw market data."""


class RawMarketDataInDB(RawMarketDataBase):
    """Schema for raw market data in database."""

    id: int = Field(..., description="Raw market data ID")
    timestamp: datetime = Field(..., description="Timestamp of the data")
    processed: int = Field(..., description="Processing status")

    class Config:
        """Pydantic model configuration."""

        orm_mode = True


class ProcessedPriceBase(BaseModel):
    """Base schema for processed price."""

    symbol: str = Field(..., description="Stock symbol")
    price: float = Field(..., description="Processed price")
    raw_data_id: int = Field(..., description="Raw market data ID")


class ProcessedPriceCreate(ProcessedPriceBase):
    """Schema for creating processed price."""


class ProcessedPriceInDB(ProcessedPriceBase):
    """Schema for processed price in database."""

    id: int = Field(..., description="Processed price ID")
    timestamp: datetime = Field(..., description="Timestamp of the data")

    class Config:
        """Pydantic model configuration."""

        orm_mode = True


class SymbolsResponse(BaseModel):
    """Response model for symbols endpoint."""

    symbols: List[str]
