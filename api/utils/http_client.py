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
