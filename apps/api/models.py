from pydantic import BaseModel, Field
from typing import List, Optional, Union, Literal


class ChatMessage(BaseModel):
    """Single chat message."""
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    """Chat completion request matching OpenAI format."""
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = Field(default=1.0, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    stop: Optional[Union[str, List[str]]] = None
    stream: Optional[bool] = False
    n: Optional[int] = Field(default=1, ge=1)
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    gpu_available: bool
    model_loaded: bool
    upstream_healthy: bool
    queue_size: Optional[int] = None
    details: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
    status_code: int
