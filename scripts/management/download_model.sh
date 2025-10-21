#!/bin/bash
set -e

MODEL_ID="$1"
MODELS_DIR="./models"

if [ -z "$MODEL_ID" ]; then
    echo "Usage: $0 <model-id>"
    exit 1
fi

# Create models directory if it doesn't exist
mkdir -p "$MODELS_DIR"

echo "=========================================="
echo "Downloading model: $MODEL_ID"
echo "To: $MODELS_DIR"
echo "=========================================="

# Set HF_HOME to use local models directory
# Always use /workspace/models regardless of where script is run from
export HF_HOME="/workspace/$MODELS_DIR"

# Download the model using huggingface-cli
huggingface-cli download "$MODEL_ID"

echo ""
echo "=========================================="
echo "Model downloaded successfully!"
echo "Location: $MODELS_DIR"
echo "=========================================="
echo ""
echo "Updating .env..."

# Update .env with the new model
cd "$(dirname "$0")/.."
if grep -q "^DEFAULT_MODEL=" .env 2>/dev/null; then
    sed -i.bak "s|^DEFAULT_MODEL=.*|DEFAULT_MODEL=$MODEL_ID|g" .env
else
    echo "DEFAULT_MODEL=$MODEL_ID" >> .env
fi

echo "Updated DEFAULT_MODEL to: $MODEL_ID"

echo ""
echo "=========================================="
echo "Download complete!"
echo "=========================================="
echo ""
echo "Model downloaded to: $MODELS_DIR"
echo "To use this model, select it in the frontend settings."
echo ""
