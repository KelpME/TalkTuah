"""Chat and models endpoints"""
import asyncio
import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse, JSONResponse

from config import settings
from models import ChatRequest
from auth import verify_token
from utils import stream_chat_response, request_with_retry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


# Rate limiter will be applied from main.py via app.state.limiter
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
        # Use retry utility with DNS refresh on connection errors
        timeout = settings.stream_timeout if is_streaming else settings.upstream_timeout
        upstream_response = await request_with_retry(
            method="POST",
            url=upstream_url,
            json=request_data,
            timeout=timeout,
            max_retries=10,
            retry_delay=4.0
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
