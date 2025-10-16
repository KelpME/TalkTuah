#!/bin/bash
# Test API temperature parameter directly

API_KEY=$(grep PROXY_API_KEY .env | cut -d'=' -f2)
TEMP=${1:-0.1}

echo "Testing API with temperature: $TEMP"
echo "========================================"

curl -X POST http://localhost:8787/api/chat \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"Qwen/Qwen2.5-1.5B-Instruct\",
    \"messages\": [
      {\"role\": \"user\", \"content\": \"Say hello\"}
    ],
    \"temperature\": $TEMP,
    \"stream\": false
  }" | jq .

echo ""
echo "========================================"
echo "Check API logs with: docker logs -f vllm-proxy-api"
echo "Should show: [API Proxy] Temperature: $TEMP"
