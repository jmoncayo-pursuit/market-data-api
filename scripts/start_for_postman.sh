#!/bin/bash

echo "🚀 Starting Market Data API for Postman tests..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Start services
echo "📦 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if API is ready
echo "🔍 Checking API readiness..."
for i in {1..30}; do
    if curl -s http://localhost:8000/ready > /dev/null 2>&1; then
        echo "✅ API is ready!"
        echo ""
        echo "🌐 API is running at: http://localhost:8000"
        echo "📊 Health check: http://localhost:8000/health"
        echo "📈 API docs: http://localhost:8000/docs"
        echo ""
        echo "📋 Postman Environment Variables:"
        echo "   base_url: http://127.0.0.1:8000"
        echo ""
        echo "🎯 You can now run your Postman tests!"
        exit 0
    fi
    echo "⏳ Waiting for API to be ready... (attempt $i/30)"
    sleep 2
done

echo "❌ API failed to start properly. Check logs with: docker-compose logs api"
exit 1
