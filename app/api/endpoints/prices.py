"""Price endpoints for the Market Data Service."""

import logging
from datetime import datetime
from threading import Lock
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from prometheus_client import Counter, Gauge
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import (
    require_admin_permission,
    require_read_permission,
    require_write_permission,
)
from app.db.session import get_db
from app.schemas.market_data import (
    MarketDataCreate,
    MarketDataInDB,
    MarketDataUpdate,
    SymbolsResponse,
)
from app.services.market_data import MarketDataService

router = APIRouter()

# In-memory polling job store and lock
polling_jobs = {}
job_counter = [0]
jobs_lock = Lock()

# Prometheus metrics
market_data_points_total = Counter(
    "market_data_points_total", "Total number of market data points"
)
symbols_tracked = Gauge("symbols_tracked", "Number of symbols being tracked")
polling_jobs_active = Gauge("polling_jobs_active", "Number of active polling jobs")

logger = logging.getLogger(__name__)


class PollingJobConfig(BaseModel):
    """Configuration for a polling job."""

    symbols: List[str]
    interval: int


@router.get("/", response_model=List[MarketDataInDB])
async def get_market_data(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    symbol: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: str = Depends(require_read_permission),
) -> List[MarketDataInDB]:
    """
    Get market data with optional filtering.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        symbol: Filter by symbol
        db: Database session
        current_user: Authenticated user

    Returns:
        List of market data records
    """
    try:
        if symbol:
            return MarketDataService.get_market_data_by_symbol(db, symbol, skip, limit)
        return MarketDataService.get_market_data(db, skip, limit)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving market data: {str(e)}",
        )


@router.post("/", response_model=MarketDataInDB, status_code=201)
async def create_market_data(
    market_data: MarketDataCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(require_write_permission),
) -> MarketDataInDB:
    """Create new market data."""
    try:
        result = MarketDataService.create_market_data(db, market_data)

        # Increment metrics
        market_data_points_total.inc()
        symbols_tracked.set(len(MarketDataService.get_all_symbols(db)))

        return result
    except HTTPException as e:
        if e.status_code == 422:
            raise
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating market data: {str(e)}",
        )


# Polling job endpoints (require admin permissions) - must be before parameterized routes
@router.post("/poll", status_code=201)
async def create_polling_job(
    config: PollingJobConfig = Body(...),
    current_user: str = Depends(require_admin_permission),
) -> dict:
    """
    Create a new polling job.

    Args:
        config: Polling job configuration
        current_user: Authenticated user with admin permissions

    Returns:
        Job information
    """
    with jobs_lock:
        job_id = str(job_counter[0] + 1)
        job_counter[0] += 1

        polling_jobs[job_id] = {
            "id": job_id,
            "config": config.dict(),
            "status": "created",
            "created_at": datetime.now().isoformat(),
        }

        polling_jobs_active.set(len(polling_jobs))

    return {
        "job_id": job_id,
        "status": "created",
        "config": config.dict(),
    }


@router.get("/poll")
async def list_polling_jobs(
    current_user: str = Depends(require_admin_permission),
) -> List[dict]:
    """
    List all polling jobs.

    Args:
        current_user: Authenticated user with admin permissions

    Returns:
        List of polling jobs
    """
    return list(polling_jobs.values())


@router.get("/poll/{job_id}")
async def get_polling_job(
    job_id: str, current_user: str = Depends(require_admin_permission)
) -> dict:
    """
    Get polling job status.

    Args:
        job_id: Job ID
        current_user: Authenticated user with admin permissions

    Returns:
        Job status
    """
    if job_id not in polling_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return polling_jobs[job_id]


@router.delete("/poll/{job_id}")
async def delete_polling_job(
    job_id: str, current_user: str = Depends(require_admin_permission)
) -> dict:
    """
    Delete a polling job.

    Args:
        job_id: Job ID
        current_user: Authenticated user with admin permissions

    Returns:
        Success message
    """
    with jobs_lock:
        if job_id not in polling_jobs:
            raise HTTPException(status_code=404, detail="Job not found")

        del polling_jobs[job_id]
        polling_jobs_active.set(len(polling_jobs))

    return {"message": "Job deleted successfully"}


@router.post("/delete-all-polling-jobs")
async def delete_all_polling_jobs(
    current_user: str = Depends(require_admin_permission),
) -> dict:
    """
    Delete all polling jobs.

    Args:
        current_user: Authenticated user with admin permissions

    Returns:
        Success message
    """
    with jobs_lock:
        polling_jobs.clear()
        polling_jobs_active.set(0)

    return {"message": "All jobs deleted successfully"}


@router.put("/{market_data_id}", response_model=MarketDataInDB)
async def update_market_data(
    market_data_id: int,
    market_data: MarketDataUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(require_write_permission),
) -> MarketDataInDB:
    """
    Update market data.

    Args:
        market_data_id: ID of market data to update
        market_data: Updated market data
        db: Database session
        current_user: Authenticated user

    Returns:
        Updated market data record
    """
    try:
        result = MarketDataService.update_market_data(db, market_data_id, market_data)
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Market data with id {market_data_id} not found",
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating market data: {str(e)}",
        )


@router.delete("/{market_data_id}", status_code=200)
async def delete_market_data(
    market_data_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(require_admin_permission),
) -> dict:
    """
    Delete market data.

    Args:
        market_data_id: ID of market data to delete
        db: Database session
        current_user: Authenticated user with admin permissions

    Returns:
        Success message
    """
    try:
        if not MarketDataService.delete_market_data(db, market_data_id):
            raise HTTPException(
                status_code=404,
                detail=f"Market data with id {market_data_id} not found",
            )
        return {"message": "Market data deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting market data: {str(e)}",
        )


@router.get("/latest")
async def get_latest_price(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(require_read_permission),
):
    """
    Get the latest price for a symbol.

    Args:
        symbol: The symbol to get the latest price for
        db: Database session
        current_user: Authenticated user

    Returns:
        Latest price data for the symbol
    """
    try:
        latest = MarketDataService.get_latest_market_data(db, symbol)
        if not latest:
            raise HTTPException(
                status_code=404, detail=f"No data found for symbol {symbol}"
            )
        return {
            "symbol": latest.symbol,
            "price": latest.price,
            "timestamp": latest.timestamp,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving latest price: {str(e)}",
        )


@router.get("/symbols", response_model=SymbolsResponse)
async def get_symbols(
    db: Session = Depends(get_db), current_user: str = Depends(require_read_permission)
):
    """Get all unique symbols from market data."""
    try:
        symbols = MarketDataService.get_all_symbols(db)
        return {"symbols": symbols}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving symbols: {str(e)}"
        )


@router.get("/{market_data_id}", response_model=MarketDataInDB)
async def get_market_data_by_id(
    market_data_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(require_read_permission),
) -> MarketDataInDB:
    """
    Get a market data record by its ID.

    Args:
        market_data_id: ID of the market data record
        db: Database session
        current_user: Authenticated user

    Returns:
        Market data record
    """
    try:
        record = MarketDataService.get_market_data_by_id(db, market_data_id)
        if not record:
            raise HTTPException(
                status_code=404,
                detail=f"Market data with id {market_data_id} not found",
            )
        return record
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving market data by id: {str(e)}",
        )


@router.get("/{symbol}/moving-average", response_model=dict)
async def get_moving_average(
    symbol: str,
    window: int = Query(5, ge=1),
    db: Session = Depends(get_db),
    current_user: str = Depends(require_read_permission),
):
    """Calculate moving average for a symbol."""
    logger.info(f"Calculating moving average for {symbol} with window {window}")
    try:
        result = MarketDataService.calculate_moving_average(db, symbol, window)
        logger.info(f"Result from calculate_moving_average: {result}")
        if result is None:
            logger.warning(f"No data for moving average: {symbol}, window={window}")
            raise HTTPException(
                status_code=404,
                detail=f"Insufficient data for moving average calculation for symbol {symbol}",
            )
        return {
            "symbol": symbol,
            "value": result,
            "window_size": window,
            "timestamp": datetime.now().isoformat(),
        }
    except HTTPException:
        logger.exception("HTTPException raised in moving average endpoint")
        raise
    except Exception as e:
        logger.exception("Unexpected error in moving average endpoint")
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating moving average: {str(e)}",
        )
