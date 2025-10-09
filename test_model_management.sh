#!/bin/bash
# Test script for model management system

set -e

echo "=========================================="
echo "Model Management System Test"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get API key from .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

API_KEY="${PROXY_API_KEY:-change-me-hehehoho}"
BASE_URL="http://localhost:8787"

echo -e "${YELLOW}Step 1: Check if services are running${NC}"
if docker ps | grep -q vllm-server && docker ps | grep -q vllm-proxy-api; then
    echo -e "${GREEN}✓ Services are running${NC}"
else
    echo -e "${RED}✗ Services are not running. Start with: make up${NC}"
    exit 1
fi
echo ""

echo -e "${YELLOW}Step 2: Test API root endpoint${NC}"
curl -s "$BASE_URL/" | jq '.' || echo "Failed to connect to API"
echo ""

echo -e "${YELLOW}Step 3: Check model status${NC}"
MODEL_STATUS=$(curl -s -H "Authorization: Bearer $API_KEY" "$BASE_URL/api/model-status")
echo "$MODEL_STATUS" | jq '.'
echo ""

MODELS_AVAILABLE=$(echo "$MODEL_STATUS" | jq -r '.models_available')
if [ "$MODELS_AVAILABLE" = "true" ]; then
    echo -e "${GREEN}✓ Models are available${NC}"
    echo "Downloaded models:"
    echo "$MODEL_STATUS" | jq -r '.downloaded_models[]'
else
    echo -e "${YELLOW}⚠ No models downloaded yet${NC}"
    echo "You can download a model with:"
    echo "  ./scripts/download_model.sh Qwen/Qwen2.5-1.5B-Instruct"
fi
echo ""

echo -e "${YELLOW}Step 4: Check models directory${NC}"
if [ -d "./models" ]; then
    echo -e "${GREEN}✓ Models directory exists${NC}"
    echo "Contents:"
    ls -lah ./models/
    if [ -d "./models/hub" ]; then
        echo ""
        echo "Hub contents:"
        ls -lah ./models/hub/ 2>/dev/null || echo "  (empty)"
    fi
else
    echo -e "${RED}✗ Models directory does not exist${NC}"
fi
echo ""

echo -e "${YELLOW}Step 5: Check vLLM health${NC}"
HEALTH=$(curl -s -H "Authorization: Bearer $API_KEY" "$BASE_URL/api/healthz")
echo "$HEALTH" | jq '.'
echo ""

STATUS=$(echo "$HEALTH" | jq -r '.status')
if [ "$STATUS" = "healthy" ]; then
    echo -e "${GREEN}✓ vLLM is healthy${NC}"
elif [ "$STATUS" = "degraded" ]; then
    echo -e "${YELLOW}⚠ vLLM is degraded (model may not be loaded)${NC}"
else
    echo -e "${RED}✗ vLLM is unhealthy${NC}"
fi
echo ""

echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo ""
echo "Models directory: ./models"
echo "Models are now stored locally and accessible outside containers"
echo ""
echo "Next steps:"
echo "  1. Download a model: ./scripts/download_model.sh <model-id>"
echo "  2. Check status: curl -H 'Authorization: Bearer $API_KEY' $BASE_URL/api/model-status"
echo "  3. View models: ls -la ./models/hub/"
echo "  4. Delete a model: rm -rf ./models/hub/models--<org>--<model>"
echo ""
