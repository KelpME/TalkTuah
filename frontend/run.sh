#!/bin/bash
# Standalone script to run TuivLLM frontend

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Load environment variables from parent .env if it exists
if [ -f "$SCRIPT_DIR/../.env" ]; then
    export $(cat "$SCRIPT_DIR/../.env" | grep -v '^#' | xargs)
fi

# Set defaults if not provided
export VLLM_API_URL="${VLLM_API_URL:-http://localhost:8787/api}"
export PROXY_API_KEY="${PROXY_API_KEY:-change-me}"
export DEFAULT_MODEL="${DEFAULT_MODEL:-meta-llama/Meta-Llama-3.1-8B-Instruct}"

echo "Starting TuivLLM Chat Interface..."
echo "API URL: $VLLM_API_URL"
echo "Model: $DEFAULT_MODEL"
echo ""

# Disable Python bytecode cache to prevent stale imports
export PYTHONDONTWRITEBYTECODE=1

# Clear any existing cache before running
find "$SCRIPT_DIR" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find "$SCRIPT_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true

# Use virtual environment if it exists, otherwise use system python
if [ -f "$SCRIPT_DIR/venv/bin/python" ]; then
    "$SCRIPT_DIR/venv/bin/python" -B "$SCRIPT_DIR/TuivLLM.py"
else
    python -B "$SCRIPT_DIR/TuivLLM.py"
fi
