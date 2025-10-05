# Quick Start Guide

Get vLLM Chat Backend running in 5 minutes.

## Prerequisites

1. **NVIDIA GPU** with 16GB+ VRAM
2. **Docker** with GPU support
3. **NVIDIA Container Toolkit**

Verify GPU access:

```bash
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

## Step 1: Configure

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

**Required changes:**

```bash
# Set a strong API key
PROXY_API_KEY=your-secret-key-here

# For Llama models, add HuggingFace token
HF_TOKEN=hf_your_token_here
```

## Step 2: Start Services

```bash
# Start vLLM + API
make up

# Follow logs (model loading takes 1-5 minutes)
make logs
```

Wait for:

```
vllm-server     | INFO:     Application startup complete.
vllm-proxy-api  | INFO:     Application startup complete.
```

## Step 3: Test

```bash
# Check health
curl http://localhost:8787/api/healthz

# List models
curl -H "Authorization: Bearer your-secret-key-here" \
     http://localhost:8787/api/models

# Chat (streaming)
curl -N -H "Authorization: Bearer your-secret-key-here" \
     -H "Content-Type: application/json" \
     -X POST http://localhost:8787/api/chat \
     -d '{
       "model": "meta-llama/Meta-Llama-3.1-8B-Instruct",
       "messages": [{"role": "user", "content": "Hello!"}]
     }'
```

## Step 4: Run Tests

```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Run tests
make test
```

## Step 5: Benchmark

```bash
# Install benchmark dependencies
pip install -r bench/requirements.txt

# Run benchmark
make bench
```

## Step 6: Use Terminal UI (Optional)

Launch the beautiful terminal chat interface:

```bash
# Install frontend dependencies
make install-frontend

# Run the TUI
make frontend
```

**Keyboard shortcuts:**
- `Enter` - Send message
- `Ctrl+L` - Clear chat
- `Ctrl+Q` - Quit
- `Ctrl+R` - Reconnect

## Next Steps

- Read [README.md](README.md) for full documentation
- Check [services/vllm/README.md](services/vllm/README.md) to switch models
- See [deploy/metrics/README.md](deploy/metrics/README.md) for monitoring

## Common Issues

### "Connection refused"

Model is still loading. Wait 1-5 minutes and check logs:

```bash
make logs
```

### "Out of memory"

Reduce context length in `.env`:

```bash
MAX_MODEL_LEN=4096
```

### "Invalid HF token"

Get token from https://huggingface.co/settings/tokens and add to `.env`:

```bash
HF_TOKEN=hf_your_token_here
```

## Stop Services

```bash
make down
```
