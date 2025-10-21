from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    proxy_api_key: str = "change-me"
    upstream_base_url: str = "http://vllm:8000/v1"
    
    # CORS Configuration
    cors_origins: str = "*"
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    
    # Timeouts (seconds)
    upstream_timeout: int = 300
    stream_timeout: int = 600
    
    # Docker Container Names
    vllm_container_name: str = "vllm-server"
    api_container_name: str = "vllm-proxy-api"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()
