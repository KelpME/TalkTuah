#!/bin/bash
# Verification script for vLLM Chat Backend setup

set -e

echo "======================================================================"
echo "vLLM Chat Backend - Setup Verification"
echo "======================================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check functions
check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# 1. Check Docker
echo "1. Checking Docker..."
if command -v docker &> /dev/null; then
    check_pass "Docker is installed"
    if docker ps &> /dev/null; then
        check_pass "Docker daemon is running"
    else
        check_fail "Docker daemon is not running"
        exit 1
    fi
else
    check_fail "Docker is not installed"
    exit 1
fi
echo ""

# 2. Check Docker Compose
echo "2. Checking Docker Compose..."
if docker compose version &> /dev/null; then
    check_pass "Docker Compose is installed"
else
    check_fail "Docker Compose is not installed"
    exit 1
fi
echo ""

# 3. Check NVIDIA GPU
echo "3. Checking NVIDIA GPU..."
if command -v nvidia-smi &> /dev/null; then
    check_pass "nvidia-smi is available"
    if nvidia-smi &> /dev/null; then
        GPU_COUNT=$(nvidia-smi --list-gpus | wc -l)
        GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -n1)
        check_pass "GPU detected: $GPU_NAME"
        check_pass "GPU count: $GPU_COUNT"
    else
        check_fail "nvidia-smi failed to run"
        exit 1
    fi
else
    check_fail "nvidia-smi not found"
    exit 1
fi
echo ""

# 4. Check .env file
echo "4. Checking configuration..."
if [ -f ".env" ]; then
    check_pass ".env file exists"
    
    if grep -q "PROXY_API_KEY=change-me" .env; then
        check_warn "PROXY_API_KEY is still set to default 'change-me'"
        echo "   Consider changing it for security"
    else
        check_pass "PROXY_API_KEY is customized"
    fi
    
    if grep -q "HF_TOKEN=" .env && ! grep -q "HF_TOKEN=$" .env; then
        check_pass "HF_TOKEN is set"
    else
        check_warn "HF_TOKEN is not set (required for Llama models)"
    fi
else
    check_warn ".env file not found"
    echo "   Run: cp .env.example .env"
fi
echo ""

# 5. Check if services are running
echo "5. Checking services..."
if docker compose ps | grep -q "vllm.*running"; then
    check_pass "vLLM service is running"
else
    check_warn "vLLM service is not running"
    echo "   Run: make up"
fi

if docker compose ps | grep -q "api.*running"; then
    check_pass "API service is running"
else
    check_warn "API service is not running"
    echo "   Run: make up"
fi
echo ""

# 6. Check API health
echo "6. Checking API health..."
if curl -s -f http://localhost:8787/api/healthz > /dev/null 2>&1; then
    check_pass "API is responding"
    
    HEALTH=$(curl -s http://localhost:8787/api/healthz)
    if echo "$HEALTH" | grep -q '"status":"healthy"'; then
        check_pass "API status is healthy"
    else
        check_warn "API status is not healthy"
        echo "   Check logs: make logs"
    fi
    
    if echo "$HEALTH" | grep -q '"model_loaded":true'; then
        check_pass "Model is loaded"
    else
        check_warn "Model is not loaded yet"
        echo "   Wait a few minutes for model to load"
    fi
else
    check_warn "API is not responding"
    echo "   Ensure services are running: make up"
fi
echo ""

# 7. Check Python for frontend
echo "7. Checking Python environment..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    check_pass "Python is installed: $PYTHON_VERSION"
    
    if [ -f "frontend/requirements.txt" ]; then
        if python3 -c "import textual" 2>/dev/null; then
            check_pass "Frontend dependencies are installed"
        else
            check_warn "Frontend dependencies not installed"
            echo "   Run: make install-frontend"
        fi
    fi
else
    check_warn "Python3 is not installed"
    echo "   Frontend requires Python 3.11+"
fi
echo ""

# 8. Summary
echo "======================================================================"
echo "Summary"
echo "======================================================================"
echo ""

if docker compose ps | grep -q "vllm.*running" && docker compose ps | grep -q "api.*running"; then
    echo -e "${GREEN}Backend is running!${NC}"
    echo ""
    echo "Try these commands:"
    echo "  curl http://localhost:8787/api/healthz"
    echo "  make logs"
    echo "  make test"
    echo "  make frontend"
else
    echo -e "${YELLOW}Backend is not running.${NC}"
    echo ""
    echo "Start with:"
    echo "  make up"
    echo "  make logs  # Wait for model to load"
fi

echo ""
echo "Documentation:"
echo "  README.md           - Full documentation"
echo "  QUICKSTART.md       - Quick start guide"
echo "  INTEGRATION_SUMMARY.md - Frontend integration details"
echo ""
echo "======================================================================"
