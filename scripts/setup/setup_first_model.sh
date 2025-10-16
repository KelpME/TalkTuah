#!/bin/bash
# First-time model setup script

set -e

echo "=========================================="
echo "vLLM Model Setup"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Error: .env file not found"
    echo "Please copy .env.example to .env first:"
    echo "  cp .env.example .env"
    exit 1
fi

# Check if DEFAULT_MODEL is already set
CURRENT_MODEL=$(grep "^DEFAULT_MODEL=" .env | cut -d'=' -f2)
if [ -n "$CURRENT_MODEL" ]; then
    echo "DEFAULT_MODEL is already set to: $CURRENT_MODEL"
    read -p "Do you want to change it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping current model."
        exit 0
    fi
fi

# Check for downloaded models
MODELS_DIR="./models/hub"
if [ ! -d "$MODELS_DIR" ]; then
    echo "No models directory found."
    echo "Please download a model first:"
    echo "  ./scripts/download_model.sh <model-id>"
    exit 1
fi

# List available models
echo "Scanning for downloaded models..."
MODELS=()
for model_dir in "$MODELS_DIR"/models--*; do
    if [ -d "$model_dir" ]; then
        # Convert models--org--name to org/name
        model_name=$(basename "$model_dir" | sed 's/models--//' | sed 's/--/\//')
        MODELS+=("$model_name")
    fi
done

if [ ${#MODELS[@]} -eq 0 ]; then
    echo ""
    echo "No models found in $MODELS_DIR"
    echo ""
    echo "Please download a model first:"
    echo "  ./scripts/download_model.sh Qwen/Qwen2.5-1.5B-Instruct"
    echo ""
    echo "Popular models:"
    echo "  - Qwen/Qwen2.5-1.5B-Instruct (small, fast)"
    echo "  - Qwen/Qwen2.5-3B-Instruct (medium)"
    echo "  - meta-llama/Llama-3.2-3B-Instruct (requires HF access)"
    exit 1
fi

# Display models
echo ""
echo "Found ${#MODELS[@]} downloaded model(s):"
echo ""
for i in "${!MODELS[@]}"; do
    echo "  $((i+1)). ${MODELS[$i]}"
done
echo ""

# Prompt for selection
while true; do
    read -p "Select a model (1-${#MODELS[@]}): " selection
    if [[ "$selection" =~ ^[0-9]+$ ]] && [ "$selection" -ge 1 ] && [ "$selection" -le "${#MODELS[@]}" ]; then
        break
    fi
    echo "Invalid selection. Please enter a number between 1 and ${#MODELS[@]}"
done

SELECTED_MODEL="${MODELS[$((selection-1))]}"

echo ""
echo "Selected: $SELECTED_MODEL"
echo ""

# Update .env
if grep -q "^DEFAULT_MODEL=" .env; then
    sed -i.bak "s|^DEFAULT_MODEL=.*|DEFAULT_MODEL=$SELECTED_MODEL|" .env
else
    echo "DEFAULT_MODEL=$SELECTED_MODEL" >> .env
fi

echo "✓ Updated .env with DEFAULT_MODEL=$SELECTED_MODEL"
echo ""

# Ask to start vLLM
read -p "Start vLLM with this model now? (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo ""
    echo "Starting vLLM..."
    docker compose up -d vllm
    echo ""
    echo "✓ vLLM is starting. This may take 30-60 seconds."
    echo ""
    echo "Check status with:"
    echo "  docker logs vllm-server"
    echo "  curl http://localhost:8787/api/healthz"
else
    echo ""
    echo "To start vLLM later, run:"
    echo "  docker compose up -d vllm"
fi

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
