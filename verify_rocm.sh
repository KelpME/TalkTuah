#!/bin/bash
set -e

echo "=========================================="
echo "ROCm Setup Verification for TalkTuah"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass() {
    echo -e "${GREEN}✓${NC} $1"
}

fail() {
    echo -e "${RED}✗${NC} $1"
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check 1: ROCm installation
echo "1. Checking ROCm installation..."
if pacman -Q rocm-core &>/dev/null; then
    ROCM_VERSION=$(pacman -Q rocm-core | awk '{print $2}')
    pass "ROCm installed: $ROCM_VERSION"
else
    fail "ROCm not installed"
    echo "   Install with: sudo pacman -S rocm-hip-sdk rocm-opencl-runtime"
    exit 1
fi

# Check 2: GPU detection
echo ""
echo "2. Checking GPU..."
if /opt/rocm/bin/rocminfo 2>/dev/null | grep -q "gfx1151"; then
    pass "AMD GPU detected: gfx1151 (Radeon 8060S)"
else
    fail "GPU not detected or not gfx1151"
    echo "   Run: /opt/rocm/bin/rocminfo | grep gfx"
    exit 1
fi

# Check 3: User permissions
echo ""
echo "3. Checking user permissions..."
if groups | grep -q "video" && groups | grep -q "render"; then
    pass "User in video and render groups"
else
    fail "User not in required groups"
    echo "   Run: sudo usermod -aG video,render $USER"
    echo "   Then log out and back in"
    exit 1
fi

# Check 4: Device files
echo ""
echo "4. Checking device access..."
if [ -c /dev/kfd ] && [ -c /dev/dri/renderD128 ]; then
    pass "ROCm devices accessible"
    ls -l /dev/kfd /dev/dri/renderD128 | awk '{print "   " $0}'
else
    fail "ROCm devices not found"
    exit 1
fi

# Check 5: Docker
echo ""
echo "5. Checking Docker..."
if command -v docker &>/dev/null; then
    pass "Docker installed: $(docker --version | cut -d' ' -f3)"
else
    fail "Docker not installed"
    exit 1
fi

if docker ps &>/dev/null; then
    pass "Docker daemon running"
else
    fail "Docker daemon not accessible"
    echo "   Run: sudo systemctl start docker"
    exit 1
fi

# Check 6: Docker ROCm test
echo ""
echo "6. Testing ROCm in Docker..."
echo "   Pulling test image (this may take a moment)..."
if docker run --rm \
    --device=/dev/kfd \
    --device=/dev/dri \
    --group-add video \
    --group-add render \
    --security-opt seccomp=unconfined \
    rocm/pytorch:rocm6.2_ubuntu22.04_py3.10_pytorch_release_2.3.0 \
    bash -c "rocminfo 2>/dev/null | grep -q gfx1151" 2>/dev/null; then
    pass "ROCm working in Docker!"
else
    warn "ROCm test failed - this may be OK if image doesn't support gfx1151"
    echo "   The vLLM ROCm image may still work"
fi

# Check 7: .env file
echo ""
echo "7. Checking configuration..."
if [ -f .env ]; then
    pass ".env file exists"
    if grep -q "PROXY_API_KEY=change-me" .env; then
        warn "PROXY_API_KEY is still default - change it!"
    fi
    if grep -q "HF_TOKEN=hf_" .env; then
        pass "HuggingFace token configured"
    else
        warn "HF_TOKEN not configured"
    fi
    if grep -q "DEFAULT_MODEL=" .env && [ -n "$(grep DEFAULT_MODEL= .env | cut -d'=' -f2)" ]; then
        MODEL=$(grep DEFAULT_MODEL= .env | cut -d'=' -f2)
        pass "Model configured: $MODEL"
    else
        warn "No DEFAULT_MODEL set in .env"
    fi
else
    warn ".env file not found"
    echo "   Run: cp .env.example .env"
fi

echo ""
echo "=========================================="
echo "Summary"
echo "=========================================="
echo ""
echo "Your Ryzen AI Max+ 395 is ready for ROCm!"
echo ""
echo "Next steps:"
echo "  1. Configure .env if not done:"
echo "     cp .env.example .env"
echo "     nano .env  # Set PROXY_API_KEY and HF_TOKEN"
echo ""
echo "  2. Start with a small model for testing:"
echo "     echo 'DEFAULT_MODEL=Qwen/Qwen2.5-1.5B-Instruct' >> .env"
echo ""
echo "  3. Start services:"
echo "     make up"
echo ""
echo "  4. Watch logs:"
echo "     make logs"
echo ""
echo "  5. Launch TUI (after backend is ready):"
echo "     make frontend"
echo ""
echo "See docs/ROCM_SETUP.md for detailed info and troubleshooting."
echo ""
