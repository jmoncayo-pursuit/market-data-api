[![codecov](https://codecov.io/gh/jmoncayo-pursuit/market-data-api/graph/badge.svg?token=GK6cjtooDF)](https://codecov.io/gh/jmoncayo-pursuit/market-data-api)
[![CI/CD Pipeline](https://github.com/jmoncayo-pursuit/market-data-api/actions/workflows/ci.yml/badge.svg)](https://github.com/jmoncayo-pursuit/market-data-api/actions/workflows/ci.yml)

# Market Data API

A high-performance, production-ready Market Data API built with FastAPI, PostgreSQL, Redis, and Kafka. Features comprehensive monitoring, rate limiting, and real-time data processing capabilities.

## Features

- Real-time market data processing (Kafka event streaming)
- High-performance caching (Redis)
- Monitoring (Prometheus, Grafana)
- Security: rate limiting, authentication, audit logging
- Robust, comprehensive test suite
- DevOps ready: Docker, CI/CD, infrastructure as code

## Architecture

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ FastAPI App  │   │ PostgreSQL   │   │   Redis      │
│  (8000)      │<->│  (5432)      │   │   (6379)     │
└──────────────┘   └──────────────┘   └──────────────┘
      │                  │                  │
      ▼                  ▼                  ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   Kafka      │   │ Prometheus   │   │   Grafana    │
│   (9092)     │   │  (9090)      │   │   (3000)     │
└──────────────┘   └──────────────┘   └──────────────┘
```

## Tech Stack

- FastAPI, SQLAlchemy, Alembic
- PostgreSQL, Redis, Apache Kafka
- Prometheus, Grafana
- pytest, coverage
- GitHub Actions, Docker

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd market-data-api
   ```
2. **Start services**
   ```bash
   docker-compose up -d
   ```
3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
4. **Run migrations**
   ```bash
   alembic upgrade head
   ```
5. **Start the app**
   ```bash
   python -m app.main
   ```
6. **Run tests**
   ```bash
   pytest tests/ --cov=app --cov-report=term-missing
   ```

## API Endpoints

- `GET /health` — Health check
- `GET /ready` — Readiness
- `GET /prices/{symbol}` — Market data
- `GET /prices/{symbol}/history` — Price history
- `GET /moving-average/{symbol}` — Moving average
- `GET /metrics` — Prometheus metrics

## Monitoring

- Prometheus: HTTP, DB, Redis, business metrics
- Grafana: API, DB, system dashboards

## Security

- Rate limiting (per-endpoint)
- API key authentication
- Audit logging
- Input validation (Pydantic)

## Testing

- Unit, integration, API, and performance tests
- Run: `pytest tests/ --cov=app --cov-report=term-missing`

## Deployment

- Build: `docker build -t market-data-api .`
- Run: `docker run -p 8000:8000 market-data-api`

## License

MIT License. See [LICENSE](LICENSE).
