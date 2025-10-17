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
