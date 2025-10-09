#!/bin/bash
# Delete a model from the models directory

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

# Convert model ID to directory name
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
echo "Path: $MODEL_PATH"
echo "Size: $MODEL_SIZE"
echo ""

# Check if this is the current model
CURRENT_MODEL=$(grep "^DEFAULT_MODEL=" .env 2>/dev/null | cut -d'=' -f2)
if [ "$CURRENT_MODEL" = "$MODEL_ID" ]; then
    echo "⚠️  WARNING: This is your current DEFAULT_MODEL!"
    echo ""
    echo "If you delete this model, vLLM will fail to start."
    echo "You should:"
    echo "  1. Run 'make setup' to select a different model first"
    echo "  2. Then delete this model"
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
echo "Stopping containers..."
docker compose stop vllm api

echo ""
echo "Deleting model..."
# Model files are owned by root (from Docker), need sudo
if [ -w "$MODEL_PATH" ]; then
    rm -rf "$MODEL_PATH"
else
    echo "Model files are owned by root, using sudo..."
    sudo rm -rf "$MODEL_PATH"
fi

# Check if deletion was successful
if [ ! -d "$MODEL_PATH" ]; then
    echo ""
    echo "✓ Model deleted: $MODEL_ID"
    echo "  Freed: $MODEL_SIZE"
    echo ""
else
    echo ""
    echo "✗ Failed to delete model completely"
    echo "Some files may remain. Try: sudo rm -rf $MODEL_PATH"
    echo ""
    exit 1
fi

# Ask to restart
read -p "Restart containers now? (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo ""
    echo "Starting containers..."
    docker compose up -d
    echo ""
    echo "✓ Containers restarted"
else
    echo ""
    echo "To restart later, run:"
    echo "  docker compose up -d"
fi

echo ""
echo "=========================================="
echo "Done!"
echo "=========================================="
