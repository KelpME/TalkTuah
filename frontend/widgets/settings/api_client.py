"""API client functions for settings"""

import httpx
from config import LMSTUDIO_URL, VLLM_API_KEY


async def fetch_downloaded_models(endpoint: str = LMSTUDIO_URL) -> list:
    """Fetch downloaded models from filesystem via API"""
    try:
        # Ensure we're using the correct path
        base_url = endpoint.rstrip('/')
        if not base_url.endswith('/api'):
            base_url = f"{base_url}/api"
        models_url = f"{base_url}/model-status"
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                models_url,
                headers={"Authorization": f"Bearer {VLLM_API_KEY}"}
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("downloaded_models", [])
    except Exception:
        pass
    return []


async def fetch_active_model(endpoint: str = LMSTUDIO_URL) -> str | None:
    """Get the currently active model from vLLM"""
    try:
        # Get currently loaded model from vLLM
        base_url = endpoint.rstrip('/')
        if not base_url.endswith('/api'):
            base_url = f"{base_url}/api"
        models_url = f"{base_url}/models"
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                models_url,
                headers={"Authorization": f"Bearer {VLLM_API_KEY}"}
            )
            if response.status_code == 200:
                data = response.json()
                models = data.get("data", [])
                if models:
                    model_id = models[0].get("id")
                    # If it's a path, extract the model name
                    # Format: /workspace/models/hub/models--org--name/snapshots/hash
                    if "models--" in model_id:
                        # Extract "models--org--name" part
                        import re
                        match = re.search(r'models--([^/]+)', model_id)
                        if match:
                            # Convert "org--name" to "org/name"
                            model_name = match.group(1).replace("--", "/")
                            return model_name
                    return model_id
    except Exception:
        pass
    return None


async def switch_model(model_id: str, endpoint: str = LMSTUDIO_URL) -> dict:
    """Switch to a different model"""
    switch_url = f"{endpoint}/switch-model"
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            switch_url,
            params={"model_id": model_id},
            headers={"Authorization": f"Bearer {VLLM_API_KEY}"}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            error_data = response.json()
            raise Exception(error_data.get('detail', 'Unknown error'))


async def download_model(model_id: str, endpoint: str = LMSTUDIO_URL) -> dict:
    """Start downloading a model"""
    download_url = f"{endpoint}/download-model"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            download_url,
            params={"model_id": model_id, "auto": "true"},
            headers={"Authorization": f"Bearer {VLLM_API_KEY}"}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed: {response.status_code}")


async def get_download_progress(endpoint: str = LMSTUDIO_URL) -> dict:
    """Fetch download progress"""
    try:
        progress_url = f"{endpoint}/download-progress"
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                progress_url,
                headers={"Authorization": f"Bearer {VLLM_API_KEY}"}
            )
            
            if response.status_code == 200:
                return response.json()
    except Exception:
        pass
    return {}


# Alias for consistency
async def fetch_download_progress(endpoint: str = LMSTUDIO_URL) -> dict:
    """Fetch download progress (alias for get_download_progress)"""
    return await get_download_progress(endpoint)


async def fetch_model_loading_status(endpoint: str = LMSTUDIO_URL) -> dict:
    """
    Check if vLLM is ready and which model is loaded.
    Returns: {"status": "ready"|"loading"|"starting", "model_loaded": bool, "current_model": str}
    """
    try:
        base_url = endpoint.rstrip('/')
        if not base_url.endswith('/api'):
            base_url = f"{base_url}/api"
        status_url = f"{base_url}/model-loading-status"
        
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(
                status_url,
                headers={"Authorization": f"Bearer {VLLM_API_KEY}"}
            )
            
            if response.status_code == 200:
                return response.json()
    except Exception:
        pass
    
    return {
        "status": "error",
        "model_loaded": False,
        "current_model": None,
        "message": "Failed to connect to API"
    }


async def restart_api(endpoint: str = LMSTUDIO_URL) -> dict:
    """
    Trigger API container restart (for DNS refresh).
    Returns immediately, restart happens in background.
    """
    try:
        base_url = endpoint.rstrip('/')
        if not base_url.endswith('/api'):
            base_url = f"{base_url}/api"
        restart_url = f"{base_url}/restart-api"
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                restart_url,
                headers={"Authorization": f"Bearer {VLLM_API_KEY}"}
            )
            
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
    return {"status": "error", "message": "Failed to restart API"}
