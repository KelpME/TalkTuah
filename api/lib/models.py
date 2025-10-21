"""Model management operations"""
import os
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ModelService:
    """Handle model management operations"""
    
    def __init__(self, models_dir: str = "/workspace/models/hub"):
        self.models_dir = Path(models_dir)
        self.env_path = Path("/workspace/.env")
        # Simple TTL cache for model list (5 minutes)
        self._model_cache = None
        self._cache_timestamp = 0
        self._cache_ttl = 300  # 5 minutes in seconds
    
    def get_downloaded_models(self, use_cache: bool = True) -> List[str]:
        """
        Get list of downloaded models from HuggingFace cache.
        
        Uses 5-minute TTL cache to avoid repeated filesystem scans.
        
        Args:
            use_cache: If False, bypass cache and scan filesystem
        
        Returns list of model IDs in format: org/model-name
        """
        # Check cache
        if use_cache and self._model_cache is not None:
            cache_age = time.time() - self._cache_timestamp
            if cache_age < self._cache_ttl:
                logger.debug(f"Returning cached model list (age: {cache_age:.1f}s)")
                return self._model_cache
        
        # Cache miss - scan filesystem
        logger.debug("Scanning models directory...")
        downloaded_models = []
        
        if not self.models_dir.exists():
            return downloaded_models
        
        for item in self.models_dir.iterdir():
            if item.is_dir() and item.name.startswith("models--"):
                # Convert models--org--name to org/name
                model_name = item.name.replace("models--", "").replace("--", "/", 1)
                downloaded_models.append(model_name)
        
        # Update cache
        self._model_cache = downloaded_models
        self._cache_timestamp = time.time()
        
        return downloaded_models
    
    def invalidate_cache(self):
        """Invalidate model list cache (call after download/delete)"""
        self._model_cache = None
        self._cache_timestamp = 0
        logger.debug("Model cache invalidated")
    
    async def get_model_status(self, vllm_service) -> Dict[str, Any]:
        """
        Get comprehensive model status.
        
        Returns information about downloaded models, currently loaded model,
        and vLLM health status.
        """
        if not self.models_dir.exists():
            return {
                "models_available": False,
                "models_dir_exists": False,
                "downloaded_models": [],
                "current_model": None,
                "vllm_healthy": False,
                "message": "Models directory not found. Please download a model first."
            }
        
        # Get downloaded models
        downloaded_models = self.get_downloaded_models()
        
        # Query vLLM for currently loaded model
        current_model = None
        vllm_healthy = False
        try:
            models_data = await vllm_service.get_models()
            vllm_healthy = True
            models_list = models_data.get("data", [])
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
    
    def verify_model_exists(self, model_id: str) -> bool:
        """Check if a model is downloaded"""
        model_dir_name = "models--" + model_id.replace("/", "--")
        model_path = self.models_dir / model_dir_name
        return model_path.exists()
    
    def update_env_file(self, model_id: str):
        """
        Update DEFAULT_MODEL in .env file.
        
        Args:
            model_id: Model ID in format org/model-name
        """
        if not self.env_path.exists():
            logger.warning(f".env file not found at {self.env_path}")
            return
        
        with open(self.env_path, 'r') as f:
            lines = f.readlines()
        
        # Update DEFAULT_MODEL line
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('DEFAULT_MODEL='):
                lines[i] = f'DEFAULT_MODEL={model_id}\n'
                updated = True
                break
        
        # If not found, append it
        if not updated:
            lines.append(f'DEFAULT_MODEL={model_id}\n')
        
        with open(self.env_path, 'w') as f:
            f.writelines(lines)
        
        logger.info(f"Updated DEFAULT_MODEL to: {model_id}")
    
    async def switch_model(
        self,
        model_id: str,
        docker_service,
        vllm_service
    ) -> Dict[str, Any]:
        """
        Switch to a different downloaded model.
        
        This updates .env and recreates the vLLM container.
        """
        # Verify model exists
        if not self.verify_model_exists(model_id):
            raise ValueError(f"Model not found: {model_id}. Please download it first.")
        
        # Update .env file
        self.update_env_file(model_id)
        
        # Invalidate model cache since we're switching models
        self.invalidate_cache()
        
        # Recreate vLLM container
        await docker_service.recreate_vllm_container()
        
        # Schedule API restart to flush DNS cache
        await docker_service.restart_api_container_delayed(delay_seconds=1)
        
        return {
            "status": "switching",
            "message": f"Switching to {model_id}",
            "model_id": model_id,
            "info": "vLLM is loading the new model. Check /api/model-loading-status for progress.",
            "estimated_time_seconds": 60
        }
