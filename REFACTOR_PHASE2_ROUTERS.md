# Phase 2 (Continued): Creating Routers

**This is a continuation of REFACTOR_PHASE2.md - Step 4**

---

## Step 4: Create Routers

### 4.1 Create routers/chat.py

**Source:** Lines 96-214, 216-245 in main.py

Create the chat endpoints router. This handles the primary chat completion and models listing endpoints.

**Note:** The rate limiter must be applied carefully - it references `app.state.limiter` which will be set in main.py.

```bash
cat > api/routers/chat.py << 'EOF'
"""Chat and models endpoints"""
import asyncio
import logging
from typing import AsyncIterator

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse, JSONResponse

from config import settings
from models import ChatRequest
from auth import verify_token
from utils import stream_chat_response, get_http_client, get_fresh_http_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat")
async def chat_completion(
    request: Request,
    chat_request: ChatRequest,
    token: str = Depends(verify_token)
):
    """
    Chat completion endpoint with streaming support.
    
    Translates requests to vLLM's /v1/chat/completions endpoint.
    Returns SSE stream by default (stream=true).
    
    Rate limited via app.state.limiter (applied in main.py).
    """
    # Prepare upstream request
    upstream_url = f"{settings.upstream_base_url}/chat/completions"
    
    request_data = chat_request.model_dump(exclude_none=True)
    is_streaming = request_data.get("stream", True)
    
    logger.info(
        f"[API Proxy] Temperature: {request_data.get('temperature')}, "
        f"Model: {request_data.get('model')}, Stream: {is_streaming}"
    )
    
    try:
        # Make request with retry logic
        max_retries = 10
        retry_delay = 4
        
        upstream_response = None
        last_error = None
        
        for attempt in range(max_retries):
            try:
                if attempt == 0:
                    # First attempt: use cached client
                    client_to_use = get_http_client()
                    timeout = settings.stream_timeout if is_streaming else settings.upstream_timeout
                else:
                    # Retry: fresh client for DNS refresh
                    logger.info(
                        f"Attempt {attempt + 1}/{max_retries} - "
                        f"retrying with fresh DNS after {retry_delay}s..."
                    )
                    await asyncio.sleep(retry_delay)
                    client_to_use = await get_fresh_http_client()
                    timeout = 10.0
                
                upstream_response = await client_to_use.post(
                    upstream_url,
                    json=request_data,
                    timeout=timeout,
                )
                
                # Close fresh client if we created one
                if attempt > 0:
                    await client_to_use.aclose()
                
                break  # Success - exit retry loop
                
            except (httpx.ConnectError, httpx.RemoteProtocolError, httpx.TimeoutException) as err:
                last_error = err
                if attempt > 0:
                    try:
                        await client_to_use.aclose()
                    except:
                        pass
                
                if attempt == max_retries - 1:
                    logger.error(f"All {max_retries} retry attempts failed. Last error: {err}")
                    raise
        
        if upstream_response is None:
            raise last_error or Exception("Failed to connect after retries")
        
        # Handle errors
        if upstream_response.status_code >= 400:
            error_detail = upstream_response.text
            try:
                error_json = upstream_response.json()
                error_detail = error_json.get("detail", error_detail)
            except:
                pass
            
            raise HTTPException(
                status_code=upstream_response.status_code,
                detail=f"Upstream error: {error_detail}"
            )
        
        # Stream response
        if is_streaming:
            return StreamingResponse(
                stream_chat_response(upstream_response),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                }
            )
        else:
            # Non-streaming response
            response_data = upstream_response.json()
            return JSONResponse(content=response_data)
            
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Request to vLLM server timed out"
        )
    except httpx.RequestError as e:
        logger.error(f"Request error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to connect to vLLM server: {str(e)}"
        )


@router.get("/models")
async def list_models(token: str = Depends(verify_token)):
    """
    List available models from vLLM server.
    
    Proxies to /v1/models endpoint.
    """
    upstream_url = f"{settings.upstream_base_url}/models"
    
    try:
        # Try with cached client first
        http_client = get_http_client()
        try:
            response = await http_client.get(upstream_url)
        except httpx.ConnectError as dns_err:
            # DNS error - retry with fresh client
            logger.warning(f"DNS error fetching models, retrying: {dns_err}")
            fresh_client = await get_fresh_http_client()
            try:
                response = await fresh_client.get(upstream_url)
            finally:
                await fresh_client.aclose()
        
        response.raise_for_status()
        return response.json()
    except httpx.RequestError as e:
        logger.error(f"Failed to fetch models: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch models from vLLM: {str(e)}"
        )
EOF
```

### 4.2 Create routers/models.py

**Source:** Lines 370-424, 427-464, 467-593, 596-638, 672-743 in main.py

```bash
cat > api/routers/models.py << 'EOF'
"""Model management endpoints"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status

from auth import verify_token
from config import settings
from lib import ModelService, DownloadService, DockerService, VLLMService
from utils import get_http_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["models"])


# Dependency functions
def get_model_service():
    return ModelService()


def get_download_service():
    return DownloadService()


def get_docker_service():
    return DockerService()


def get_vllm_service():
    http_client = get_http_client()
    return VLLMService(http_client, settings.upstream_base_url)


@router.get("/model-status")
async def model_status(
    token: str = Depends(verify_token),
    model_service: ModelService = Depends(get_model_service),
    vllm_service: VLLMService = Depends(get_vllm_service)
):
    """
    Check if any models are downloaded and available.
    Returns model availability status and currently loaded model from vLLM.
    """
    return await model_service.get_model_status(vllm_service)


@router.get("/download-progress")
async def download_progress(
    token: str = Depends(verify_token),
    download_service: DownloadService = Depends(get_download_service)
):
    """Get current download progress"""
    return download_service.get_progress()


@router.post("/switch-model")
async def switch_model(
    model_id: str,
    token: str = Depends(verify_token),
    model_service: ModelService = Depends(get_model_service),
    docker_service: DockerService = Depends(get_docker_service),
    vllm_service: VLLMService = Depends(get_vllm_service)
):
    """
    Switch to a different downloaded model.
    Updates .env and restarts vLLM.
    """
    try:
        return await model_service.switch_model(
            model_id,
            docker_service,
            vllm_service
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error switching model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to switch model: {str(e)}"
        )


@router.get("/model-loading-status")
async def model_loading_status(
    token: str = Depends(verify_token),
    vllm_service: VLLMService = Depends(get_vllm_service)
):
    """
    Check if vLLM is ready and which model is loaded.
    Used by frontend to poll during model switching.
    """
    return await vllm_service.get_loading_status()


@router.post("/download-model")
async def download_model(
    model_id: str,
    auto: bool = False,
    token: str = Depends(verify_token),
    download_service: DownloadService = Depends(get_download_service)
):
    """
    Download a model from HuggingFace.
    
    If auto=true, triggers automated download and restart.
    Otherwise, returns instructions.
    """
    try:
        return download_service.trigger_download(model_id, auto=auto)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
EOF
```

### 4.3 Create routers/monitoring.py

**Source:** Lines 248-314, 317-338, 641-669, 347-367 in main.py

```bash
cat > api/routers/monitoring.py << 'EOF'
"""Health, metrics, and system endpoints"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from config import settings
from models import HealthResponse
from auth import verify_token
from lib import VLLMService, DockerService
from utils import get_http_client
import httpx

logger = logging.getLogger(__name__)

router = APIRouter(tags=["monitoring"])


def get_vllm_service():
    http_client = get_http_client()
    return VLLMService(http_client, settings.upstream_base_url)


def get_docker_service():
    return DockerService()


@router.get("/api/healthz", response_model=HealthResponse)
async def health_check(vllm_service: VLLMService = Depends(get_vllm_service)):
    """
    Health check endpoint.
    
    Reports:
    - GPU availability (inferred from vLLM health)
    - Model loaded status
    - Upstream liveness
    - Queue size (if available)
    """
    return await vllm_service.get_health_status()


@router.get("/metrics")
async def metrics_proxy(vllm_service: VLLMService = Depends(get_vllm_service)):
    """
    Proxy Prometheus metrics from vLLM server.
    
    Exposes vLLM's /metrics endpoint for Prometheus scraping.
    """
    try:
        metrics_text = await vllm_service.get_metrics()
        return StreamingResponse(
            iter([metrics_text]),
            media_type="text/plain; version=0.0.4"
        )
    except httpx.RequestError as e:
        logger.error(f"Failed to fetch metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch metrics from vLLM: {str(e)}"
        )


@router.post("/api/restart-api")
async def restart_api(
    token: str = Depends(verify_token),
    docker_service: DockerService = Depends(get_docker_service)
):
    """
    Restart the API container (for DNS refresh after vLLM restart).
    This endpoint schedules a restart and returns immediately.
    """
    return await docker_service.restart_api_container_manual(delay_seconds=30)


@router.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "vLLM Chat Proxy API",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/api/chat",
            "models": "/api/models",
            "model_status": "/api/model-status",
            "model_loading_status": "/api/model-loading-status",
            "switch_model": "/api/switch-model",
            "restart_api": "/api/restart-api",
            "health": "/api/healthz",
            "metrics": "/metrics",
            "download_model": "/api/download-model",
            "download_progress": "/api/download-progress",
        },
        "docs": "/docs"
    }
EOF
```

### 4.4 Update routers/__init__.py

```bash
cat > api/routers/__init__.py << 'EOF'
"""API routers"""
from .chat import router as chat_router
from .models import router as models_router
from .monitoring import router as monitoring_router

__all__ = [
    "chat_router",
    "models_router",
    "monitoring_router",
]
EOF
```

**Test all router imports:**
```bash
python3 -c "from api.routers import chat_router, models_router, monitoring_router; print('✓ All router imports successful')"
```

---

## Step 5: Refactor main.py

Now reduce main.py to ~50 lines - just app initialization and router registration.

```bash
cat > api/main.py << 'EOF'
"""
vLLM Chat Proxy API

FastAPI proxy server for vLLM with authentication, rate limiting, and model management.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config import settings
from routers import chat_router, models_router, monitoring_router
from utils import close_http_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI app
app = FastAPI(
    title="vLLM Chat Proxy API",
    description="Proxy API for vLLM OpenAI-compatible server with authentication and streaming",
    version="1.0.0",
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(chat_router)
app.include_router(models_router)
app.include_router(monitoring_router)

# Apply rate limiting to chat endpoint
limiter.limit(f"{settings.rate_limit_per_minute}/minute")(chat_router.url_path_for)


@app.on_event("shutdown")
async def shutdown_event():
    """Close HTTP client on shutdown"""
    await close_http_client()
    logger.info("Shutdown complete")
EOF
```

**Verify line count:**
```bash
wc -l api/main.py
# Should be ~55 lines (down from 744!)
```

---

## Step 6: Test Refactored API

### 6.1 Rebuild container
```bash
cd /home/tmo/Work/TalkTuah
docker compose build api
```

**Watch for errors:**
- Import errors
- Missing modules
- Syntax errors

### 6.2 Start services
```bash
docker compose up -d
```

### 6.3 Check logs
```bash
# API logs
docker compose logs api

# Look for successful startup
docker compose logs api | grep "Application startup complete"
```

### 6.4 Test all endpoints

```bash
# Set API key
export PROXY_API_KEY=$(grep PROXY_API_KEY .env | cut -d'=' -f2)

# 1. Root endpoint
curl -s http://localhost:8787/ | jq .

# 2. Health check
curl -s http://localhost:8787/api/healthz | jq .

# 3. Models list
curl -s -H "Authorization: Bearer ${PROXY_API_KEY}" \
     http://localhost:8787/api/models | jq .

# 4. Model status
curl -s -H "Authorization: Bearer ${PROXY_API_KEY}" \
     http://localhost:8787/api/model-status | jq .

# 5. Model loading status
curl -s -H "Authorization: Bearer ${PROXY_API_KEY}" \
     http://localhost:8787/api/model-loading-status | jq .

# 6. Download progress
curl -s -H "Authorization: Bearer ${PROXY_API_KEY}" \
     http://localhost:8787/api/download-progress | jq .

# 7. Chat (non-streaming)
curl -s -X POST http://localhost:8787/api/chat \
     -H "Authorization: Bearer ${PROXY_API_KEY}" \
     -H "Content-Type: application/json" \
     -d '{
       "model": "test",
       "messages": [{"role": "user", "content": "Say hello"}],
       "stream": false,
       "temperature": 0.7
     }' | jq .

# 8. Metrics
curl -s http://localhost:8787/metrics | head -20
```

### 6.5 Compare with baseline

```bash
# Health
diff <(curl -s http://localhost:8787/api/healthz | jq -S .) \
     <(cat baseline_health.json | jq -S .)

# Models (if vLLM is running)
diff <(curl -s -H "Authorization: Bearer ${PROXY_API_KEY}" \
       http://localhost:8787/api/models | jq -S .) \
     <(cat baseline_models.json | jq -S .)
```

**Expected:** No functional differences, only possible formatting changes

---

## Step 7: Test Frontend Integration

```bash
cd /home/tmo/Work/TalkTuah/frontend
bash run.sh
```

**Test in TUI:**
1. Send a message - should get response
2. Check settings - model switching should work
3. Verify no errors in UI

---

## Step 8: Commit Changes

```bash
cd /home/tmo/Work/TalkTuah

git add -A
git commit -m "Phase 2: Refactor API - split main.py (744→55 lines) into modules"
git tag phase2-complete
```

---

## Rollback if Needed

```bash
# Restore backup
cp api/main.py.backup api/main.py

# Remove new modules
rm -rf api/routers api/lib api/utils

# Rebuild
docker compose build api
docker compose restart api
```

---

## Validation Checklist

- [ ] All directories created (routers/, lib/, utils/)
- [ ] All modules have __init__.py with proper exports
- [ ] main.py reduced to ~55 lines
- [ ] main.py.backup exists
- [ ] Docker build succeeds
- [ ] Services start without errors
- [ ] All 8 API endpoints respond correctly
- [ ] No import errors in logs
- [ ] No functional regressions vs baseline
- [ ] Frontend can connect and send messages
- [ ] Changes committed to git
- [ ] Tag phase2-complete created

---

**Next:** Proceed to REFACTOR_PHASE3.md to eliminate duplicate logic
