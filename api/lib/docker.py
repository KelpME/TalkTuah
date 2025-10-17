"""Docker container management"""
import asyncio
import logging
import subprocess
import os
from typing import Dict, Any

# Import docker at module level
try:
    import docker
except ImportError:
    docker = None
    logging.warning("docker module not available")

logger = logging.getLogger(__name__)


class DockerService:
    """Manage Docker container operations"""
    
    async def recreate_vllm_container(self) -> Dict[str, Any]:
        """
        Recreate vLLM container using docker compose.
        
        This preserves network configuration and picks up new environment variables.
        """
        try:
            logger.info("Recreating vLLM container...")
            
            result = subprocess.run(
                ["docker", "compose", "-p", "talktuah", "up", "-d", "--force-recreate", "vllm"],
                cwd="/workspace",
                capture_output=True,
                text=True,
                timeout=120,
                env=os.environ.copy()
            )
            
            if result.returncode != 0:
                logger.error(f"docker compose stdout: {result.stdout}")
                logger.error(f"docker compose stderr: {result.stderr}")
                raise Exception(f"Docker compose up failed: {result.stderr}")
            
            logger.info("Successfully recreated vLLM container")
            return {
                "success": True,
                "message": "vLLM container recreated"
            }
            
        except subprocess.TimeoutExpired as e:
            logger.error("Docker command timed out")
            raise Exception("Docker command timed out. Container may still be restarting.")
        except Exception as e:
            logger.error(f"Error during container recreation: {e}")
            raise
    
    async def restart_api_container_delayed(self, delay_seconds: int = 15):
        """
        Schedule a delayed restart of the API container.
        
        This is used to flush DNS cache after vLLM restarts.
        Creates a background task that doesn't block the response.
        """
        async def delayed_restart():
            """Restart API container after delay"""
            await asyncio.sleep(delay_seconds)
            
            try:
                if docker is None:
                    logger.error("docker module not available for restart")
                    return
                
                client = docker.from_env()
                try:
                    api_container = client.containers.get("vllm-proxy-api")
                    logger.info("Restarting API container to flush DNS cache...")
                    api_container.restart(timeout=10)
                    logger.info("API container restarted - DNS cache flushed")
                finally:
                    client.close()
            except Exception as e:
                logger.error(f"Failed to restart API container: {e}")
        
        # Start the restart task in background
        asyncio.create_task(delayed_restart())
        logger.info(f"Scheduled API restart in {delay_seconds} seconds")
    
    async def restart_api_container_manual(self, delay_seconds: int = 30):
        """
        Manually triggered API restart (for /api/restart-api endpoint).
        
        Schedules a delayed restart and returns immediately.
        """
        async def delayed_restart():
            """Restart API container after vLLM stabilizes"""
            await asyncio.sleep(delay_seconds)
            try:
                if docker is None:
                    logger.error("docker module not available for restart")
                    return
                
                client = docker.from_env()
                try:
                    api_container = client.containers.get("vllm-proxy-api")
                    logger.info("Restarting API container...")
                    api_container.restart(timeout=10)
                finally:
                    client.close()
            except Exception as e:
                logger.error(f"Failed to restart API container: {e}")
        
        # Schedule restart in background
        asyncio.create_task(delayed_restart())
        
        return {
            "status": "restarting",
            "message": f"API will restart in {delay_seconds} seconds to refresh DNS cache",
            "info": "You may need to reconnect after restart"
        }
