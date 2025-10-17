"""Model download management with pure Python"""
import os
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Import huggingface_hub
try:
    from huggingface_hub import snapshot_download
    from huggingface_hub.utils import HfHubHTTPError
except ImportError:
    snapshot_download = None
    HfHubHTTPError = Exception
    logger.warning("huggingface_hub not available - downloads will fail")


class DownloadService:
    """Manage model downloads using pure Python"""
    
    def __init__(self):
        # Don't set cache_dir - let HF_HOME env var handle it
        # HF_HOME is set to /workspace/models, which creates hub/ subdirectory automatically
        self.hf_token = os.getenv("HF_TOKEN")
        self.models_hub_dir = Path("/workspace/models/hub")
        # In-memory progress tracking
        self._download_state: Dict[str, Dict[str, Any]] = {}
    
    def get_progress(self, model_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current download progress.
        
        Args:
            model_id: Optional model ID to check specific download
        
        Returns:
            Progress information
        """
        if model_id and model_id in self._download_state:
            return self._download_state[model_id]
        
        # Return most recent download state if no specific model requested
        if self._download_state:
            latest = max(
                self._download_state.items(),
                key=lambda x: x[1].get("started_at", 0)
            )
            return latest[1]
        
        return {
            "status": "idle",
            "progress": 0,
            "model": None
        }
    
    async def download_model(self, model_id: str) -> Dict[str, Any]:
        """
        Download a model from HuggingFace using pure Python.
        
        Args:
            model_id: HuggingFace model ID (org/model-name)
        
        Returns:
            Download status information
        """
        if snapshot_download is None:
            raise RuntimeError("huggingface_hub not available")
        
        logger.info(f"Starting download for model: {model_id}")
        
        # Initialize progress state
        self._download_state[model_id] = {
            "status": "downloading",
            "progress": 0,
            "model": model_id,
            "started_at": datetime.now().timestamp(),
            "error": None
        }
        
        try:
            # Download model in background task
            asyncio.create_task(self._download_in_background(model_id))
            
            return {
                "status": "downloading",
                "message": f"Download started for {model_id}",
                "model_id": model_id,
                "info": "Download in progress. Check /api/download-progress for status."
            }
        except Exception as e:
            logger.error(f"Failed to start download: {e}", exc_info=True)
            self._download_state[model_id] = {
                "status": "error",
                "progress": 0,
                "model": model_id,
                "error": str(e)
            }
            raise RuntimeError(f"Failed to start download: {str(e)}")
    
    async def _download_in_background(self, model_id: str):
        """Background task to download model"""
        try:
            # Update progress
            self._download_state[model_id]["progress"] = 10
            self._download_state[model_id]["status"] = "downloading"
            
            # Run download in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._download_sync,
                model_id
            )
            
            # Success
            self._download_state[model_id]["progress"] = 100
            self._download_state[model_id]["status"] = "complete"
            logger.info(f"Download complete: {model_id}")
            
        except HfHubHTTPError as e:
            error_msg = f"HuggingFace API error: {str(e)}"
            logger.error(error_msg)
            self._download_state[model_id]["status"] = "error"
            self._download_state[model_id]["error"] = error_msg
        except Exception as e:
            error_msg = f"Download failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self._download_state[model_id]["status"] = "error"
            self._download_state[model_id]["error"] = error_msg
    
    def _download_sync(self, model_id: str):
        """Synchronous download using huggingface_hub"""
        logger.info(f"Downloading {model_id} (using HF_HOME for cache location)")
        
        # Update progress
        self._download_state[model_id]["progress"] = 25
        
        # Download the model - don't pass cache_dir, use HF_HOME env var
        # This ensures models go to /workspace/models/hub/ automatically
        snapshot_download(
            repo_id=model_id,
            token=self.hf_token,
            resume_download=True,
            local_files_only=False,
        )
        
        # Update progress
        self._download_state[model_id]["progress"] = 90
        logger.info(f"Model {model_id} downloaded successfully")
    
    async def delete_model(self, model_id: str) -> Dict[str, Any]:
        """
        Delete a downloaded model.
        
        Args:
            model_id: HuggingFace model ID (org/model-name)
        
        Returns:
            Deletion status
        """
        import shutil
        
        # Convert model ID to cache directory name
        model_dir_name = "models--" + model_id.replace("/", "--")
        model_path = self.models_hub_dir / model_dir_name
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_id}")
        
        try:
            logger.info(f"Deleting model: {model_id} at {model_path}")
            shutil.rmtree(model_path)
            logger.info(f"Model deleted successfully: {model_id}")
            
            return {
                "status": "deleted",
                "message": f"Model {model_id} deleted successfully",
                "model_id": model_id
            }
        except Exception as e:
            logger.error(f"Failed to delete model: {e}", exc_info=True)
            raise RuntimeError(f"Failed to delete model: {str(e)}")
    
    def trigger_download(self, model_id: str, auto: bool = False) -> Dict[str, Any]:
        """
        Legacy method for backward compatibility.
        
        Now always uses pure Python download when auto=True.
        """
        if auto:
            # Create a task to download
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # This will be handled by the async download_model method
            return {
                "status": "downloading",
                "message": f"Download started for {model_id}",
                "model_id": model_id,
                "info": "Use the async download_model method instead"
            }
        else:
            return self._get_manual_instructions(model_id)
    
    def _get_manual_instructions(self, model_id: str) -> Dict[str, Any]:
        """Get manual download instructions"""
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
                "Or use auto=true to download via API:",
                "  POST /api/download-model?model_id={model_id}&auto=true"
            ]
        }
