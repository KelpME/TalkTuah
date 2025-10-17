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
            "delete_model": "/api/delete-model",
        },
        "docs": "/docs"
    }
