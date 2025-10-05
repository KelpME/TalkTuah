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
            "health": "/api/healthz",
            "metrics": "/metrics"
        },
        "docs": "/docs"
    }
