# Configuration file for TuivLLM Chat Interface
import os

# vLLM Proxy API Configuration
VLLM_API_URL = os.getenv("VLLM_API_URL", "http://localhost:8787/api")
VLLM_API_KEY = os.getenv("PROXY_API_KEY", "change-me")
VLLM_MODEL = os.getenv("DEFAULT_MODEL", "meta-llama/Meta-Llama-3.1-8B-Instruct")

# Request Configuration
LMSTUDIO_URL = VLLM_API_URL  # For backward compatibility
LMSTUDIO_TIMEOUT = 60.0
LMSTUDIO_MAX_TOKENS = 500
LMSTUDIO_TEMPERATURE = 0.7

# LLM System Prompt
LLM_SYSTEM_PROMPT = """You are a helpful AI assistant. 
Be concise, accurate, and friendly in your responses.
Provide clear explanations and helpful information."""

# Color Scheme (for future customization)
COLORS = {
    "positive": "green",
    "neutral": "yellow", 
    "negative": "red",
    "primary": "cyan",
    "chart_border": "green",
    "bar_chart_border": "yellow",
    "chat_border": "cyan"
}
