"""API package for the Market Data Service."""

from fastapi import APIRouter

from app.api.endpoints import prices

api_router = APIRouter()
api_router.include_router(prices.router, prefix="/prices", tags=["prices"])
