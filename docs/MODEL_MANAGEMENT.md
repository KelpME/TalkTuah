# Model Management Guide

## Overview

Models are now stored in the `./models` directory in your project root, making them:
- ✅ Accessible outside Docker containers
- ✅ Persistent across container restarts
- ✅ Easy to manage (view, delete, backup)
- ✅ Shared between vLLM and API containers

## Directory Structure

```
models/
├── hub/
│   ├── models--Qwen--Qwen2.5-1.5B-Instruct/  (2.9GB)
│   │   ├── blobs/
│   │   ├── refs/
│   │   └── snapshots/
│   └── models--{org}--{model-name}/
└── README.md
```

## Quick Commands

### Check Model Status
```bash
curl -H "Authorization: Bearer change-me" \
  http://localhost:8787/api/model-status | jq '.'
```

### Download a Model
```bash
./scripts/download_model.sh Qwen/Qwen2.5-1.5B-Instruct
```

This will:
1. Download the model to `./models/hub/`
2. Update `.env` with `DEFAULT_MODEL`
3. Restart vLLM automatically
4. Wait for vLLM to be ready

### List Downloaded Models
```bash
ls -lh ./models/hub/
```

### Check Model Size
```bash
du -sh ./models/hub/models--*
```

### Delete a Model
```bash
# Option 1: Via API
curl -X DELETE -H "Authorization: Bearer change-me" \
  "http://localhost:8787/api/delete-model?model_id=Qwen/Qwen2.5-1.5B-Instruct"

# Option 2: Manually (requires stopping vLLM first)
make down
rm -rf ./models/hub/models--Qwen--Qwen2.5-1.5B-Instruct
make up
```

## API Endpoints

### GET /api/model-status
Check if models are available and list downloaded models.

**Request:**
```bash
curl -H "Authorization: Bearer change-me" \
  http://localhost:8787/api/model-status
```

**Response:**
```json
{
  "models_available": true,
  "models_dir_exists": true,
  "downloaded_models": [
    "Qwen/Qwen2.5-1.5B-Instruct"
  ],
  "message": "Models found"
}
```

### POST /api/download-model
Download a model from HuggingFace.

**Request:**
```bash
curl -X POST -H "Authorization: Bearer change-me" \
  "http://localhost:8787/api/download-model?model_id=Qwen/Qwen2.5-1.5B-Instruct&auto=true"
```

### GET /api/download-progress
Check download progress.

**Request:**
```bash
curl -H "Authorization: Bearer change-me" \
  http://localhost:8787/api/download-progress
```

### DELETE /api/delete-model
Delete a downloaded model.

**Request:**
```bash
curl -X DELETE -H "Authorization: Bearer change-me" \
  "http://localhost:8787/api/delete-model?model_id=Qwen/Qwen2.5-1.5B-Instruct"
```

## Testing

Run the comprehensive test script:
```bash
./test_model_management.sh
```

This will verify:
- ✅ Services are running
- ✅ API endpoints are accessible
- ✅ Models directory exists
- ✅ Models are detected
- ✅ vLLM is healthy

## Troubleshooting

### Model not loading after download
```bash
# Check vLLM logs
docker logs vllm-server

# Verify model exists
ls -la ./models/hub/

# Restart vLLM
docker compose restart vllm
```

### Permission issues
```bash
# Fix permissions (if needed)
sudo chown -R $USER:$USER ./models/
```

### Model directory not found
```bash
# Recreate directory
mkdir -p ./models/hub

# Restart services
docker compose down
docker compose up -d
```

## Migration from Old System

If you had models in `~/.cache/huggingface/`, they won't be automatically migrated. You can:

1. **Option A**: Re-download (recommended)
   ```bash
   ./scripts/download_model.sh <model-id>
   ```

2. **Option B**: Copy manually
   ```bash
   cp -r ~/.cache/huggingface/hub/* ./models/hub/
   ```

## Configuration

The model directory is configured in `docker-compose.yml`:

```yaml
services:
  vllm:
    environment:
      - HF_HOME=/workspace/models
    volumes:
      - ./models:/workspace/models
```

## Benefits

### Before (Old System)
- ❌ Models in `~/.cache/huggingface/` (hidden)
- ❌ Required root access to manage
- ❌ Hard to find and delete
- ❌ Re-downloaded on container recreate

### After (New System)
- ✅ Models in `./models/` (visible)
- ✅ User-accessible without root
- ✅ Easy to manage from file system
- ✅ Persistent across container lifecycle

## Next Steps

The frontend can be updated to:
- Show a setup wizard when no models are detected
- Display model download progress
- Allow model selection and deletion from the UI

This is tracked in the pending task: "Update frontend to show settings/download UI when no model exists"
