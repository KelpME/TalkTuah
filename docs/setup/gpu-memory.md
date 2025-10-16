# GPU Memory Configuration

## Overview
Configure GPU memory allocation dynamically for your AMD Ryzen AI Max+ 395 APU using the TUI settings menu.

## Configuration

### Via TUI Settings
1. Launch TUI: `make frontend`
2. Press `s` to open Settings
3. Adjust **GPU Memory** slider (10% - 95%)
4. Exit settings to save

### Apply Settings
```bash
make apply
```

This syncs TUI settings to `.env` and restarts vLLM with new GPU memory allocation.

## Manual Configuration

### Edit .env directly
```bash
# Set GPU memory utilization (0.1 to 0.95)
GPU_MEMORY_UTILIZATION=0.85
```

### Restart services
```bash
make restart
```

## N8n Integration

### Endpoint
```
http://localhost:8787/api/chat/completions
```

### HTTP Request Node Configuration
**Method:** POST  
**Authentication:** Bearer Token  
**Token:** `your-api-key-from-env`

**Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Body (JSON):**
```json
{
  "model": "your-model-name",
  "messages": [
    {
      "role": "user",
      "content": "Your prompt here"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 500
}
```

### Response
```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "model-name",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "AI response"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 50,
    "total_tokens": 60
  }
}
```

### Extract Response
Use JSONPath: `$.choices[0].message.content`

## Recommendations

### Memory Allocation by Use Case
- **Maximum Performance:** 0.90 - 0.95
- **Balanced:** 0.75 - 0.85
- **Conservative:** 0.50 - 0.70

### Model Size Guidelines
Your AI Max+ 395 has shared memory architecture (up to 128GB addressable).

**Safe allocations:**
- 7B models: 0.75+
- 13B models: 0.85+
- 34B models: 0.90+

The 16GB mentioned in docs is conservative. Adjust based on total system RAM availability.

## Monitoring
```bash
# Watch GPU usage
watch -n 1 'rocm-smi'

# Check vLLM logs
make logs
```
