"""Configuration settings for the Market Data Service."""

from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # API settings
    PROJECT_NAME: str = "Market Data Service"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # Database settings
    SQLALCHEMY_DATABASE_URI: str = Field(
        default="sqlite:///./market_data.db",
        description="Database connection string",
    )

    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )

    # Kafka settings
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_CONSUMER_GROUP: str = "market_data_group"
    KAFKA_TOPIC: str = "market_data"

    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]

    class Config:
        """Configuration settings for the application."""

        case_sensitive = True


settings = Settings()
