#!/bin/bash

echo "🎬 Market Data API Demo Script"
echo "================================"

echo ""
echo "1. 🐳 Docker Setup & Architecture"
echo "=================================="
docker-compose ps
echo ""
docker system df

echo ""
echo "2. 🏥 Health Checks"
echo "==================="
echo "Health:"
curl -s http://localhost:8000/health | jq .
echo ""
echo "Ready:"
curl -s http://localhost:8000/ready | jq .

echo ""
echo "3. 📊 API Functionality"
echo "======================"
echo "Creating market data..."
curl -X POST http://localhost:8000/api/v1/prices/ \
  -H "Content-Type: application/json" \
  -d '{"symbol":"AAPL","price":150.25,"volume":1000,"source":"demo"}' | jq .

echo ""
echo "Getting latest price..."
curl -s http://localhost:8000/api/v1/prices/latest?symbol=AAPL | jq .

echo ""
echo "Creating polling job..."
curl -X POST http://localhost:8000/api/v1/prices/poll \
  -H "Content-Type: application/json" \
  -d '{"symbols":["AAPL","MSFT","GOOGL"],"interval":60}' | jq .

echo ""
echo "4. 🗄️ Database & Cache"
echo "====================="
echo "Database data:"
docker exec -it blockhouse-db-1 psql -U postgres -d market_data -c "SELECT symbol, price, timestamp FROM market_data ORDER BY timestamp DESC LIMIT 3;"

echo ""
echo "Redis keys:"
docker exec -it blockhouse-redis-1 redis-cli KEYS "*"

echo ""
echo "5. 📈 Monitoring & Observability"
echo "==============================="
echo "API Metrics:"
curl -s http://localhost:8000/metrics | head -10

echo ""
echo "Available symbols:"
curl -s http://localhost:8000/symbols | jq .

echo ""
echo "Moving average for AAPL:"
curl -s http://localhost:8000/moving-average/AAPL | jq .

echo ""
echo "6. 🎛️ Monitoring Dashboards"
echo "=========================="
echo "Prometheus: http://localhost:9090"
echo "Grafana: http://localhost:3000 (admin/admin)"
echo "API Docs: http://localhost:8000/docs"

echo ""
echo "7. 🧪 Testing"
echo "============"
pytest --cov=app tests/ -v --tb=short

echo ""
echo "✅ Demo Complete!"
echo ""
echo "📊 Access Monitoring:"
echo "   - Grafana: http://localhost:3000"
echo "   - Prometheus: http://localhost:9090"
echo "   - API Docs: http://localhost:8000/docs"
