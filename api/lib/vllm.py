"""vLLM service operations"""
import logging
from typing import Dict, Any
import httpx

logger = logging.getLogger(__name__)


class VLLMService:
    """Handle vLLM server interactions"""
    
    def __init__(self, http_client: httpx.AsyncClient, base_url: str):
        self.http_client = http_client
        self.base_url = base_url
    
    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get comprehensive health status.
        
        Returns health data including GPU availability, model loaded status,
        upstream health, and queue size if available.
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
            models_response = await self.http_client.get(
                f"{self.base_url}/models",
                timeout=5.0
            )
            
            if models_response.status_code == 200:
                health_data["upstream_healthy"] = True
                models_data = models_response.json()
                
                # Check if models are loaded
                if models_data.get("data") and len(models_data["data"]) > 0:
                    health_data["model_loaded"] = True
                    health_data["gpu_available"] = True
                    health_data["details"]["models"] = [
                        m["id"] for m in models_data["data"]
                    ]
            
            # Try to get metrics for queue size (optional)
            try:
                metrics_response = await self.http_client.get(
                    f"{self.base_url.replace('/v1', '')}/metrics",
                    timeout=2.0
                )
                if metrics_response.status_code == 200:
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
    
    async def get_loading_status(self) -> Dict[str, Any]:
        """
        Check if vLLM is ready and which model is loaded.
        Used by frontend to poll during model switching.
        """
        try:
            models_response = await self.http_client.get(
                f"{self.base_url}/models",
                timeout=3.0
            )
            
            if models_response.status_code == 200:
                models_data = models_response.json()
                models = models_data.get("data", [])
                
                if models:
                    loaded_model = models[0].get("id", "unknown")
                    return {
                        "status": "ready",
                        "model_loaded": True,
                        "current_model": loaded_model,
                        "message": "vLLM is ready"
                    }
            
            # vLLM responded but no model loaded yet
            return {
                "status": "loading",
                "model_loaded": False,
                "current_model": None,
                "message": "vLLM is starting up..."
            }
            
        except Exception as e:
            # vLLM not responding - still starting
            return {
                "status": "starting",
                "model_loaded": False,
                "current_model": None,
                "message": "vLLM container is starting...",
                "error": str(e)
            }
    
    async def get_models(self) -> Dict[str, Any]:
        """Get list of available models from vLLM server"""
        response = await self.http_client.get(f"{self.base_url}/models")
        response.raise_for_status()
        return response.json()
    
    async def get_metrics(self) -> str:
        """Get Prometheus metrics from vLLM server"""
        metrics_url = f"{self.base_url.replace('/v1', '')}/metrics"
        response = await self.http_client.get(metrics_url, timeout=5.0)
        response.raise_for_status()
        return response.text
