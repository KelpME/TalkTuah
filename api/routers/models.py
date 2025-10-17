"""Model management endpoints"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status

from auth import verify_token
from config import settings
from lib import ModelService, DownloadService, DockerService, VLLMService
from utils import get_http_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["models"])


# Singleton instances for stateful services
_download_service_instance = None


# Dependency functions
def get_model_service():
    return ModelService()


def get_download_service():
    """Get singleton DownloadService to preserve state across requests"""
    global _download_service_instance
    if _download_service_instance is None:
        _download_service_instance = DownloadService()
    return _download_service_instance


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
    
    If auto=true, triggers automated download using pure Python.
    Otherwise, returns manual instructions.
    """
    try:
        if auto:
            # Use new async download method
            return await download_service.download_model(model_id)
        else:
            # Return manual instructions
            return download_service.trigger_download(model_id, auto=False)
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


@router.delete("/delete-model")
async def delete_model(
    model_id: str,
    token: str = Depends(verify_token),
    download_service: DownloadService = Depends(get_download_service)
):
    """
    Delete a downloaded model.
    
    Args:
        model_id: HuggingFace model ID (org/model-name)
    
    Returns:
        Deletion status
    """
    try:
        return await download_service.delete_model(model_id)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
