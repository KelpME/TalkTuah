# Model Switching Guide

## Overview

When you select a different model in the frontend settings, the system now automatically:
1. Updates the `.env` file with the new `DEFAULT_MODEL`
2. Restarts the vLLM container
3. Loads the new model (takes 30-60 seconds)

## How It Works

### Frontend Flow
```
User clicks model in settings
    ↓
Frontend calls /api/switch-model
    ↓
API updates .env file
    ↓
API restarts vLLM container
    ↓
vLLM loads new model
    ↓
User can chat with new model
```

### API Endpoint

**POST /api/switch-model**
- Parameters: `model_id` (e.g., "Qwen/Qwen2.5-1.5B-Instruct")
- Requires: Model must be downloaded first
- Action: Updates `.env` and restarts vLLM
- Response: Success message with timing info

## Usage

### Via Frontend
1. Open settings (in TUI)
2. Click on a different model in the "Model:" section
3. Wait for notification: "✓ Switched to {model}"
4. Wait 30-60 seconds for vLLM to restart
5. Start chatting with the new model

### Via API
```bash
curl -X POST \
  -H "Authorization: Bearer change-me" \
  "http://localhost:8787/api/switch-model?model_id=Qwen/Qwen2.5-1.5B-Instruct"
```

### Via Command Line
```bash
# Update .env
sed -i 's/DEFAULT_MODEL=.*/DEFAULT_MODEL=Qwen\/Qwen2.5-1.5B-Instruct/' .env

# Restart vLLM
docker compose restart vllm
```

## Important Notes

### Gated Models
Some models (like Gemma) require HuggingFace access approval:
- Visit the model page on HuggingFace
- Request access
- Add your `HF_TOKEN` to `.env`
- Wait for approval (can take hours/days)

### Restart Time
- Small models (1-3B): ~30 seconds
- Medium models (7-13B): ~60 seconds
- Large models (30B+): ~2-3 minutes

### Model Must Be Downloaded
The switch will fail if the model isn't in `./models/hub/`:
```json
{
  "detail": "Model not found: {model_id}. Please download it first."
}
```

Download first:
```bash
./scripts/download_model.sh {model_id}
```

## Troubleshooting

### Model Won't Load
**Check vLLM logs:**
```bash
docker logs vllm-server
```

**Common issues:**
- **Gated model**: Need HuggingFace access
- **Out of VRAM**: Model too large for GPU
- **Model not found**: Not downloaded yet

### Switch Fails
**Error: "Failed to restart vLLM"**
- Check Docker is running
- Check API has Docker socket access
- Check `.env` file permissions

### Wrong Model Still Loading
**Check .env:**
```bash
grep DEFAULT_MODEL .env
```

**Force restart:**
```bash
docker compose restart vllm
```

## Examples

### Switch to Qwen
```bash
curl -X POST -H "Authorization: Bearer change-me" \
  "http://localhost:8787/api/switch-model?model_id=Qwen/Qwen2.5-1.5B-Instruct"
```

### Check Current Model
```bash
curl -H "Authorization: Bearer change-me" \
  http://localhost:8787/api/models | jq '.data[].id'
```

### List Downloaded Models
```bash
curl -H "Authorization: Bearer change-me" \
  http://localhost:8787/api/model-status | jq '.downloaded_models'
```

## Technical Details

### Files Modified
- `.env` - `DEFAULT_MODEL` updated
- vLLM container - Restarted with new model

### Docker API
The API uses the Python Docker SDK to restart containers:
```python
import docker
client = docker.from_env()
container = client.containers.get("vllm-server")
container.restart()
```

### Requirements
- Docker socket mounted: `/var/run/docker.sock`
- Python package: `docker==7.1.0`
- API has write access to `.env`
