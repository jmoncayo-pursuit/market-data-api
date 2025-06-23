"""Configuration settings for the Market Data Service."""

import os
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # API settings
    PROJECT_NAME: str = Field(
        default="Market Data Service",
        env="PROJECT_NAME",
        description="Project name for API documentation"
    )
    API_V1_STR: str = Field(
        default="/api/v1",
        env="API_V1_STR",
        description="API version string"
    )
    DEBUG: bool = Field(
        default=False,
        env="DEBUG",
        description="Debug mode flag"
    )
    HOST: str = Field(
        default="0.0.0.0",
        env="HOST",
        description="Host to bind the server to"
    )
    PORT: int = Field(
        default=8000,
        env="PORT",
        description="Port to bind the server to"
    )
    # Additional API settings to match environment variables
    API_HOST: str = Field(
        default="0.0.0.0",
        env="API_HOST",
        description="API host to bind the server to"
    )
    API_PORT: int = Field(
        default=8000,
        env="API_PORT",
        description="API port to bind the server to"
    )
    API_WORKERS: int = Field(
        default=4,
        env="API_WORKERS",
        description="Number of API workers"
    )
    API_RELOAD: bool = Field(
        default=True,
        env="API_RELOAD",
        description="Enable API auto-reload"
    )

    # Database settings
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/market_data",
        env="DATABASE_URL",
        description="Database connection string"
    )
    SQLALCHEMY_DATABASE_URI: str = Field(
        default="",
        env="SQLALCHEMY_DATABASE_URI",
        description="SQLAlchemy database URI (deprecated, use DATABASE_URL)"
    )

    # Redis settings
    REDIS_HOST: str = Field(
        default="localhost",
        env="REDIS_HOST",
        description="Redis host"
    )
    REDIS_PORT: int = Field(
        default=6379,
        env="REDIS_PORT",
        description="Redis port"
    )
    REDIS_DB: int = Field(
        default=0,
        env="REDIS_DB",
        description="Redis database number"
    )
    REDIS_PASSWORD: str = Field(
        default="",
        env="REDIS_PASSWORD",
        description="Redis password"
    )
    REDIS_URL: str = Field(
        default="",
        env="REDIS_URL",
        description="Redis connection URL"
    )

    # Kafka settings
    KAFKA_BOOTSTRAP_SERVERS: str = Field(
        default="localhost:9092",
        env="KAFKA_BOOTSTRAP_SERVERS",
        description="Kafka bootstrap servers"
    )
    KAFKA_CONSUMER_GROUP: str = Field(
        default="market_data_group",
        env="KAFKA_CONSUMER_GROUP",
        description="Kafka consumer group ID"
    )
    KAFKA_TOPIC: str = Field(
        default="price-events",
        env="KAFKA_TOPIC",
        description="Kafka topic for price events"
    )
    KAFKA_AUTO_OFFSET_RESET: str = Field(
        default="earliest",
        env="KAFKA_AUTO_OFFSET_RESET",
        description="Kafka auto offset reset policy"
    )

    # Security settings
    API_KEY: str = Field(
        default="",
        env="API_KEY",
        description="API key for authentication"
    )
    SECRET_KEY: str = Field(
        default="",
        env="SECRET_KEY",
        description="Secret key for JWT tokens"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        env="ACCESS_TOKEN_EXPIRE_MINUTES",
        description="Access token expiration time in minutes"
    )

    # Rate limiting settings
    RATE_LIMIT_REQUESTS: int = Field(
        default=100,
        env="RATE_LIMIT_REQUESTS",
        description="Maximum requests per window"
    )
    RATE_LIMIT_WINDOW: int = Field(
        default=60,
        env="RATE_LIMIT_WINDOW",
        description="Rate limit window in seconds"
    )

    # Monitoring settings
    PROMETHEUS_ENABLED: bool = Field(
        default=True,
        env="PROMETHEUS_ENABLED",
        description="Enable Prometheus metrics"
    )
    GRAFANA_ENABLED: bool = Field(
        default=True,
        env="GRAFANA_ENABLED",
        description="Enable Grafana dashboards"
    )
    METRICS_PORT: int = Field(
        default=9090,
        env="METRICS_PORT",
        description="Prometheus metrics port"
    )

    # Logging settings
    LOG_LEVEL: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Logging level"
    )
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT",
        description="Log format string"
    )

    # CORS settings
    CORS_ORIGINS: List[str] = Field(
        default=["*"],
        env="CORS_ORIGINS",
        description="CORS allowed origins"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(
        default=True,
        env="CORS_ALLOW_CREDENTIALS",
        description="Allow CORS credentials"
    )

    # Cache settings
    CACHE_TTL: int = Field(
        default=300,
        env="CACHE_TTL",
        description="Cache TTL in seconds"
    )
    CACHE_ENABLED: bool = Field(
        default=True,
        env="CACHE_ENABLED",
        description="Enable Redis caching"
    )

    # Market data settings
    DEFAULT_PROVIDER: str = Field(
        default="alpha_vantage",
        env="DEFAULT_PROVIDER",
        description="Default market data provider"
    )
    POLLING_INTERVAL: int = Field(
        default=60,
        env="POLLING_INTERVAL",
        description="Default polling interval in seconds"
    )
    MOVING_AVERAGE_WINDOW: int = Field(
        default=5,
        env="MOVING_AVERAGE_WINDOW",
        description="Default moving average window size"
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set SQLALCHEMY_DATABASE_URI from DATABASE_URL if not explicitly set
        if not self.SQLALCHEMY_DATABASE_URI and self.DATABASE_URL:
            self.SQLALCHEMY_DATABASE_URI = self.DATABASE_URL
        
        # Build REDIS_URL from components if not explicitly set
        if not self.REDIS_URL:
            if self.REDIS_PASSWORD:
                self.REDIS_URL = f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
            else:
                self.REDIS_URL = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    class Config:
        """Configuration settings for the application."""
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
