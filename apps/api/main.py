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
# Note: We recreate this on DNS errors to force fresh resolution
http_client = httpx.AsyncClient(
    timeout=httpx.Timeout(settings.upstream_timeout, read=settings.stream_timeout),
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
)


async def get_fresh_client():
    """Create a fresh HTTP client to force DNS re-resolution"""
    # Force new connections by disabling keep-alive
    return httpx.AsyncClient(
        timeout=httpx.Timeout(settings.upstream_timeout, read=settings.stream_timeout),
        limits=httpx.Limits(max_keepalive_connections=0, max_connections=100),
        # Force HTTP/1.1 to ensure clean connection
        http1=True,
        http2=False
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
    
    # Default to streaming, but respect client's explicit choice
    request_data = chat_request.model_dump(exclude_none=True)
    # Use client's setting (now defaults to True from model)
    is_streaming = request_data.get("stream", True)
    
    # Log request parameters for debugging
    logger.info(f"[API Proxy] Temperature: {request_data.get('temperature')}, Model: {request_data.get('model')}, Stream: {is_streaming}")
    
    try:
        # Make request to vLLM (with DNS retry logic)
        import asyncio
        max_retries = 10  # Cover vLLM startup window (30-40s)
        retry_delay = 4  # seconds
        
        upstream_response = None
        last_error = None
        
        for attempt in range(max_retries):
            try:
                if attempt == 0:
                    # First attempt: use cached client with normal timeout
                    client_to_use = http_client
                    timeout = settings.stream_timeout if is_streaming else settings.upstream_timeout
                else:
                    # Retry attempts: create fresh client to force DNS re-resolution
                    logger.info(f"Attempt {attempt + 1}/{max_retries} - retrying with fresh DNS after {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                    client_to_use = await get_fresh_client()
                    # Use shorter timeout for retries (10s) to fail fast
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
                    # Close fresh client on error
                    try:
                        await client_to_use.aclose()
                    except:
                        pass
                
                if attempt == max_retries - 1:
                    # Last attempt failed
                    logger.error(f"All {max_retries} retry attempts failed. Last error: {err}")
                    raise
                # Continue to next retry
        
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


@app.get("/api/models")
async def list_models(token: str = Depends(verify_token)):
    """
    List available models from vLLM server.
    
    Proxies to /v1/models endpoint.
    """
    upstream_url = f"{settings.upstream_base_url}/models"
    
    try:
        # Try with cached client first
        try:
            response = await http_client.get(upstream_url)
        except httpx.ConnectError as dns_err:
            # DNS error - retry with fresh client
            logger.warning(f"DNS error fetching models, retrying: {dns_err}")
            fresh_client = await get_fresh_client()
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
            "model_loading_status": "/api/model-loading-status",
            "switch_model": "/api/switch-model",
            "restart_api": "/api/restart-api",
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
    Returns model availability status and currently loaded model from vLLM.
    """
    import os
    from pathlib import Path
    
    models_dir = Path("/workspace/models/hub")
    
    if not models_dir.exists():
        return {
            "models_available": False,
            "models_dir_exists": False,
            "downloaded_models": [],
            "current_model": None,
            "vllm_healthy": False,
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
    
    # Query vLLM for currently loaded model
    current_model = None
    vllm_healthy = False
    try:
        response = await http_client.get(
            f"{settings.upstream_base_url}/models",
            timeout=3.0
        )
        if response.status_code == 200:
            vllm_healthy = True
            data = response.json()
            models_list = data.get("data", [])
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
            # Use docker compose for entire operation to preserve network config
            logger.info("Stopping and recreating vLLM container...")
            
            # Use docker compose to stop, remove, and recreate in one operation
            # This ensures network configuration is preserved
            # CRITICAL: Use -p to specify project name to avoid wrong network creation
            logger.info("Recreating vLLM container with new model...")
            up_result = subprocess.run(
                ["docker", "compose", "-p", "talktuah", "up", "-d", "--force-recreate", "vllm"],
                cwd="/workspace",
                capture_output=True,
                text=True,
                timeout=120,
                env=os.environ.copy()
            )
            
            if up_result.returncode != 0:
                logger.error(f"docker compose stdout: {up_result.stdout}")
                logger.error(f"docker compose stderr: {up_result.stderr}")
                raise Exception(f"Docker compose up failed: {up_result.stderr}")
            
            logger.info(f"Successfully switched to model: {model_id}")
            
            # Schedule API restart to flush DNS cache
            # Restart immediately to clear DNS, then vLLM health will improve after its startup
            async def delayed_api_restart():
                """Restart API container to flush DNS cache after brief delay"""
                # Give vLLM time to start container and begin model loading
                # Don't wait too long - the restart itself will flush DNS
                await asyncio.sleep(15)  
                
                try:
                    restart_client = docker.from_env()
                    try:
                        api_container = restart_client.containers.get("vllm-proxy-api")
                        logger.info("Restarting API container to flush DNS cache...")
                        api_container.restart(timeout=10)
                        logger.info("API container restarted - DNS cache flushed")
                    finally:
                        restart_client.close()
                except Exception as e:
                    logger.error(f"Failed to restart API container: {e}")
            
            # Start the restart task in background
            asyncio.create_task(delayed_api_restart())
                
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
            "status": "switching",
            "message": f"Switching to {model_id}",
            "model_id": model_id,
            "info": "vLLM is loading the new model. Check /api/model-loading-status for progress.",
            "estimated_time_seconds": 60
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error switching model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to switch model: {str(e)}"
        )


@app.get("/api/model-loading-status")
async def model_loading_status(token: str = Depends(verify_token)):
    """
    Check if vLLM is ready and which model is loaded.
    Used by frontend to poll during model switching.
    """
    try:
        # Try to connect to vLLM
        models_response = await http_client.get(
            f"{settings.upstream_base_url}/models",
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


@app.post("/api/restart-api")
async def restart_api(token: str = Depends(verify_token)):
    """
    Restart the API container (for DNS refresh after vLLM restart).
    This endpoint schedules a restart and returns immediately.
    """
    async def delayed_api_restart():
        """Restart API container after vLLM stabilizes"""
        await asyncio.sleep(30)  # Wait for vLLM to fully initialize
        try:
            import docker
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
    asyncio.create_task(delayed_api_restart())
    
    return {
        "status": "restarting",
        "message": "API will restart in 2 seconds to refresh DNS cache",
        "info": "You may need to reconnect after restart"
    }


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
        
        logger.info(f"Starting automated download for model: {model_id}")
        script_path = "/workspace/scripts/management/download_model.sh"
        
        # Check if script exists
        if not os.path.exists(script_path):
            logger.error(f"Script not found: {script_path}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Download script not found at {script_path}. Run from host: ./scripts/management/download_model.sh"
            )
        
        logger.info(f"Script found at: {script_path}")
        try:
            # Start download in background using bash explicitly
            logger.info(f"Executing: bash {script_path} {model_id}")
            process = subprocess.Popen(
                ["bash", script_path, model_id],
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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to start download: {str(e)}"
            )
    else:
        # Return manual instructions
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
