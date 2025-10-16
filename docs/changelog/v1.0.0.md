# Model Management System - Changes Summary

## Overview
Complete overhaul of model storage and management to make models user-accessible and persistent.

## Changes Made

### 1. Model Storage Location
**Before:** `~/.cache/huggingface/hub` (hidden, root-owned in containers)
**After:** `./models/hub` (visible, user-accessible in project directory)

### 2. Files Created
- `models/.gitkeep` - Keeps models directory in git
- `models/README.md` - Documentation for models directory
- `docs/MODEL_MANAGEMENT.md` - Complete guide for model management
- `test_model_management.sh` - Automated testing script

### 3. Files Modified

#### `docker-compose.yml`
- Changed vLLM volume mount: `./models:/workspace/models`
- Added `HF_HOME=/workspace/models` environment variable
- Changed API volume mount: removed huggingface cache mount
- Added `MODELS_DIR=/workspace/models` to API environment
- Changed API dependency: `service_started` instead of `service_healthy` (faster startup)

#### `.gitignore`
- Added models directory exclusions:
  ```
  models/*
  !models/.gitkeep
  !models/README.md
  ```

#### `scripts/download_model.sh`
- Updated to use `./models` directory
- Sets `HF_HOME` to project models directory
- Updates `.env` instead of `docker-compose.yml`

#### `apps/api/main.py`
- Added `/api/model-status` endpoint - checks for downloaded models
- Updated `/api/delete-model` - uses new models path
- Updated root endpoint - includes all model management endpoints

#### `frontend/widgets/settings/model_list.py`
- Updated `scan_huggingface_cache()` - checks `./models/hub` first
- Added `refresh_models()` method - refreshes list after downloads

#### `frontend/widgets/settings/settings_modal.py`
- Added `refresh_model_lists()` method - refreshes both dropdowns
- Updated `poll_download_progress()` - calls refresh on completion

## New API Endpoints

### GET /api/model-status
Returns information about downloaded models.

**Response:**
```json
{
  "models_available": true,
  "models_dir_exists": true,
  "downloaded_models": ["Qwen/Qwen2.5-1.5B-Instruct"],
  "message": "Models found"
}
```

## Benefits

### User Experience
- ✅ Models visible in project directory
- ✅ Easy to delete: `rm -rf ./models/hub/models--*`
- ✅ Easy to backup: copy `./models/` directory
- ✅ No root access needed for management
- ✅ Model selector updates automatically after download

### Technical
- ✅ Persistent across container lifecycle
- ✅ No re-downloads on `docker compose down/up`
- ✅ Shared between vLLM and API containers
- ✅ Works with existing HuggingFace tools

## Testing

Run the test script:
```bash
./test_model_management.sh
```

Expected output:
- ✅ Services running
- ✅ API endpoints accessible
- ✅ Models detected in `./models/hub/`
- ✅ vLLM healthy with model loaded

## Migration

No automatic migration from old cache location. Options:

1. **Re-download (recommended):**
   ```bash
   ./scripts/download_model.sh Qwen/Qwen2.5-1.5B-Instruct
   ```

2. **Manual copy:**
   ```bash
   cp -r ~/.cache/huggingface/hub/* ./models/hub/
   ```

## Frontend Integration

The frontend now:
1. Scans `./models/hub/` for downloaded models
2. Polls download progress via `/api/download-progress`
3. Automatically refreshes model lists when download completes
4. Shows both available models (from vLLM) and downloaded models (from filesystem)

## Backwards Compatibility

The `model_list.py` widget checks both locations:
1. `./models/hub` (new location) - checked first
2. `~/.cache/huggingface/hub` (old location) - fallback

This ensures the system works even if models exist in the old location.
