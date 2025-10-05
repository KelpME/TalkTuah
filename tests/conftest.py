import pytest
import os
from httpx import AsyncClient

# Test configuration
TEST_API_URL = os.getenv("TEST_API_URL", "http://localhost:8787")
TEST_API_KEY = os.getenv("PROXY_API_KEY", "change-me")
TEST_MODEL = os.getenv("DEFAULT_MODEL", "meta-llama/Meta-Llama-3.1-8B-Instruct")


@pytest.fixture
def api_url():
    """Base API URL for tests."""
    return TEST_API_URL


@pytest.fixture
def api_key():
    """API key for authentication."""
    return TEST_API_KEY


@pytest.fixture
def model_name():
    """Default model name for tests."""
    return TEST_MODEL


@pytest.fixture
def auth_headers(api_key):
    """Authentication headers."""
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }


@pytest.fixture
async def client():
    """Async HTTP client for tests."""
    async with AsyncClient(timeout=60.0) as client:
        yield client
