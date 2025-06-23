#!/bin/bash
echo "=== Market Data API Demo ==="
echo "1. Health Check:"
curl -s http://localhost:8000/health | jq .
echo ""
echo "2. Create Market Data:"
curl -s -X POST http://localhost:8000/api/v1/prices/ \
  -H "Content-Type: application/json" \
  -d '{"symbol":"AAPL","price":150.25,"volume":1000,"source":"demo"}' | jq .
echo ""
echo "3. Get Latest Price:"
curl -s http://localhost:8000/api/v1/prices/latest\?symbol\=AAPL | jq .
