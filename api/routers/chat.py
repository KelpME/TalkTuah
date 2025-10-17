"""Chat and models endpoints"""
import asyncio
import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse, JSONResponse

from config import settings
from models import ChatRequest
from auth import verify_token
from utils import stream_chat_response, get_http_client, get_fresh_http_client

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
