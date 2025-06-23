"""Main application module."""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import Response, JSONResponse
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import DataError, IntegrityError

from app.api.endpoints import prices
from app.core.audit import setup_audit_logging
from app.core.auth import require_read_permission, require_write_permission
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.rate_limit import init_rate_limiter, rate_limit_middleware
from app.db.session import get_db
from app.schemas.market_data import MarketDataCreate
from app.services.market_data import MarketDataService

# Configure logging
setup_logging()
setup_audit_logging()  # Setup audit logging
logger = logging.getLogger(__name__)

# Prometheus metrics (only HTTP request metrics here, others are in prices.py)
http_requests_total = Counter(
    "http_requests_total", "Total number of HTTP requests", ["method", "endpoint"]
)
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds", "Duration of HTTP requests"
)
app_version = Gauge("app_version", "Application version", ["version"])

# Set initial values
app_version.labels(version="1.0.0").set(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    try:
        # Initialize rate limiter with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                await init_rate_limiter(settings.REDIS_URL)
                logger.info("Services initialized")
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(
                        f"Failed to initialize rate limiter after {max_retries} attempts: {e}"
                    )
                    raise
                logger.warning(
                    f"Rate limiter initialization attempt {attempt + 1} failed: {e}"
                )
                await asyncio.sleep(1)  # Wait before retry
        yield
    except Exception as e:
        logger.error(f"Error during application startup: {e}")
        raise
    finally:
        logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Market Data Service API - Secure and Production Ready",
    version="1.0.0",
    lifespan=lifespan,
    debug=settings.DEBUG,
)

# Add security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],  # In production, specify actual allowed hosts
)

# Add CORS middleware with dynamic settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600,
)

# Include routers
app.include_router(prices.router, prefix=settings.API_V1_STR + "/prices", tags=["prices"])
app.include_router(prices.router, prefix="/prices", tags=["prices"])


@app.get("/")
async def root() -> Dict[str, str]:
    """
    Root endpoint.

    Returns:
        Welcome message
    """
    return {"message": f"Welcome to the {settings.PROJECT_NAME} API"}


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint.

    Returns:
        Health status
    """
    return {"status": "healthy"}


@app.get("/ready")
async def readiness_check() -> Dict[str, str]:
    """
    Readiness check endpoint.

    Checks if the application is ready to serve traffic.
    This includes database connectivity and service dependencies.

    Returns:
        Readiness status
    """
    try:
        # Check database connectivity
        db = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()

        return {"status": "ready", "service": settings.PROJECT_NAME}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")


@app.get("/metrics")
async def metrics() -> Response:
    """
    Prometheus metrics endpoint.

    Returns:
        Application metrics in Prometheus format
    """
    if not settings.PROMETHEUS_ENABLED:
        raise HTTPException(status_code=404, detail="Metrics endpoint disabled")
    
    # Return metrics in Prometheus format
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/symbols")
async def get_symbols(
    db: Session = Depends(get_db), current_user: str = Depends(require_read_permission)
) -> List[str]:
    """
    Get all available symbols.

    Args:
        db: Database session
        current_user: Authenticated user

    Returns:
        List of available symbols
    """
    try:
        symbols = MarketDataService.get_all_symbols(db)
        return symbols
    except Exception as e:
        logger.error(f"Error getting symbols: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving symbols",
        )


@app.get("/moving-average/{symbol}")
async def get_moving_average(
    symbol: str,
    window: int = Query(settings.MOVING_AVERAGE_WINDOW, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: str = Depends(require_read_permission),
) -> Dict:
    """
    Get moving average for a symbol.

    Args:
        symbol: Symbol to get moving average for
        window: Window size for moving average calculation
        db: Database session
        current_user: Authenticated user

    Returns:
        Moving average data
    """
    try:
        moving_average = MarketDataService.calculate_moving_average(db, symbol, window)
        if moving_average is None:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for symbol {symbol}",
            )
        # Get the latest timestamp for the symbol
        latest_timestamp = MarketDataService.get_latest_timestamp(db, symbol)
        timestamp = latest_timestamp if latest_timestamp else datetime.now().isoformat()
        return {
            "symbol": symbol,
            "moving_average": moving_average,
            "window": window,
            "timestamp": timestamp,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating moving average: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error calculating moving average",
        )


@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    """Middleware to track HTTP requests for Prometheus metrics."""
    start_time = time.time()

    # Track request
    http_requests_total.labels(method=request.method, endpoint=request.url.path).inc()

    response = await call_next(request)

    # Track duration
    duration = time.time() - start_time
    http_request_duration_seconds.observe(duration)

    return response


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Content-Security-Policy"] = "default-src 'self'"

    return response


@app.middleware("http")
async def rate_limit_middleware_wrapper(request: Request, call_next):
    """Rate limiting middleware wrapper."""
    try:
        # Apply rate limiting to all endpoints except health checks
        if not request.url.path.startswith(("/health", "/ready", "/metrics")):
            await rate_limit_middleware(request, max_requests=100, window_seconds=60)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rate limiting error: {e}")
        # Continue on error (fail open)

    return await call_next(request)


@app.post("/api/v1/prices/", response_model=Dict[str, str])
async def create_price(
    price_data: MarketDataCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(require_write_permission),
) -> Dict[str, str]:
    """Create a new price entry."""
    try:
        result = MarketDataService.create_market_data(db, price_data)

        return {"message": "Price created successfully", "id": str(result.id)}
    except Exception as e:
        logger.error(f"Error creating price: {e}")
        raise HTTPException(status_code=500, detail="Error creating price")


@app.get("/api/v1/prices/", response_model=List[Dict[str, Any]])
async def get_prices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    symbol: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: str = Depends(require_read_permission),
) -> List[Dict[str, Any]]:
    """Get market data with optional filtering."""
    try:
        if symbol:
            prices = MarketDataService.get_market_data_by_symbol(
                db, symbol, skip=skip, limit=limit
            )
        else:
            prices = MarketDataService.get_market_data(db, skip=skip, limit=limit)

        return [
            {
                "id": price.id,
                "symbol": price.symbol,
                "price": price.price,
                "volume": price.volume,
                "source": price.source,
                "timestamp": price.timestamp.isoformat(),
            }
            for price in prices
        ]
    except Exception as e:
        logger.error(f"Error retrieving prices: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving prices")


@app.exception_handler(DataError)
async def sqlalchemy_data_error_handler(request: Request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": f"Invalid input data: {str(exc)}"},
    )


@app.exception_handler(IntegrityError)
async def sqlalchemy_integrity_error_handler(request: Request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": f"Invalid input data: {str(exc)}"},
    )
