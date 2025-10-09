# First-Time Setup Guide

## Overview

On first setup, you need to:
1. Download at least one model
2. Select which model to use as default
3. Start vLLM with that model

## Quick Start

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Edit .env and set your API key
nano .env  # Change PROXY_API_KEY

# 3. Download a model
./scripts/download_model.sh Qwen/Qwen2.5-1.5B-Instruct

# 4. Run setup to select default model
make setup

# 5. Start services
make up

# 6. Run frontend
make frontend
```

## Detailed Steps

### 1. Environment Configuration

```bash
cp .env.example .env
```

Edit `.env` and configure:
- `PROXY_API_KEY` - Your API authentication key
- `HF_TOKEN` - HuggingFace token (for gated models)
- `DEFAULT_MODEL` - Leave blank for first-time setup

### 2. Download Your First Model

Choose a model based on your GPU:

**Small Models (4-8GB VRAM):**
```bash
./scripts/download_model.sh Qwen/Qwen2.5-1.5B-Instruct
```

**Medium Models (12-16GB VRAM):**
```bash
./scripts/download_model.sh Qwen/Qwen2.5-3B-Instruct
```

**Large Models (24GB+ VRAM):**
```bash
./scripts/download_model.sh Qwen/Qwen2.5-7B-Instruct
```

### 3. Run Setup Script

```bash
make setup
```

Or directly:
```bash
./scripts/setup_first_model.sh
```

This will:
1. Scan `./models/hub/` for downloaded models
2. Show you a list to choose from
3. Update `.env` with your selection
4. Optionally start vLLM

**Example:**
```
Found 2 downloaded model(s):

  1. Qwen/Qwen2.5-1.5B-Instruct
  2. Qwen/Qwen2.5-3B-Instruct

Select a model (1-2): 1

Selected: Qwen/Qwen2.5-1.5B-Instruct

✓ Updated .env with DEFAULT_MODEL=Qwen/Qwen2.5-1.5B-Instruct

Start vLLM with this model now? (Y/n):
```

### 4. Start Services

```bash
make up
```

This starts:
- vLLM server (port 8000)
- API proxy (port 8787)

Wait 30-60 seconds for vLLM to load the model.

### 5. Verify Setup

```bash
# Check health
curl http://localhost:8787/api/healthz

# Check loaded model
curl -H "Authorization: Bearer your-api-key" \
  http://localhost:8787/api/models
```

### 6. Run Frontend

```bash
make install-frontend  # First time only
make frontend
```

## Changing Default Model

You can change the default model anytime:

**Option 1: Via Setup Script**
```bash
make setup
```

**Option 2: Via Frontend**
- Open settings
- Click on a different model
- System automatically switches

**Option 3: Manually**
```bash
# Edit .env
nano .env  # Change DEFAULT_MODEL

# Restart vLLM
docker compose restart vllm
```

## Troubleshooting

### No Models Found

```
No models found in ./models/hub
```

**Solution:** Download a model first:
```bash
./scripts/download_model.sh Qwen/Qwen2.5-1.5B-Instruct
```

### vLLM Won't Start

**Check logs:**
```bash
docker logs vllm-server
```

**Common issues:**
- **Gated model**: Need HuggingFace access
  - Visit model page on HuggingFace
  - Request access
  - Add `HF_TOKEN` to `.env`
  
- **Out of VRAM**: Model too large
  - Use a smaller model
  - Check GPU memory: `nvidia-smi`

- **Model not found**: Not downloaded
  - Download with `./scripts/download_model.sh`

### DEFAULT_MODEL is Blank

If `.env` has `DEFAULT_MODEL=` (blank), vLLM won't start.

**Solution:**
```bash
make setup
```

## Recommended Models

### For Testing (4-8GB VRAM)
- `Qwen/Qwen2.5-1.5B-Instruct` - Fast, small
- `Qwen/Qwen2.5-0.5B-Instruct` - Tiny, very fast

### For Production (12-16GB VRAM)
- `Qwen/Qwen2.5-3B-Instruct` - Good balance
- `Qwen/Qwen2.5-7B-Instruct` - Better quality

### Gated Models (Require Access)
- `meta-llama/Llama-3.2-1B-Instruct`
- `meta-llama/Llama-3.2-3B-Instruct`
- `google/gemma-2-2b-it`

## Next Steps

After setup:
1. **Test the API**: `curl http://localhost:8787/api/healthz`
2. **Run the frontend**: `make frontend`
3. **Download more models**: `./scripts/download_model.sh <model-id>`
4. **Switch models**: Open settings in frontend

## Files Created

- `.env` - Your configuration
- `./models/hub/` - Downloaded models
- `.env.bak` - Backup of previous .env

## Clean Start

To start over:
```bash
# Stop everything
make down

# Remove models
rm -rf ./models/hub/*

# Reset .env
cp .env.example .env

# Start fresh
make setup
```
