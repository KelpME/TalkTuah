"""
vLLM Chat Proxy API

FastAPI proxy server for vLLM with authentication, rate limiting, and model management.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config import settings
from routers import chat_router, models_router, monitoring_router
from utils import close_http_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI app
app = FastAPI(
    title="vLLM Chat Proxy API",
    description="Proxy API for vLLM OpenAI-compatible server with authentication and streaming",
    version="1.0.0",
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers  
app.include_router(chat_router)
app.include_router(models_router)
app.include_router(monitoring_router)


@app.on_event("shutdown")
async def shutdown_event():
    """Close HTTP client on shutdown"""
    await close_http_client()
    logger.info("Shutdown complete")
