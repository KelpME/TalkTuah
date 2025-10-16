#!/bin/bash
set -e

MODEL_ID="$1"
PROGRESS_FILE="/tmp/model_download_progress.txt"
MODELS_DIR="./models"

if [ -z "$MODEL_ID" ]; then
    echo "Usage: $0 <model-id>"
    exit 1
fi

# Create models directory if it doesn't exist
mkdir -p "$MODELS_DIR"

# Initialize progress file
echo "status=starting" > "$PROGRESS_FILE"
echo "model=$MODEL_ID" >> "$PROGRESS_FILE"
echo "progress=0" >> "$PROGRESS_FILE"

echo "=========================================="
echo "Downloading model: $MODEL_ID"
echo "To: $MODELS_DIR"
echo "=========================================="

# Update progress
echo "status=downloading" > "$PROGRESS_FILE"
echo "model=$MODEL_ID" >> "$PROGRESS_FILE"
echo "progress=10" >> "$PROGRESS_FILE"

# Set HF_HOME to use local models directory
# Always use /workspace/models regardless of where script is run from
export HF_HOME="/workspace/$MODELS_DIR"

# Download the model using huggingface-cli
huggingface-cli download "$MODEL_ID" 2>&1 | while IFS= read -r line; do
    echo "$line"
    # Update progress based on output
    if [[ "$line" == *"Fetching"* ]]; then
        echo "progress=30" >> "$PROGRESS_FILE"
    elif [[ "$line" == *"Downloading"* ]]; then
        echo "progress=50" >> "$PROGRESS_FILE"
    fi
done

echo "progress=70" >> "$PROGRESS_FILE"

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
echo "progress=90" >> "$PROGRESS_FILE"

echo ""
echo "=========================================="
echo "Download complete!"
echo "=========================================="
echo ""
echo "Model downloaded to: $MODELS_DIR"
echo "To use this model, select it in the frontend settings."
echo ""

echo "status=complete" > "$PROGRESS_FILE"
echo "model=$MODEL_ID" >> "$PROGRESS_FILE"
echo "progress=100" >> "$PROGRESS_FILE"
