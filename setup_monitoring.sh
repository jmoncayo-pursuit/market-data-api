#!/bin/bash

echo "🔧 Setting up Monitoring Stack"
echo "=============================="

echo ""
echo "1. 📊 Generate API Metrics"
echo "=========================="
echo "Making API calls to generate metrics..."

# Generate some API traffic
for i in {1..10}; do
    curl -s http://localhost:8000/health > /dev/null
    curl -s http://localhost:8000/metrics > /dev/null
    curl -s http://localhost:8000/api/v1/prices/ > /dev/null
    sleep 1
done

echo "✅ Generated API traffic"

echo ""
echo "2. 🎯 Prometheus Setup"
echo "====================="
echo "Prometheus URL: http://localhost:9090"
echo ""
echo "To see metrics in Prometheus:"
echo "1. Go to http://localhost:9090"
echo "2. Click 'Status' → 'Targets' to see if API is being scraped"
echo "3. Click 'Graph' and search for metrics like:"
echo "   - http_requests_total"
echo "   - market_data_points_total"
echo "   - polling_jobs_active"

echo ""
echo "3. 📈 Grafana Setup"
echo "=================="
echo "Grafana URL: http://localhost:3000"
echo "Username: admin"
echo "Password: admin"
echo ""
echo "After login:"
echo "1. Add Prometheus as a data source:"
echo "   - URL: http://prometheus:9090"
echo "   - Access: Server (default)"
echo "2. Create a new dashboard"
echo "3. Add panels for metrics like:"
echo "   - API request rate"
echo "   - Market data points"
echo "   - System health"

echo ""
echo "4. 🧪 Test Monitoring"
echo "===================="
echo "Current API metrics:"
curl -s http://localhost:8000/metrics | jq .

echo ""
echo "Prometheus targets:"
curl -s "http://localhost:9090/api/v1/targets" | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'

echo ""
echo "✅ Monitoring setup complete!"
echo ""
echo "📊 Access URLs:"
echo "   - Prometheus: http://localhost:9090"
echo "   - Grafana: http://localhost:3000"
echo "   - API Docs: http://localhost:8000/docs"

echo ""
echo "🚀 Setting up Grafana monitoring..."

# Wait for Grafana to be ready
echo "⏳ Waiting for Grafana to be ready..."
sleep 10

# Add Prometheus data source to Grafana
echo "📊 Adding Prometheus data source to Grafana..."

curl -X POST http://admin:admin@localhost:3000/api/datasources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Prometheus",
    "type": "prometheus",
    "url": "http://prometheus:9090",
    "access": "proxy",
    "isDefault": true
  }'

echo ""
echo "✅ Prometheus data source added!"

# Import the dashboard
echo "📈 Importing dashboard..."

curl -X POST http://admin:admin@localhost:3000/api/dashboards/import \
  -H "Content-Type: application/json" \
  -d @grafana_dashboard.json

echo ""
echo "✅ Dashboard imported!"

# Generate some API traffic to see metrics
echo "🔄 Generating API traffic to populate metrics..."
for i in {1..20}; do
  curl -s http://localhost:8000/health > /dev/null
  curl -s http://localhost:8000/metrics > /dev/null
  sleep 0.5
done

echo ""
echo "🎉 Monitoring setup complete!"
echo ""
echo "📊 Access your monitoring:"
echo "   Grafana: http://localhost:3000 (admin/admin)"
echo "   Prometheus: http://localhost:9090"
echo ""
echo "📋 Dashboard should now show:"
echo "   - HTTP Requests Total"
echo "   - Market Data Points"
echo "   - Application Version"
echo "   - Active Polling Jobs"
