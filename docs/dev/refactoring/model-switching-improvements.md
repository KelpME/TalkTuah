# Model Switching Improvements

## Overview

Professional model switching implementation with real-time status updates and proper container orchestration.

## Architecture

### Backend API Endpoints

#### 1. `/api/switch-model` (POST)
**Purpose**: Switch to a different downloaded model

**Flow**:
1. Validates model exists in cache
2. Updates `.env` file with new model ID
3. Stops vLLM container
4. Recreates vLLM container with `--force-recreate` flag
5. Returns immediately with status "switching"

**Response**:
```json
{
  "status": "switching",
  "message": "Switching to Qwen/Qwen2.5-0.5B-Instruct",
  "model_id": "Qwen/Qwen2.5-0.5B-Instruct",
  "info": "vLLM is loading the new model. Check /api/model-loading-status for progress.",
  "estimated_time_seconds": 60
}
```

**Key Improvements**:
- ✅ Uses `docker compose` (modern syntax) instead of deprecated `docker-compose`
- ✅ Includes `--force-recreate` flag to ensure environment variables update
- ✅ Extended timeout to 120 seconds
- ✅ Returns immediately (doesn't wait for model to load)
- ✅ Doesn't restart itself (avoids connection loss)

#### 2. `/api/model-loading-status` (GET)
**Purpose**: Poll to check if vLLM is ready after a model switch

**Returns**:
- `status: "ready"` - vLLM is running and model is loaded
- `status: "loading"` - vLLM is running but model not loaded yet
- `status: "starting"` - vLLM container is still starting up

**Response Example**:
```json
{
  "status": "ready",
  "model_loaded": true,
  "current_model": "Qwen/Qwen2.5-0.5B-Instruct",
  "message": "vLLM is ready"
}
```

**Use Case**: Frontend polls this endpoint every 2-3 seconds during model switching to update status bar.

#### 3. `/api/restart-api` (POST)
**Purpose**: Restart API container to refresh DNS cache (optional)

**Flow**:
1. Schedules restart in background (2 second delay)
2. Returns immediately
3. API container restarts after response is sent

**When to Use**: If DNS resolution issues occur after vLLM restart (rare with modern Docker).

---

## Frontend Integration

### API Client Functions

Located in `/frontend/widgets/settings/api_client.py`:

```python
# Switch model
await switch_model(model_id)

# Poll for readiness
status = await fetch_model_loading_status()

# Optional: restart API for DNS refresh
await restart_api()
```

### Status Bar Integration

The status bar can show real-time model switching progress:

```python
# During switch
status_bar.status_text = "\n[yellow]● Loading model...[/yellow]"

# Poll every 2 seconds
status = await fetch_model_loading_status()

if status["status"] == "ready":
    status_bar.status_text = "\n[green]● Connected[/green]"
elif status["status"] == "loading":
    status_bar.status_text = "\n[yellow]● Loading model...[/yellow]"
elif status["status"] == "starting":
    status_bar.status_text = "\n[yellow]● Starting vLLM...[/yellow]"
```

---

## Recommended Frontend Flow

### Model Switch Workflow

```python
async def on_model_switch(self, model_id: str):
    """Handle model switching with status updates"""
    
    # 1. Initiate switch
    status_bar = self.query_one("#status-bar", StatusBar)
    status_bar.status_text = "\n[yellow]● Switching model...[/yellow]"
    
    try:
        # 2. Call switch endpoint
        result = await switch_model(model_id)
        
        # 3. Start polling for readiness
        max_attempts = 60  # 60 attempts * 2 seconds = 2 minutes max
        for attempt in range(max_attempts):
            await asyncio.sleep(2)
            
            status = await fetch_model_loading_status()
            
            if status["status"] == "ready":
                # Model loaded successfully
                status_bar.status_text = "\n[green]● Connected[/green]"
                self.notify("Model switched successfully!", severity="information")
                break
            elif status["status"] == "loading":
                status_bar.status_text = f"\n[yellow]● Loading {model_id}...[/yellow]"
            elif status["status"] == "starting":
                status_bar.status_text = "\n[yellow]● Starting vLLM...[/yellow]"
            else:
                # Error state
                status_bar.status_text = f"\n[red]● Error: {status.get('message', 'Unknown')}[/red]"
                break
        
        # Optional: Restart API for DNS refresh (usually not needed)
        # await restart_api()
        # await asyncio.sleep(3)  # Wait for API to restart
        
    except Exception as e:
        status_bar.status_text = f"\n[red]● Error: {str(e)}[/red]"
        self.notify(f"Failed to switch model: {str(e)}", severity="error")
```

---

## Benefits

### 1. **Professional UX**
- ✅ Immediate feedback on switch initiation
- ✅ Real-time progress updates
- ✅ Clear error messages
- ✅ No connection loss during switch

### 2. **Robust Error Handling**
- ✅ Timeout protection (2 minute max)
- ✅ Graceful degradation
- ✅ Clear error states

### 3. **Maintainable Code**
- ✅ Separation of concerns
- ✅ Testable endpoints
- ✅ Well-documented flow

### 4. **Scalable**
- ✅ Can add progress percentage later
- ✅ Can add model download progress
- ✅ Can add health metrics

---

## Technical Details

### Why No Self-Restart?

**Problem**: Original code tried to restart API container from within itself:
```python
api_container.restart(timeout=10)  # ❌ Kills the HTTP connection
```

**Solution**: Return response first, let frontend handle orchestration:
```python
return {"status": "switching", ...}  # ✅ Client gets response
# Frontend polls for readiness
```

### Why `--force-recreate`?

Docker's `up -d` doesn't always detect environment variable changes. The `--force-recreate` flag ensures:
- Container is fully recreated
- New environment variables are applied
- No stale configuration

### Why Modern `docker compose`?

The old `docker-compose` (with hyphen) is deprecated. Modern Docker uses:
```bash
docker compose up -d  # ✅ Modern
docker-compose up -d  # ❌ Deprecated
```

---

## Testing

### Manual Test

```bash
# 1. Start services
make up

# 2. Switch model via API
curl -X POST "http://localhost:8787/api/switch-model?model_id=Qwen/Qwen2.5-0.5B-Instruct" \
  -H "Authorization: Bearer my-secret-api-key-12345"

# 3. Poll status
while true; do
  curl -H "Authorization: Bearer my-secret-api-key-12345" \
    http://localhost:8787/api/model-loading-status | jq
  sleep 2
done
```

### Expected Output

```json
// Immediately after switch
{"status": "starting", "model_loaded": false, ...}

// After 10-20 seconds
{"status": "loading", "model_loaded": false, ...}

// After 30-60 seconds
{"status": "ready", "model_loaded": true, "current_model": "Qwen/Qwen2.5-0.5B-Instruct"}
```

---

## Next Steps

1. **Rebuild API container**:
   ```bash
   docker compose build api
   docker compose up -d --force-recreate api
   ```

2. **Integrate with frontend**: Add polling logic to settings modal

3. **Test model switching**: Verify status bar updates in real-time

4. **Optional**: Add progress percentage for large model loads
