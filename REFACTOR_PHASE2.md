# Phase 2: API Refactoring (main.py 744→50 lines)

**Risk Level:** 🟡 MEDIUM-HIGH  
**Estimated Time:** 3-4 hours  
**Can Break:** All API endpoints  
**Prerequisites:** Phase 1 complete, git backup

---

## Overview

Split monolithic `api/main.py` (744 lines) into organized modules:
- **utils/** - Pure utility functions (HTTP client, streaming)
- **lib/** - Business logic services (vLLM, Docker, models, downloads)
- **routers/** - API endpoint definitions  
- **main.py** - App initialization only (~50 lines)

### Module Structure
```
api/
├── main.py              # 50 lines - app init + router registration
├── config.py            # Existing - no changes
├── auth.py              # Existing - no changes
├── models.py            # Existing - no changes
├── routers/
│   ├── __init__.py
│   ├── chat.py          # ~120 lines: /api/chat, /api/models
│   ├── models.py        # ~200 lines: Model management endpoints
│   └── monitoring.py    # ~100 lines: Health, metrics, root
├── lib/
│   ├── __init__.py
│   ├── vllm.py          # ~80 lines: vLLM operations
│   ├── docker.py        # ~100 lines: Container operations
│   ├── models.py        # ~100 lines: Model file management
│   └── downloads.py     # ~80 lines: Download management
└── utils/
    ├── __init__.py
    ├── http_client.py   # ~80 lines: HTTP client + retry
    └── streaming.py     # ~40 lines: SSE streaming
```

---

## Pre-Flight Checks

### 1. Create backup
```bash
cd /home/tmo/Work/TalkTuah

git checkout -b refactor-phase2
git add -A
git commit -m "Before Phase 2: API refactoring"
git tag phase2-start
```

### 2. Backup main.py
```bash
cp api/main.py api/main.py.backup
```

### 3. Test baseline behavior
```bash
# Start services
docker compose up -d
sleep 30  # Wait for startup

# Test all endpoints
echo "Testing health..."
curl -s http://localhost:8787/api/healthz > baseline_health.json

echo "Testing models..."
curl -s -H "Authorization: Bearer ${PROXY_API_KEY}" \
     http://localhost:8787/api/models > baseline_models.json

echo "Testing model status..."
curl -s -H "Authorization: Bearer ${PROXY_API_KEY}" \
     http://localhost:8787/api/model-status > baseline_model_status.json

echo "✓ Baseline saved"
```

---

## Step 1: Create Directory Structure

```bash
cd /home/tmo/Work/TalkTuah/api

# Create directories
mkdir -p routers lib utils

# Create __init__.py files
touch routers/__init__.py
touch lib/__init__.py
touch utils/__init__.py
```

**Validation:**
```bash
ls -la routers/ lib/ utils/
# Each should show __init__.py
```

---

## Step 2: Extract Utils (Lowest Risk)

### 2.1 Create utils/streaming.py

**Source:** Lines 63-93 in main.py

```bash
cat > api/utils/streaming.py << 'EOF'
"""SSE streaming utilities for vLLM responses"""
import httpx
import json
import logging
from typing import AsyncIterator

logger = logging.getLogger(__name__)


async def stream_chat_response(upstream_response: httpx.Response) -> AsyncIterator[str]:
    """
    Stream SSE events from vLLM to client, preserving OpenAI format.
    
    Args:
        upstream_response: Response from vLLM server
        
    Yields:
        SSE-formatted chunks
    """
    try:
        async for line in upstream_response.aiter_lines():
            if not line.strip():
                continue
            
            # Forward SSE data lines as-is
            if line.startswith("data: "):
                yield f"{line}\n\n"
                
                # Check for [DONE] sentinel
                if line.strip() == "data: [DONE]":
                    break
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        error_event = {
            "error": str(e),
            "type": "stream_error"
        }
        yield f"data: {json.dumps(error_event)}\n\n"
    finally:
        await upstream_response.aclose()
EOF
```

**Test import:**
```bash
cd /home/tmo/Work/TalkTuah
python3 -c "from api.utils.streaming import stream_chat_response; print('✓ Import successful')"
```

### 2.2 Create utils/http_client.py

**Source:** Lines 45-48, 51-60, 122-172 in main.py

```bash
cat > api/utils/http_client.py << 'EOF'
"""HTTP client management with retry logic and DNS refresh"""
import httpx
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Global HTTP client instance
_http_client: Optional[httpx.AsyncClient] = None


def get_http_client() -> httpx.AsyncClient:
    """Get or create the shared HTTP client"""
    global _http_client
    
    if _http_client is None:
        from config import settings
        _http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                settings.upstream_timeout,
                read=settings.stream_timeout
            ),
            limits=httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100
            ),
        )
    return _http_client


async def get_fresh_http_client() -> httpx.AsyncClient:
    """Create a fresh HTTP client to force DNS re-resolution"""
    from config import settings
    
    return httpx.AsyncClient(
        timeout=httpx.Timeout(
            settings.upstream_timeout,
            read=settings.stream_timeout
        ),
        limits=httpx.Limits(
            max_keepalive_connections=0,
            max_connections=100
        ),
        http1=True,
        http2=False
    )


async def close_http_client():
    """Close the global HTTP client"""
    global _http_client
    
    if _http_client:
        await _http_client.aclose()
        _http_client = None
        logger.info("HTTP client closed")


async def request_with_retry(
    method: str,
    url: str,
    max_retries: int = 10,
    retry_delay: float = 4.0,
    **kwargs
) -> httpx.Response:
    """
    Make HTTP request with automatic retry and DNS refresh on connection errors.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        url: Request URL
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        **kwargs: Additional arguments for httpx request
    
    Returns:
        Response from successful request
    
    Raises:
        Last exception if all retries fail
    """
    last_error = None
    
    for attempt in range(max_retries):
        try:
            if attempt == 0:
                # First attempt: use cached client
                client = get_http_client()
                timeout = kwargs.get('timeout', None)
            else:
                # Retry: create fresh client for DNS refresh
                logger.info(
                    f"Attempt {attempt + 1}/{max_retries} - "
                    f"retrying with fresh DNS after {retry_delay}s..."
                )
                await asyncio.sleep(retry_delay)
                client = await get_fresh_http_client()
                # Use shorter timeout for retries
                timeout = 10.0
                kwargs['timeout'] = timeout
            
            # Make request
            response = await client.request(method, url, **kwargs)
            
            # Close fresh client if we created one
            if attempt > 0:
                await client.aclose()
            
            return response
            
        except (httpx.ConnectError, httpx.RemoteProtocolError, httpx.TimeoutException) as err:
            last_error = err
            
            # Close fresh client on error
            if attempt > 0:
                try:
                    await client.aclose()
                except:
                    pass
            
            if attempt == max_retries - 1:
                # Last attempt failed
                logger.error(
                    f"All {max_retries} retry attempts failed. "
                    f"Last error: {err}"
                )
                raise
    
    # Should never reach here, but just in case
    raise last_error or Exception("Failed to connect after retries")
EOF
```

**Test import:**
```bash
python3 -c "from api.utils.http_client import get_http_client; print('✓ Import successful')"
```

### 2.3 Update utils/__init__.py

```bash
cat > api/utils/__init__.py << 'EOF'
"""Utility functions and helpers"""
from .streaming import stream_chat_response
from .http_client import (
    get_http_client,
    get_fresh_http_client,
    close_http_client,
    request_with_retry
)

__all__ = [
    "stream_chat_response",
    "get_http_client",
    "get_fresh_http_client",
    "close_http_client",
    "request_with_retry",
]
EOF
```

**Test imports:**
```bash
python3 -c "from api.utils import stream_chat_response, get_http_client; print('✓ All utils imports successful')"
```

---

## Step 3: Extract Business Logic to lib/

### 3.1 Create lib/vllm.py

**Source:** Lines 248-314, 596-638 in main.py

```bash
cat > api/lib/vllm.py << 'EOF'
"""vLLM service operations"""
import logging
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)


class VLLMService:
    """Handle vLLM server interactions"""
    
    def __init__(self, http_client: httpx.AsyncClient, base_url: str):
        self.http_client = http_client
        self.base_url = base_url
    
    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get comprehensive health status.
        
        Returns health data including GPU availability, model loaded status,
        upstream health, and queue size if available.
        """
        health_data = {
            "status": "healthy",
            "gpu_available": False,
            "model_loaded": False,
            "upstream_healthy": False,
            "queue_size": None,
            "details": {}
        }
        
        try:
            # Check vLLM /v1/models endpoint
            models_response = await self.http_client.get(
                f"{self.base_url}/models",
                timeout=5.0
            )
            
            if models_response.status_code == 200:
                health_data["upstream_healthy"] = True
                models_data = models_response.json()
                
                # Check if models are loaded
                if models_data.get("data") and len(models_data["data"]) > 0:
                    health_data["model_loaded"] = True
                    health_data["gpu_available"] = True
                    health_data["details"]["models"] = [
                        m["id"] for m in models_data["data"]
                    ]
            
            # Try to get metrics for queue size (optional)
            try:
                metrics_response = await self.http_client.get(
                    f"{self.base_url.replace('/v1', '')}/metrics",
                    timeout=2.0
                )
                if metrics_response.status_code == 200:
                    metrics_text = metrics_response.text
                    for line in metrics_text.split("\n"):
                        if "vllm:num_requests_waiting" in line and not line.startswith("#"):
                            try:
                                health_data["queue_size"] = int(float(line.split()[-1]))
                            except:
                                pass
            except:
                pass  # Metrics are optional
                
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            health_data["status"] = "degraded"
            health_data["details"]["error"] = str(e)
        
        # Determine overall status
        if not health_data["upstream_healthy"]:
            health_data["status"] = "unhealthy"
        elif not health_data["model_loaded"]:
            health_data["status"] = "degraded"
        
        return health_data
    
    async def get_loading_status(self) -> Dict[str, Any]:
        """
        Check if vLLM is ready and which model is loaded.
        Used by frontend to poll during model switching.
        """
        try:
            models_response = await self.http_client.get(
                f"{self.base_url}/models",
                timeout=3.0
            )
            
            if models_response.status_code == 200:
                models_data = models_response.json()
                models = models_data.get("data", [])
                
                if models:
                    loaded_model = models[0].get("id", "unknown")
                    return {
                        "status": "ready",
                        "model_loaded": True,
                        "current_model": loaded_model,
                        "message": "vLLM is ready"
                    }
            
            # vLLM responded but no model loaded yet
            return {
                "status": "loading",
                "model_loaded": False,
                "current_model": None,
                "message": "vLLM is starting up..."
            }
            
        except Exception as e:
            # vLLM not responding - still starting
            return {
                "status": "starting",
                "model_loaded": False,
                "current_model": None,
                "message": "vLLM container is starting...",
                "error": str(e)
            }
    
    async def get_models(self) -> Dict[str, Any]:
        """Get list of available models from vLLM server"""
        response = await self.http_client.get(f"{self.base_url}/models")
        response.raise_for_status()
        return response.json()
    
    async def get_metrics(self) -> str:
        """Get Prometheus metrics from vLLM server"""
        metrics_url = f"{self.base_url.replace('/v1', '')}/metrics"
        response = await self.http_client.get(metrics_url, timeout=5.0)
        response.raise_for_status()
        return response.text
EOF
```

**Test:**
```bash
python3 -c "from api.lib.vllm import VLLMService; print('✓ VLLMService import successful')"
```

### 3.2 Create lib/docker.py

**Source:** Lines 519-576, 647-663 in main.py

```bash
cat > api/lib/docker.py << 'EOF'
"""Docker container management"""
import asyncio
import logging
import subprocess
import os
from typing import Dict, Any

# Import docker at module level (not in functions)
try:
    import docker
except ImportError:
    docker = None
    logging.warning("docker module not available")

logger = logging.getLogger(__name__)


class DockerService:
    """Manage Docker container operations"""
    
    async def recreate_vllm_container(self) -> Dict[str, Any]:
        """
        Recreate vLLM container using docker compose.
        
        This preserves network configuration and picks up new environment variables.
        """
        try:
            logger.info("Recreating vLLM container...")
            
            result = subprocess.run(
                ["docker", "compose", "-p", "talktuah", "up", "-d", "--force-recreate", "vllm"],
                cwd="/workspace",
                capture_output=True,
                text=True,
                timeout=120,
                env=os.environ.copy()
            )
            
            if result.returncode != 0:
                logger.error(f"docker compose stdout: {result.stdout}")
                logger.error(f"docker compose stderr: {result.stderr}")
                raise Exception(f"Docker compose up failed: {result.stderr}")
            
            logger.info("Successfully recreated vLLM container")
            return {
                "success": True,
                "message": "vLLM container recreated"
            }
            
        except subprocess.TimeoutExpired as e:
            logger.error("Docker command timed out")
            raise Exception("Docker command timed out. Container may still be restarting.")
        except Exception as e:
            logger.error(f"Error during container recreation: {e}")
            raise
    
    async def restart_api_container_delayed(self, delay_seconds: int = 15):
        """
        Schedule a delayed restart of the API container.
        
        This is used to flush DNS cache after vLLM restarts.
        Creates a background task that doesn't block the response.
        """
        async def delayed_restart():
            """Restart API container after delay"""
            await asyncio.sleep(delay_seconds)
            
            try:
                if docker is None:
                    logger.error("docker module not available for restart")
                    return
                
                client = docker.from_env()
                try:
                    api_container = client.containers.get("vllm-proxy-api")
                    logger.info("Restarting API container to flush DNS cache...")
                    api_container.restart(timeout=10)
                    logger.info("API container restarted - DNS cache flushed")
                finally:
                    client.close()
            except Exception as e:
                logger.error(f"Failed to restart API container: {e}")
        
        # Start the restart task in background
        asyncio.create_task(delayed_restart())
        logger.info(f"Scheduled API restart in {delay_seconds} seconds")
    
    async def restart_api_container_manual(self, delay_seconds: int = 30):
        """
        Manually triggered API restart (for /api/restart-api endpoint).
        
        Schedules a delayed restart and returns immediately.
        """
        async def delayed_restart():
            """Restart API container after vLLM stabilizes"""
            await asyncio.sleep(delay_seconds)
            try:
                if docker is None:
                    logger.error("docker module not available for restart")
                    return
                
                client = docker.from_env()
                try:
                    api_container = client.containers.get("vllm-proxy-api")
                    logger.info("Restarting API container...")
                    api_container.restart(timeout=10)
                finally:
                    client.close()
            except Exception as e:
                logger.error(f"Failed to restart API container: {e}")
        
        # Schedule restart in background
        asyncio.create_task(delayed_restart())
        
        return {
            "status": "restarting",
            "message": f"API will restart in {delay_seconds} seconds to refresh DNS cache",
            "info": "You may need to reconnect after restart"
        }
EOF
```

**Test:**
```bash
python3 -c "from api.lib.docker import DockerService; print('✓ DockerService import successful')"
```

### 3.3 Create lib/models.py

**Source:** Lines 370-424, 467-593 in main.py

```bash
cat > api/lib/models.py << 'EOF'
"""Model management operations"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ModelService:
    """Handle model management operations"""
    
    def __init__(self, models_dir: str = "/workspace/models/hub"):
        self.models_dir = Path(models_dir)
        self.env_path = Path("/workspace/.env")
    
    def get_downloaded_models(self) -> List[str]:
        """
        Get list of downloaded models from HuggingFace cache.
        
        Returns list of model IDs in format: org/model-name
        """
        downloaded_models = []
        
        if not self.models_dir.exists():
            return downloaded_models
        
        for item in self.models_dir.iterdir():
            if item.is_dir() and item.name.startswith("models--"):
                # Convert models--org--name to org/name
                model_name = item.name.replace("models--", "").replace("--", "/", 1)
                downloaded_models.append(model_name)
        
        return downloaded_models
    
    async def get_model_status(self, vllm_service) -> Dict[str, Any]:
        """
        Get comprehensive model status.
        
        Returns information about downloaded models, currently loaded model,
        and vLLM health status.
        """
        if not self.models_dir.exists():
            return {
                "models_available": False,
                "models_dir_exists": False,
                "downloaded_models": [],
                "current_model": None,
                "vllm_healthy": False,
                "message": "Models directory not found. Please download a model first."
            }
        
        # Get downloaded models
        downloaded_models = self.get_downloaded_models()
        
        # Query vLLM for currently loaded model
        current_model = None
        vllm_healthy = False
        try:
            models_data = await vllm_service.get_models()
            vllm_healthy = True
            models_list = models_data.get("data", [])
            if models_list and len(models_list) > 0:
                current_model = models_list[0].get("id")
        except Exception as e:
            logger.debug(f"Failed to query vLLM for current model: {e}")
        
        return {
            "models_available": len(downloaded_models) > 0,
            "models_dir_exists": True,
            "downloaded_models": downloaded_models,
            "current_model": current_model,
            "vllm_healthy": vllm_healthy,
            "message": "Models found" if downloaded_models else "No models downloaded yet"
        }
    
    def verify_model_exists(self, model_id: str) -> bool:
        """Check if a model is downloaded"""
        model_dir_name = "models--" + model_id.replace("/", "--")
        model_path = self.models_dir / model_dir_name
        return model_path.exists()
    
    def update_env_file(self, model_id: str):
        """
        Update DEFAULT_MODEL in .env file.
        
        Args:
            model_id: Model ID in format org/model-name
        """
        if not self.env_path.exists():
            logger.warning(f".env file not found at {self.env_path}")
            return
        
        with open(self.env_path, 'r') as f:
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
        
        with open(self.env_path, 'w') as f:
            f.writelines(lines)
        
        logger.info(f"Updated DEFAULT_MODEL to: {model_id}")
    
    async def switch_model(
        self,
        model_id: str,
        docker_service,
        vllm_service
    ) -> Dict[str, Any]:
        """
        Switch to a different downloaded model.
        
        This updates .env and recreates the vLLM container.
        """
        # Verify model exists
        if not self.verify_model_exists(model_id):
            raise ValueError(f"Model not found: {model_id}. Please download it first.")
        
        # Update .env file
        self.update_env_file(model_id)
        
        # Recreate vLLM container
        await docker_service.recreate_vllm_container()
        
        # Schedule API restart to flush DNS cache
        await docker_service.restart_api_container_delayed(delay_seconds=15)
        
        return {
            "status": "switching",
            "message": f"Switching to {model_id}",
            "model_id": model_id,
            "info": "vLLM is loading the new model. Check /api/model-loading-status for progress.",
            "estimated_time_seconds": 60
        }
EOF
```

**Test:**
```bash
python3 -c "from api.lib.models import ModelService; print('✓ ModelService import successful')"
```

### 3.4 Create lib/downloads.py

**Source:** Lines 427-464, 672-743 in main.py

```bash
cat > api/lib/downloads.py << 'EOF'
"""Model download management"""
import os
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


class DownloadService:
    """Manage model downloads"""
    
    def __init__(self):
        self.progress_file = Path("/tmp/model_download_progress.txt")
        self.script_path = Path("/workspace/scripts/management/download_model.sh")
    
    def get_progress(self) -> Dict[str, Any]:
        """
        Get current download progress.
        
        Reads progress from temporary file written by download script.
        """
        if not self.progress_file.exists():
            return {
                "status": "idle",
                "progress": 0,
                "model": None
            }
        
        try:
            with open(self.progress_file, 'r') as f:
                lines = f.readlines()
            
            data = {}
            for line in lines:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    data[key] = value
            
            return {
                "status": data.get('status', 'unknown'),
                "progress": int(data.get('progress', 0)),
                "model": data.get('model'),
                "error": data.get('error')
            }
        except Exception as e:
            logger.error(f"Failed to read progress: {e}")
            return {
                "status": "error",
                "progress": 0,
                "model": None,
                "error": str(e)
            }
    
    def trigger_download(self, model_id: str, auto: bool = False) -> Dict[str, Any]:
        """
        Trigger model download.
        
        Args:
            model_id: HuggingFace model ID (org/model-name)
            auto: If True, trigger automated download via subprocess
        
        Returns:
            Status information or manual instructions
        """
        if auto:
            return self._start_automated_download(model_id)
        else:
            return self._get_manual_instructions(model_id)
    
    def _start_automated_download(self, model_id: str) -> Dict[str, Any]:
        """Start automated download using shell script"""
        logger.info(f"Starting automated download for model: {model_id}")
        
        if not self.script_path.exists():
            logger.error(f"Script not found: {self.script_path}")
            raise FileNotFoundError(
                f"Download script not found at {self.script_path}. "
                f"Run from host: ./scripts/management/download_model.sh"
            )
        
        logger.info(f"Script found at: {self.script_path}")
        
        try:
            # Start download in background
            logger.info(f"Executing: bash {self.script_path} {model_id}")
            process = subprocess.Popen(
                ["bash", str(self.script_path), model_id],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd="/workspace",
                env=os.environ.copy()
            )
            logger.info(f"Process started with PID: {process.pid}")
            
            return {
                "status": "downloading",
                "message": f"Automated download started for {model_id}",
                "model_id": model_id,
                "info": "The system will download the model, update config, and restart vLLM automatically."
            }
        except Exception as e:
            logger.error(f"Failed to start automated download: {e}", exc_info=True)
            raise RuntimeError(f"Failed to start download: {str(e)}")
    
    def _get_manual_instructions(self, model_id: str) -> Dict[str, Any]:
        """Get manual download instructions"""
        download_cmd = f"./scripts/management/download_model.sh {model_id}"
        
        return {
            "status": "manual",
            "message": f"Manual download instructions for {model_id}",
            "model_id": model_id,
            "command": download_cmd,
            "instructions": [
                f"Run this command from the project root:",
                f"  {download_cmd}",
                "",
                "This will:",
                "  1. Download the model",
                "  2. Update docker-compose.yml",
                "  3. Restart vLLM automatically"
            ]
        }
EOF
```

**Test:**
```bash
python3 -c "from api.lib.downloads import DownloadService; print('✓ DownloadService import successful')"
```

### 3.5 Update lib/__init__.py

```bash
cat > api/lib/__init__.py << 'EOF'
"""Business logic services"""
from .vllm import VLLMService
from .docker import DockerService
from .models import ModelService
from .downloads import DownloadService

__all__ = [
    "VLLMService",
    "DockerService",
    "ModelService",
    "DownloadService",
]
EOF
```

**Test all lib imports:**
```bash
python3 -c "from api.lib import VLLMService, DockerService, ModelService, DownloadService; print('✓ All lib imports successful')"
```

---

## Step 4: Create Routers

**Note:** Continue in next file due to length...

This checklist is comprehensive and ready for use. Would you like me to:
1. Continue with creating Phase 2 routers section in a separate file?
2. Create Phase 3 and Phase 4 documents?
3. Make any adjustments to the current documentation?
