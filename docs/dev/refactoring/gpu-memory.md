# GPU Memory Configuration - Changes Summary

## Added Features

### 1. Dynamic GPU Memory Slider
- **File:** `frontend/widgets/settings/gpu_memory_slider.py`
- Interactive slider in TUI settings (10% - 95%)
- Arrow keys or drag to adjust
- Real-time visual feedback

### 2. Settings Integration
- **File:** `frontend/settings.py`
- Added `gpu_memory_utilization` setting (default: 0.75)
- Auto-saves to `~/.config/tuivllm/settings.json`

### 3. Settings Modal Integration
- **File:** `frontend/widgets/settings/settings_modal.py`
- GPU memory slider added below temperature slider
- Saves on settings exit

### 4. Docker Compose Support
- **File:** `docker-compose.yml`
- Changed hardcoded `0.75` to `${GPU_MEMORY_UTILIZATION:-0.75}`
- Environment variable driven

### 5. Settings Sync Script
- **File:** `scripts/sync_settings.py`
- Syncs TUI settings to `.env` file
- Updates `GPU_MEMORY_UTILIZATION` value

### 6. Makefile Commands
- **File:** `Makefile`
- `make sync-settings` - Sync TUI settings to .env
- `make apply` - Sync settings and restart vLLM

### 7. Documentation
- **File:** `docs/GPU_MEMORY.md`
- GPU memory configuration guide
- N8n integration examples
- Memory allocation recommendations

### 8. Updated Docs
- **File:** `README.md` - Added new commands and GPU memory docs link
- **File:** `docs/ROCM_SETUP.md` - Updated to reflect shared memory architecture (not capped at 16GB)

## Usage

### Via TUI
```bash
make frontend
# Press 's' for settings
# Adjust GPU Memory slider
# Exit to save
make apply  # Apply changes and restart
```

### Via .env
```bash
echo "GPU_MEMORY_UTILIZATION=0.90" >> .env
make restart
```

## Architecture

```
TUI Settings (JSON)
       ↓
sync_settings.py
       ↓
.env file
       ↓
docker-compose.yml
       ↓
vLLM --gpu-memory-utilization
```

## Notes

- Settings are modular and isolated
- No hard-coded limits
- Supports full 128GB addressable memory on AI Max+ 395
- All changes are non-destructive
