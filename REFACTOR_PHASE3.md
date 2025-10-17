# Phase 3: Eliminate Duplicate Logic

**Risk Level:** 🔴 HIGH  
**Estimated Time:** 2-3 hours  
**Can Break:** Download functionality, model management  
**Prerequisites:** Phase 1 & 2 complete

---

## Overview

Currently, the API calls shell scripts via subprocess for model downloads. This creates:
- **Tight coupling** between Python and Bash
- **Two sources of truth** for business logic
- **Difficulty testing** and error handling
- **No proper progress tracking** (uses text file)

### Current Duplicate Logic

| Function | API Implementation | Shell Script | Status |
|----------|-------------------|--------------|--------|
| Download model | Calls script via subprocess | `download_model.sh` | 🔴 Remove subprocess |
| Delete model | ❌ Missing | `delete_model.sh` | ➕ Create API endpoint |
| Progress tracking | Reads `/tmp/*.txt` | Writes `/tmp/*.txt` | 🔴 Use proper state |

### Goals

1. **Replace subprocess calls** with pure Python using `huggingface_hub`
2. **Add DELETE endpoint** for model deletion
3. **Proper state management** instead of temp files
4. **Keep scripts as optional CLI wrappers** (low priority)

---

## Step 1: Backup & Preparation

```bash
cd /home/tmo/Work/TalkTuah

git checkout -b refactor-phase3
git add -A
git commit -m "Before Phase 3: Eliminate duplicate logic"
git tag phase3-start
```

---

## Step 2: Add HuggingFace Hub Dependency

### 2.1 Update requirements.txt

```bash
echo "huggingface-hub==0.20.0" >> api/requirements.txt
```

**Full api/requirements.txt should now have:**
```
fastapi==0.115.0
uvicorn[standard]==0.32.0
httpx==0.27.2
pydantic==2.9.2
pydantic-settings==2.6.0
python-multipart==0.0.12
slowapi==0.1.9
docker==7.1.0
huggingface-hub==0.20.0
```

### 2.2 Verify Dockerfile already installs it

Check `api/Dockerfile` line 17:
```dockerfile
RUN pip install --no-cache-dir huggingface-hub[cli]
```

**This already exists!** We just need to import it in Python.

---

## Step 3: Rewrite DownloadService with Pure Python

### 3.1 Create new download implementation

**Backup current version:**
```bash
cp api/lib/downloads.py api/lib/downloads.py.backup
```

**Replace with new implementation:**

```bash
cat > api/lib/downloads.py << 'EOF'
"""Model download management with pure Python implementation"""
import os
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# HuggingFace Hub for downloads
try:
    from huggingface_hub import snapshot_download
    HF_HUB_AVAILABLE = True
except ImportError:
    HF_HUB_AVAILABLE = False
    logging.warning("huggingface_hub not available - downloads will not work")

logger = logging.getLogger(__name__)


class DownloadProgress:
    """Track download progress in memory"""
    
    def __init__(self):
        self.status: str = "idle"
        self.progress: int = 0
        self.model: Optional[str] = None
        self.error: Optional[str] = None
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "progress": self.progress,
            "model": self.model,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class DownloadService:
    """Manage model downloads using HuggingFace Hub"""
    
    def __init__(self):
        self.models_dir = Path("/workspace/models")
        self.cache_dir = self.models_dir / "hub"
        self.hf_token = os.getenv("HF_TOKEN")
        
        # In-memory progress tracking
        self._progress = DownloadProgress()
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current download progress from memory"""
        return self._progress.to_dict()
    
    def trigger_download(self, model_id: str, auto: bool = False) -> Dict[str, Any]:
        """
        Trigger model download.
        
        Args:
            model_id: HuggingFace model ID (org/model-name)
            auto: If True, trigger automated download (async)
        
        Returns:
            Status information or manual instructions
        """
        if not HF_HUB_AVAILABLE:
            raise RuntimeError(
                "huggingface_hub is not installed. "
                "Cannot download models. Please install: pip install huggingface-hub"
            )
        
        if auto:
            # Start async download
            asyncio.create_task(self._download_model_async(model_id))
            
            return {
                "status": "downloading",
                "message": f"Download started for {model_id}",
                "model_id": model_id,
                "info": "Check /api/download-progress for status updates."
            }
        else:
            return self._get_manual_instructions(model_id)
    
    async def _download_model_async(self, model_id: str):
        """Download model asynchronously using HuggingFace Hub"""
        logger.info(f"Starting download for model: {model_id}")
        
        # Initialize progress
        self._progress.status = "downloading"
        self._progress.progress = 0
        self._progress.model = model_id
        self._progress.error = None
        self._progress.started_at = datetime.now()
        self._progress.completed_at = None
        
        try:
            # Ensure cache directory exists
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Set HF_HOME environment variable
            os.environ["HF_HOME"] = str(self.models_dir)
            
            self._progress.progress = 10
            logger.info(f"Downloading model {model_id} to {self.cache_dir}")
            
            # Download using HuggingFace Hub
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._download_model_sync,
                model_id
            )
            
            self._progress.progress = 90
            logger.info(f"Download complete for {model_id}")
            
            # Update .env file
            self._update_env_file(model_id)
            
            self._progress.progress = 100
            self._progress.status = "complete"
            self._progress.completed_at = datetime.now()
            
            logger.info(f"Model {model_id} ready to use")
            
        except Exception as e:
            logger.error(f"Download failed for {model_id}: {e}", exc_info=True)
            self._progress.status = "error"
            self._progress.error = str(e)
            self._progress.progress = 0
    
    def _download_model_sync(self, model_id: str):
        """Synchronous download using snapshot_download"""
        snapshot_download(
            repo_id=model_id,
            cache_dir=str(self.cache_dir),
            token=self.hf_token,
            resume_download=True,
            local_files_only=False,
        )
    
    def _update_env_file(self, model_id: str):
        """Update DEFAULT_MODEL in .env file"""
        env_path = Path("/workspace/.env")
        
        if not env_path.exists():
            logger.warning(f".env file not found at {env_path}")
            return
        
        try:
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            # Update DEFAULT_MODEL line
            updated = False
            for i, line in enumerate(lines):
                if line.startswith('DEFAULT_MODEL='):
                    lines[i] = f'DEFAULT_MODEL={model_id}\n'
                    updated = True
                    break
            
            # If not found, append it
            if not updated:
                lines.append(f'DEFAULT_MODEL={model_id}\n')
            
            with open(env_path, 'w') as f:
                f.writelines(lines)
            
            logger.info(f"Updated DEFAULT_MODEL to: {model_id}")
        except Exception as e:
            logger.error(f"Failed to update .env: {e}")
    
    def _get_manual_instructions(self, model_id: str) -> Dict[str, Any]:
        """Get manual download instructions"""
        return {
            "status": "manual",
            "message": f"Manual download instructions for {model_id}",
            "model_id": model_id,
            "instructions": [
                f"Download model: {model_id}",
                "",
                "Option 1 - Use API:",
                f"  POST /api/download-model?model_id={model_id}&auto=true",
                "",
                "Option 2 - Python CLI:",
                f"  python -m huggingface_hub.commands.download {model_id}",
                "",
                "Option 3 - Shell script:",
                f"  ./scripts/management/download_model.sh {model_id}",
                "",
                "The model will be downloaded to: /workspace/models/hub/"
            ]
        }
    
    async def delete_model(self, model_id: str, force: bool = False) -> Dict[str, Any]:
        """
        Delete a downloaded model.
        
        Args:
            model_id: Model ID to delete (org/model-name)
            force: Skip safety checks
        
        Returns:
            Deletion status
        """
        # Convert model ID to directory name
        model_dir_name = "models--" + model_id.replace("/", "--")
        model_path = self.cache_dir / model_dir_name
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_id}")
        
        # Check if this is the current model (unless force=True)
        if not force:
            current_model = self._get_current_model_from_env()
            if current_model == model_id:
                raise ValueError(
                    f"Cannot delete current model: {model_id}. "
                    "Switch to a different model first or use force=true."
                )
        
        # Get size before deletion
        import shutil
        size = sum(f.stat().st_size for f in model_path.rglob('*') if f.is_file())
        size_mb = size / (1024 * 1024)
        
        # Delete directory
        try:
            shutil.rmtree(model_path)
            logger.info(f"Deleted model: {model_id} ({size_mb:.1f} MB)")
            
            return {
                "status": "deleted",
                "model_id": model_id,
                "size_mb": round(size_mb, 1),
                "message": f"Successfully deleted {model_id}"
            }
        except PermissionError:
            # Files may be owned by root from Docker
            raise PermissionError(
                f"Permission denied deleting {model_id}. "
                "Model files may be owned by root. Use: sudo rm -rf {model_path}"
            )
    
    def _get_current_model_from_env(self) -> Optional[str]:
        """Read current model from .env file"""
        env_path = Path("/workspace/.env")
        
        if not env_path.exists():
            return None
        
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    if line.startswith('DEFAULT_MODEL='):
                        return line.split('=', 1)[1].strip()
        except Exception as e:
            logger.error(f"Failed to read .env: {e}")
        
        return None
EOF
```

**Test import:**
```bash
python3 -c "from api.lib.downloads import DownloadService; print('✓ New DownloadService loads')"
```

---

## Step 4: Add Model Deletion Endpoint

### 4.1 Update routers/models.py

Add the DELETE endpoint to `api/routers/models.py`:

```bash
# Add this function to the end of api/routers/models.py
cat >> api/routers/models.py << 'EOF'


@router.delete("/delete-model")
async def delete_model(
    model_id: str,
    force: bool = False,
    token: str = Depends(verify_token),
    download_service: DownloadService = Depends(get_download_service)
):
    """
    Delete a downloaded model.
    
    Args:
        model_id: Model ID to delete (org/model-name)
        force: Skip safety checks (delete even if current model)
    
    **N8n HTTP Request:**
    ```
    Method: DELETE
    URL: http://localhost:8787/api/delete-model
    Query Parameters:
      - model_id: google/gemma-2-2b-it
      - force: false
    Headers:
      - Authorization: Bearer YOUR_API_KEY
    ```
    """
    try:
        return await download_service.delete_model(model_id, force=force)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete model: {str(e)}"
        )
EOF
```

### 4.2 Update root endpoint

Update the root endpoint in `api/routers/monitoring.py` to include the new endpoint:

```bash
# Update the root() function in api/routers/monitoring.py
# Add "delete_model": "/api/delete-model" to the endpoints dict
```

---

## Step 5: Remove Legacy Progress File Support

The new implementation uses in-memory state. We can remove the temp file dependency, but let's keep backward compatibility for now.

**Optional:** Add cleanup of old progress files in a migration function.

---

## Step 6: Update Docker for Better Permissions

Model files created by Python will have correct permissions. No changes needed to Dockerfile, but document this improvement.

---

## Step 7: Test New Implementation

### 7.1 Rebuild container

```bash
docker compose build api
docker compose up -d
```

### 7.2 Test download endpoint

```bash
# Test manual instructions
curl -s -X POST \
  "http://localhost:8787/api/download-model?model_id=google/gemma-2-2b-it&auto=false" \
  -H "Authorization: Bearer ${PROXY_API_KEY}" | jq .

# Test automated download (if you want to actually download)
curl -s -X POST \
  "http://localhost:8787/api/download-model?model_id=Qwen/Qwen2.5-1.5B-Instruct&auto=true" \
  -H "Authorization: Bearer ${PROXY_API_KEY}" | jq .
```

### 7.3 Monitor progress

```bash
# Poll progress endpoint
watch -n 2 'curl -s -H "Authorization: Bearer ${PROXY_API_KEY}" \
  http://localhost:8787/api/download-progress | jq .'
```

### 7.4 Test deletion

```bash
# Try to delete a model (not the current one)
curl -s -X DELETE \
  "http://localhost:8787/api/delete-model?model_id=OLD_MODEL&force=false" \
  -H "Authorization: Bearer ${PROXY_API_KEY}" | jq .
```

### 7.5 Test with N8n

Create an N8n workflow with HTTP Request node:

**Download:**
```
Method: POST
URL: http://localhost:8787/api/download-model
Query: model_id=Qwen/Qwen2.5-1.5B-Instruct&auto=true
Headers: Authorization: Bearer YOUR_KEY
```

**Check Progress:**
```
Method: GET
URL: http://localhost:8787/api/download-progress
Headers: Authorization: Bearer YOUR_KEY
```

**Delete:**
```
Method: DELETE
URL: http://localhost:8787/api/delete-model
Query: model_id=google/gemma-2-2b-it&force=false
Headers: Authorization: Bearer YOUR_KEY
```

---

## Step 8: (Optional) Convert Scripts to CLI Wrappers

**LOW PRIORITY** - Scripts can remain as-is or become thin wrappers that call the API.

Example `scripts/management/download_model_cli.sh`:
```bash
#!/bin/bash
MODEL_ID="$1"
API_KEY=$(grep PROXY_API_KEY .env | cut -d'=' -f2)

curl -X POST \
  "http://localhost:8787/api/download-model?model_id=${MODEL_ID}&auto=true" \
  -H "Authorization: Bearer ${API_KEY}"
```

**Decision:** Keep old scripts for now, document new API endpoints.

---

## Step 9: Update Documentation

Create `docs/api/model-management.md` documenting the new endpoints:

```bash
cat > docs/api/model-management.md << 'EOF'
# Model Management API

## Endpoints

### Download Model
```
POST /api/download-model?model_id={model_id}&auto={true|false}
```

### Check Download Progress
```
GET /api/download-progress
```

### Delete Model
```
DELETE /api/delete-model?model_id={model_id}&force={true|false}
```

## N8n Integration

All endpoints support Bearer token authentication and can be called from N8n HTTP Request nodes.

See REFACTOR_PHASE3.md for examples.
EOF
```

---

## Step 10: Commit Changes

```bash
git add -A
git commit -m "Phase 3: Eliminate duplicate logic - pure Python downloads, add delete endpoint"
git tag phase3-complete
```

---

## Rollback if Needed

```bash
# Restore backup
cp api/lib/downloads.py.backup api/lib/downloads.py

# Remove new endpoint
# Edit api/routers/models.py to remove delete_model function

# Rebuild
docker compose build api
docker compose restart api
```

---

## Validation Checklist

- [ ] `huggingface-hub` added to requirements.txt
- [ ] DownloadService rewritten with pure Python
- [ ] In-memory progress tracking works
- [ ] DELETE /api/delete-model endpoint added
- [ ] Docker builds successfully
- [ ] Download test works (progress updates)
- [ ] Delete test works (proper error handling)
- [ ] N8n can call all endpoints
- [ ] No subprocess calls remaining
- [ ] Documentation updated
- [ ] Changes committed
- [ ] Tag phase3-complete created

---

**Next:** Proceed to REFACTOR_PHASE4.md for frontend cleanup
