"""
LLM API Client

Handles communication with the vLLM Proxy API including:
- Chat completions
- Model queries
- Settings integration
- Error handling

Moved from llm_client.py during Phase 4 refactoring.
"""

import httpx
from typing import List, Dict, Optional
import json
from config import (
    VLLM_API_URL, VLLM_API_KEY, VLLM_MODEL,
    LMSTUDIO_TIMEOUT, LMSTUDIO_MAX_TOKENS, 
    LMSTUDIO_TEMPERATURE, LLM_SYSTEM_PROMPT
)
from settings import get_settings


class LLMClient:
    """Client for interacting with vLLM Proxy API"""
    
    def __init__(self, base_url: str = None, api_key: str = VLLM_API_KEY):
        # Read endpoint and model from settings if not provided
        if base_url is None:
            from settings import get_settings
            settings = get_settings()
            base_url = settings.get("endpoint", VLLM_API_URL)
            # Use selected model from settings, or default from config
            selected_model = settings.get("selected_model")
            self.model = selected_model if selected_model else VLLM_MODEL
        else:
            self.model = VLLM_MODEL
        
        self.base_url = base_url
        self.api_key = api_key
        self.conversation_history: List[Dict[str, str]] = []
        self.system_prompt = LLM_SYSTEM_PROMPT
    
    async def get_current_model(self) -> str:
        """Fetch the currently loaded model from the API"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("data", [])
                    if models:
                        return models[0].get("id", self.model)
        except:
            pass
        return self.model
    
    async def get_response(self, user_message: str, analytics_context: str = "") -> str:
        """Get a response from the LLM"""
        
        # Get the current model dynamically
        current_model = await self.get_current_model()
        
        # Build the messages
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # Add analytics context if available
        if analytics_context:
            messages.append({
                "role": "system", 
                "content": f"Current Analytics Data:\n{analytics_context}"
            })
        
        # Add conversation history (last 5 exchanges)
        messages.extend(self.conversation_history[-10:])
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        try:
            settings = get_settings()
            temperature = settings.get("temperature", LMSTUDIO_TEMPERATURE)
            max_tokens = settings.get("max_tokens", 2048)
            
            request_payload = {
                "model": current_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            # Log the actual request being sent
            import logging
            logging.info(f"[LLM Request] Temperature: {temperature}, Model: {current_model}, Max Tokens: {max_tokens}")
            
            async with httpx.AsyncClient(timeout=LMSTUDIO_TIMEOUT) as client:
                response = await client.post(
                    f"{self.base_url}/chat",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=request_payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    assistant_message = data["choices"][0]["message"]["content"]
                    
                    # Update conversation history
                    self.conversation_history.append({"role": "user", "content": user_message})
                    self.conversation_history.append({"role": "assistant", "content": assistant_message})
                    
                    # Keep only last 10 messages
                    if len(self.conversation_history) > 10:
                        self.conversation_history = self.conversation_history[-10:]
                    
                    return assistant_message
                else:
                    error_msg = f"Error: API returned status {response.status_code}"
                    try:
                        error_data = response.json()
                        error_msg += f"\nDetails: {error_data.get('detail', response.text)}"
                    except:
                        error_msg += f"\nResponse: {response.text[:200]}"
                    return error_msg
                    
        except httpx.ConnectError:
            return f"Cannot connect to vLLM API at {self.base_url}. Please ensure:\n1. Docker services are running (make up)\n2. API is healthy (curl http://localhost:8787/api/healthz)\n3. Check logs with: make logs"
        except httpx.TimeoutException:
            return "Request timed out. The model might be processing a long response. Try again or reduce max_tokens."
        except Exception as e:
            return f"Error communicating with vLLM API: {str(e)}"
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def set_system_prompt(self, prompt: str):
        """Update the system prompt"""
        self.system_prompt = prompt
