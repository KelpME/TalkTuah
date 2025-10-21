#!/bin/bash
# Delete a model via API (handles permissions correctly)

set -e

MODEL_ID="$1"

if [ -z "$MODEL_ID" ]; then
    echo "Usage: $0 <model-id>"
    echo ""
    echo "Example:"
    echo "  $0 google/gemma-2-2b-it"
    echo ""
    echo "Available models:"
    ls -1 ./models/hub/ 2>/dev/null | grep "^models--" | sed 's/models--/  - /' | sed 's/--/\//' || echo "  (none)"
    exit 1
fi

# Get API key from .env
API_KEY=$(grep "^PROXY_API_KEY=" .env 2>/dev/null | cut -d'=' -f2)
if [ -z "$API_KEY" ]; then
    echo "Error: PROXY_API_KEY not found in .env"
    exit 1
fi

# Convert model ID to directory name for size check
MODEL_DIR_NAME="models--$(echo "$MODEL_ID" | sed 's/\//--/g')"
MODEL_PATH="./models/hub/$MODEL_DIR_NAME"

# Check if model exists
if [ ! -d "$MODEL_PATH" ]; then
    echo "Error: Model not found: $MODEL_ID"
    echo "Path checked: $MODEL_PATH"
    echo ""
    echo "Available models:"
    ls -1 ./models/hub/ 2>/dev/null | grep "^models--" | sed 's/models--/  - /' | sed 's/--/\//' || echo "  (none)"
    exit 1
fi

# Get model size
MODEL_SIZE=$(du -sh "$MODEL_PATH" | cut -f1)

echo "=========================================="
echo "Delete Model"
echo "=========================================="
echo ""
echo "Model: $MODEL_ID"
echo "Size: $MODEL_SIZE"
echo ""

# Check if this is the current model
CURRENT_MODEL=$(grep "^DEFAULT_MODEL=" .env 2>/dev/null | cut -d'=' -f2)
if [ "$CURRENT_MODEL" = "$MODEL_ID" ]; then
    echo "⚠️  WARNING: This is your current DEFAULT_MODEL!"
    echo ""
    echo "If you delete this model, vLLM will fail to start."
    echo "You should switch models first in the settings."
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
fi

# Confirm deletion
read -p "Are you sure you want to delete this model? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "Deleting model via API..."

# Call API to delete model (API runs in container with proper permissions)
RESPONSE=$(curl -s -w "\n%{http_code}" -X DELETE \
    "http://localhost:8787/api/delete-model?model_id=$MODEL_ID" \
    -H "Authorization: Bearer $API_KEY")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo ""
    echo "✓ Model deleted successfully: $MODEL_ID"
    echo "  Freed: $MODEL_SIZE"
    echo ""
    echo "Note: You may want to restart vLLM if this was the active model:"
    echo "  docker compose restart vllm"
elif [ "$HTTP_CODE" = "404" ]; then
    echo ""
    echo "✗ Model not found in API"
    echo "Response: $BODY"
    exit 1
else
    echo ""
    echo "✗ Failed to delete model (HTTP $HTTP_CODE)"
    echo "Response: $BODY"
    exit 1
fi

echo ""
echo "=========================================="
echo "Done!"
echo "=========================================="
