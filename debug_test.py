#!/usr/bin/env python3
"""Debug script to test the latest price endpoint."""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import app

# Import models to register them with Base
from app.models import *  # noqa: F401, F403
from app.services.market_data import MarketDataService

# Create test database
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


app.dependency_overrides[get_db] = override_get_db

# Test the endpoint
client = TestClient(app)

# Add some test data
session = TestingSessionLocal()
MarketDataService.add_price(session, "AAPL", 123.45, volume=1000, source="test_source")
session.commit()
session.close()

# Test the API
response = client.get("/api/v1/prices/latest?symbol=AAPL")
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
