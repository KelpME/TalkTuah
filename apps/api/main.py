import httpx
import json
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import AsyncIterator
import logging

from config import settings
from models import ChatRequest, HealthResponse, ErrorResponse
from auth import verify_token

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

# HTTP client for upstream requests
http_client = httpx.AsyncClient(
    timeout=httpx.Timeout(settings.upstream_timeout, read=settings.stream_timeout),
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
)


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


@app.post("/api/chat")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def chat_completion(
    request: Request,
    chat_request: ChatRequest,
    token: str = Depends(verify_token)
):
    """
    Chat completion endpoint with streaming support.
    
    Translates requests to vLLM's /v1/chat/completions endpoint.
    Returns SSE stream by default (stream=true).
    """
    # Prepare upstream request
    upstream_url = f"{settings.upstream_base_url}/chat/completions"
    
    # Force streaming by default unless explicitly disabled
    request_data = chat_request.model_dump(exclude_none=True)
    if "stream" not in request_data:
        request_data["stream"] = True
    
    is_streaming = request_data.get("stream", True)
    
    try:
        # Make request to vLLM
        upstream_response = await http_client.post(
            upstream_url,
            json=request_data,
            timeout=settings.stream_timeout if is_streaming else settings.upstream_timeout,
        )
        
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


@app.get("/api/models")
async def list_models(token: str = Depends(verify_token)):
    """
    List available models from vLLM server.
    
    Proxies to /v1/models endpoint.
    """
    upstream_url = f"{settings.upstream_base_url}/models"
    
    try:
        response = await http_client.get(upstream_url)
        response.raise_for_status()
        return response.json()
    except httpx.RequestError as e:
        logger.error(f"Failed to fetch models: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch models from vLLM: {str(e)}"
        )


@app.get("/api/healthz", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Reports:
    - GPU availability (inferred from vLLM health)
    - Model loaded status
    - Upstream liveness
    - Queue size (if available)
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
        models_response = await http_client.get(
            f"{settings.upstream_base_url}/models",
            timeout=5.0
        )
        
        if models_response.status_code == 200:
            health_data["upstream_healthy"] = True
            models_data = models_response.json()
            
            # Check if models are loaded
            if models_data.get("data") and len(models_data["data"]) > 0:
                health_data["model_loaded"] = True
                health_data["gpu_available"] = True  # If model is loaded, GPU is available
                health_data["details"]["models"] = [m["id"] for m in models_data["data"]]
        
        # Try to get metrics for queue size (optional)
        try:
            metrics_response = await http_client.get(
                f"{settings.upstream_base_url.replace('/v1', '')}/metrics",
                timeout=2.0
            )
            if metrics_response.status_code == 200:
                # Parse Prometheus metrics for queue size
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


@app.get("/metrics")
async def metrics_proxy():
    """
    Proxy Prometheus metrics from vLLM server.
    
    Exposes vLLM's /metrics endpoint for Prometheus scraping.
    """
    try:
        metrics_url = f"{settings.upstream_base_url.replace('/v1', '')}/metrics"
        response = await http_client.get(metrics_url, timeout=5.0)
        response.raise_for_status()
        
        return StreamingResponse(
            iter([response.text]),
            media_type="text/plain; version=0.0.4"
        )
    except httpx.RequestError as e:
        logger.error(f"Failed to fetch metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch metrics from vLLM: {str(e)}"
        )


@app.on_event("shutdown")
async def shutdown_event():
    """Close HTTP client on shutdown."""
    await http_client.aclose()


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "vLLM Chat Proxy API",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/api/chat",
            "models": "/api/models",
            "model_status": "/api/model-status",
            "switch_model": "/api/switch-model",
            "health": "/api/healthz",
            "metrics": "/metrics",
            "download_model": "/api/download-model",
            "download_progress": "/api/download-progress",
            "delete_model": "/api/delete-model"
        },
        "docs": "/docs"
    }


@app.get("/api/model-status")
async def model_status(token: str = Depends(verify_token)):
    """
    Check if any models are downloaded and available.
    Returns model availability status.
    """
    import os
    from pathlib import Path
    
    models_dir = Path("/workspace/models/hub")
    
    if not models_dir.exists():
        return {
            "models_available": False,
            "models_dir_exists": False,
            "downloaded_models": [],
            "message": "Models directory not found. Please download a model first."
        }
    
    # Check for downloaded models
    downloaded_models = []
    if models_dir.exists():
        for item in models_dir.iterdir():
            if item.is_dir() and item.name.startswith("models--"):
                # Convert models--org--name to org/name
                model_name = item.name.replace("models--", "").replace("--", "/", 1)
                downloaded_models.append(model_name)
    
    return {
        "models_available": len(downloaded_models) > 0,
        "models_dir_exists": True,
        "downloaded_models": downloaded_models,
        "message": "Models found" if downloaded_models else "No models downloaded yet"
    }


@app.get("/api/download-progress")
async def download_progress(token: str = Depends(verify_token)):
    """Get current download progress"""
    import os
    
    progress_file = "/tmp/model_download_progress.txt"
    
    if not os.path.exists(progress_file):
        return {
            "status": "idle",
            "progress": 0,
            "model": None
        }
    
    try:
        with open(progress_file, 'r') as f:
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


@app.post("/api/switch-model")
async def switch_model(
    model_id: str,
    token: str = Depends(verify_token)
):
    """
    Switch to a different downloaded model.
    Updates .env and restarts vLLM.
    """
    import asyncio
    import os
    from pathlib import Path
    
    try:
        # Verify model exists
        cache_dir = Path("/workspace/models/hub")
        model_dir_name = "models--" + model_id.replace("/", "--")
        model_path = cache_dir / model_dir_name
        
        if not model_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model not found: {model_id}. Please download it first."
            )
        
        # Update .env file with HuggingFace model name format
        # vLLM will automatically find the model in the cache using HF_HOME
        env_path = "/workspace/.env"
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            # Update DEFAULT_MODEL line with HuggingFace format (org/model-name)
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
        
        # Recreate vLLM container to pick up new environment variables
        logger.info(f"Switching to model: {model_id}")
        import subprocess
        import os
        
        try:
            # Use docker API directly instead of docker-compose
            logger.info("Stopping and recreating vLLM container...")
            import docker
            
            client = docker.from_env()
            container = client.containers.get("vllm-server")
            
            # Stop the container
            logger.info("Stopping vLLM container...")
            container.stop(timeout=30)
            
            # Remove the container
            logger.info("Removing vLLM container...")
            container.remove(force=True)
            
            # Recreate using docker-compose (with hyphen)
            logger.info("Recreating vLLM container with new model...")
            up_result = subprocess.run(
                ["docker-compose", "up", "-d", "vllm"],
                cwd="/workspace",
                capture_output=True,
                text=True,
                timeout=60,
                env=os.environ.copy()
            )
            
            if up_result.returncode != 0:
                logger.error(f"docker-compose stdout: {up_result.stdout}")
                logger.error(f"docker-compose stderr: {up_result.stderr}")
                raise Exception(f"Docker compose up failed: {up_result.stderr}")
            
            logger.info(f"Successfully switched to model: {model_id}")
                
        except subprocess.TimeoutExpired:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Docker command timed out. The container may still be restarting."
            )
        except Exception as e:
            logger.error(f"Error during container recreation: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to restart vLLM: {str(e)}"
            )
        
        return {
            "status": "success",
            "message": f"Switched to {model_id}",
            "model_id": model_id,
            "info": "vLLM is restarting with the new model. This may take 30-60 seconds."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error switching model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to switch model: {str(e)}"
        )


@app.post("/api/download-model")
async def download_model(
    model_id: str,
    auto: bool = False,
    token: str = Depends(verify_token)
):
    """
    Download a model from HuggingFace.
    
    If auto=true, triggers automated download and restart.
    Otherwise, returns instructions.
    """
    if auto:
        # Trigger automated download
        import subprocess
        import os
        
        script_path = "/workspace/scripts/download_model.sh"
        
        # Check if script exists
        if not os.path.exists(script_path):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Download script not found. Run from host: ./scripts/download_model.sh"
            )
        
        try:
            # Start download in background
            subprocess.Popen(
                [script_path, model_id],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd="/workspace"
            )
            
            return {
                "status": "downloading",
                "message": f"Automated download started for {model_id}",
                "model_id": model_id,
                "info": "The system will download the model, update config, and restart vLLM automatically."
            }
        except Exception as e:
            logger.error(f"Failed to start automated download: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to start download: {str(e)}"
            )
    else:
        # Return manual instructions
        download_cmd = f"./scripts/download_model.sh {model_id}"
        
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
