import pytest
import json
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient, api_url: str):
    """Test health check endpoint returns healthy status."""
    response = await client.get(f"{api_url}/api/healthz")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "status" in data
    assert "upstream_healthy" in data
    assert "model_loaded" in data
    assert "gpu_available" in data
    
    # After startup, these should be true
    assert data["upstream_healthy"] is True
    assert data["model_loaded"] is True


@pytest.mark.asyncio
async def test_list_models(client: AsyncClient, api_url: str, auth_headers: dict):
    """Test models endpoint returns at least one model."""
    response = await client.get(
        f"{api_url}/api/models",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "data" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) > 0
    
    # Check model structure
    model = data["data"][0]
    assert "id" in model
    assert "object" in model
    assert model["object"] == "model"


@pytest.mark.asyncio
async def test_chat_non_stream(
    client: AsyncClient,
    api_url: str,
    auth_headers: dict,
    model_name: str
):
    """Test non-streaming chat completion."""
    request_data = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": "Say 'Hello, World!' and nothing else."}
        ],
        "max_tokens": 50,
        "temperature": 0.1,
        "stream": False
    }
    
    response = await client.post(
        f"{api_url}/api/chat",
        headers=auth_headers,
        json=request_data,
        timeout=60.0
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Validate OpenAI response structure
    assert "id" in data
    assert "object" in data
    assert data["object"] == "chat.completion"
    assert "choices" in data
    assert len(data["choices"]) > 0
    
    choice = data["choices"][0]
    assert "message" in choice
    assert "content" in choice["message"]
    assert "role" in choice["message"]
    assert choice["message"]["role"] == "assistant"
    
    # Validate content is present
    content = choice["message"]["content"]
    assert len(content) > 0
    
    # Validate usage
    assert "usage" in data
    assert "prompt_tokens" in data["usage"]
    assert "completion_tokens" in data["usage"]
    assert "total_tokens" in data["usage"]
    
    # Check token limits
    assert data["usage"]["completion_tokens"] <= 50


@pytest.mark.asyncio
async def test_chat_stream(
    client: AsyncClient,
    api_url: str,
    auth_headers: dict,
    model_name: str
):
    """Test streaming chat completion."""
    request_data = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": "Count from 1 to 3."}
        ],
        "max_tokens": 50,
        "temperature": 0.1,
        "stream": True
    }
    
    headers = {**auth_headers, "Accept": "text/event-stream"}
    
    async with client.stream(
        "POST",
        f"{api_url}/api/chat",
        headers=headers,
        json=request_data,
        timeout=60.0
    ) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        
        chunks_received = 0
        done_received = False
        content_parts = []
        
        async for line in response.aiter_lines():
            if not line.strip():
                continue
            
            if line.startswith("data: "):
                data_str = line[6:]  # Remove "data: " prefix
                
                if data_str.strip() == "[DONE]":
                    done_received = True
                    break
                
                try:
                    chunk = json.loads(data_str)
                    chunks_received += 1
                    
                    # Validate chunk structure
                    assert "id" in chunk
                    assert "object" in chunk
                    assert chunk["object"] == "chat.completion.chunk"
                    assert "choices" in chunk
                    
                    if len(chunk["choices"]) > 0:
                        choice = chunk["choices"][0]
                        if "delta" in choice and "content" in choice["delta"]:
                            content_parts.append(choice["delta"]["content"])
                
                except json.JSONDecodeError:
                    pytest.fail(f"Invalid JSON in stream: {data_str}")
        
        # Validate streaming behavior
        assert chunks_received > 0, "Should receive at least one chunk"
        assert done_received, "Should receive [DONE] sentinel"
        
        # Validate accumulated content
        full_content = "".join(content_parts)
        assert len(full_content) > 0, "Should have received content"


@pytest.mark.asyncio
async def test_auth_missing_token(client: AsyncClient, api_url: str, model_name: str):
    """Test that requests without auth token are rejected."""
    request_data = {
        "model": model_name,
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": False
    }
    
    response = await client.post(
        f"{api_url}/api/chat",
        json=request_data
    )
    
    assert response.status_code == 403  # No auth header


@pytest.mark.asyncio
async def test_auth_invalid_token(client: AsyncClient, api_url: str, model_name: str):
    """Test that requests with invalid token are rejected."""
    request_data = {
        "model": model_name,
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": False
    }
    
    headers = {
        "Authorization": "Bearer invalid-token-12345",
        "Content-Type": "application/json"
    }
    
    response = await client.post(
        f"{api_url}/api/chat",
        headers=headers,
        json=request_data
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_models_auth_required(client: AsyncClient, api_url: str):
    """Test that models endpoint requires authentication."""
    response = await client.get(f"{api_url}/api/models")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_chat_with_parameters(
    client: AsyncClient,
    api_url: str,
    auth_headers: dict,
    model_name: str
):
    """Test chat with various parameters."""
    request_data = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2+2?"}
        ],
        "max_tokens": 100,
        "temperature": 0.7,
        "top_p": 0.9,
        "stop": ["\n\n"],
        "stream": False
    }
    
    response = await client.post(
        f"{api_url}/api/chat",
        headers=auth_headers,
        json=request_data,
        timeout=60.0
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "choices" in data
    assert len(data["choices"]) > 0
    assert "message" in data["choices"][0]
    assert "content" in data["choices"][0]["message"]
