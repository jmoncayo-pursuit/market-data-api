# Market Data API

A high-performance, production-ready Market Data API built with FastAPI, PostgreSQL, Redis, and Kafka. Features comprehensive monitoring, rate limiting, and real-time data processing capabilities.

## 🚀 Features

- **Real-time Market Data Processing**: Kafka-based event streaming for price updates
- **High-Performance Caching**: Redis-based caching with intelligent invalidation
- **Comprehensive Monitoring**: Prometheus metrics, Grafana dashboards, and structured logging
- **Production-Grade Security**: Rate limiting, authentication, and audit logging
- **Robust Testing**: 79% test coverage with comprehensive error handling
- **DevOps Ready**: Docker, CI/CD pipelines, and infrastructure as code

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │   PostgreSQL    │    │     Redis       │
│   (Port 8000)   │◄──►│   (Port 5432)   │    │   (Port 6379)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Kafka       │    │   Prometheus    │    │     Grafana     │
│   (Port 9092)   │    │   (Port 9090)   │    │   (Port 3000)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Tech Stack

- **Backend**: FastAPI, SQLAlchemy, Alembic
- **Database**: PostgreSQL
- **Cache**: Redis
- **Message Queue**: Apache Kafka
- **Monitoring**: Prometheus, Grafana
- **Testing**: pytest, coverage
- **CI/CD**: GitHub Actions
- **Containerization**: Docker, Docker Compose

## 📦 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Git

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd market-data-api
   ```

2. **Start the services**
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

5. **Start the application**
   ```bash
   python -m app.main
   ```

6. **Run tests**
   ```bash
   pytest tests/ --cov=app --cov-report=term-missing
   ```

### API Endpoints

- **Health Check**: `GET /health`
- **API Status**: `GET /ready`
- **Market Data**: `GET /prices/{symbol}`
- **Price History**: `GET /prices/{symbol}/history`
- **Moving Average**: `GET /moving-average/{symbol}`
- **Metrics**: `GET /metrics`

## 📊 Monitoring

### Prometheus Metrics
- HTTP request duration and count
- Database connection pool metrics
- Redis operation metrics
- Custom business metrics

### Grafana Dashboards
- API performance dashboard
- Database performance dashboard
- System health dashboard

## 🔒 Security

- **Rate Limiting**: Configurable per-endpoint rate limits
- **Authentication**: API key-based authentication
- **Audit Logging**: Comprehensive request/response logging
- **Input Validation**: Pydantic-based request validation

## 🧪 Testing

The project maintains **79% test coverage** with comprehensive testing:

- **Unit Tests**: Core business logic
- **Integration Tests**: Database and external service integration
- **API Tests**: Endpoint functionality and error handling
- **Performance Tests**: Load testing and benchmarking

```bash
# Run all tests
pytest tests/ --cov=app --cov-report=term-missing

# Run specific test categories
pytest tests/test_api_endpoints.py
pytest tests/test_services/
pytest tests/test_integration.py
```

## 🚀 Deployment

### Docker Deployment

```bash
# Build the image
docker build -t market-data-api .

# Run the container
docker run -p 8000:8000 market-data-api
```

### Production Considerations

- Use environment variables for configuration
- Set up proper logging and monitoring
- Configure database connection pooling
- Enable rate limiting and security headers
- Set up backup and disaster recovery

## 📈 Performance

- **Response Time**: < 50ms for cached data
- **Throughput**: 1000+ requests/second
- **Concurrent Users**: 100+ simultaneous connections
- **Data Freshness**: Real-time updates via Kafka

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For questions or issues:
- Create an issue in the repository
- Check the documentation
- Review the test examples

---

**Built with ❤️ using modern Python and DevOps practices**
