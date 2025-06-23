#!/bin/bash

# Start all services
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Run database migrations
alembic upgrade head

# Start the Kafka consumer in the background
python scripts/run_consumer.py &

# Start the FastAPI application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
