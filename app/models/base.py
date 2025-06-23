"""Base model for SQLAlchemy ORM models."""

from datetime import datetime

from sqlalchemy import Column, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()
"""Declarative base for all ORM models."""


class TimestampMixin:
    """Mixin class that adds timestamp columns to models."""

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
