# API Endpoints Documentation

API endpoints for TalkTuah - optimized for N8n HTTP Request nodes.

## Base URL
```
http://localhost:8787
```

## Authentication
All endpoints (except `/`, `/api/healthz`, `/metrics`) require Bearer token authentication:
```
Authorization: Bearer ${PROXY_API_KEY}
```

---

## Model Downloads

### Download Model
**Endpoint:** `POST /api/download-model`

Download a model from HuggingFace using pure Python (no shell scripts).

**N8n HTTP Request Node Settings:**
- Method: `POST`
- URL: `http://localhost:8787/api/download-model`
- Authentication: Generic Credential Type → Header Auth
  - Name: `Authorization`
  - Value: `Bearer YOUR_API_KEY`
- Query Parameters:
  - `model_id`: HuggingFace model ID (e.g., `TinyLlama/TinyLlama-1.1B-Chat-v1.0`)
  - `auto`: `true` (triggers automated download)

**Example:**
```bash
curl -X POST "http://localhost:8787/api/download-model?model_id=TinyLlama/TinyLlama-1.1B-Chat-v1.0&auto=true" \
  -H "Authorization: Bearer ${PROXY_API_KEY}"
```

**Response:**
```json
{
  "status": "downloading",
  "message": "Download started for TinyLlama/TinyLlama-1.1B-Chat-v1.0",
  "model_id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
  "info": "Download in progress. Check /api/download-progress for status."
}
```

---

### Check Download Progress
**Endpoint:** `GET /api/download-progress`

Get real-time download progress.

**N8n HTTP Request Node Settings:**
- Method: `GET`
- URL: `http://localhost:8787/api/download-progress`
- Authentication: Bearer Token

**Example:**
```bash
curl "http://localhost:8787/api/download-progress" \
  -H "Authorization: Bearer ${PROXY_API_KEY}"
```

**Response:**
```json
{
  "status": "downloading",
  "progress": 45,
  "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
  "error": null
}
```

**Status Values:**
- `idle`: No active download
- `downloading`: Download in progress
- `complete`: Download finished
- `error`: Download failed (check `error` field)

---

### Delete Model
**Endpoint:** `DELETE /api/delete-model`

Delete a downloaded model to free up disk space.

**N8n HTTP Request Node Settings:**
- Method: `DELETE`
- URL: `http://localhost:8787/api/delete-model`
- Authentication: Bearer Token
- Query Parameters:
  - `model_id`: Model to delete (e.g., `TinyLlama/TinyLlama-1.1B-Chat-v1.0`)

**Example:**
```bash
curl -X DELETE "http://localhost:8787/api/delete-model?model_id=TinyLlama/TinyLlama-1.1B-Chat-v1.0" \
  -H "Authorization: Bearer ${PROXY_API_KEY}"
```

**Response:**
```json
{
  "status": "deleted",
  "message": "Model TinyLlama/TinyLlama-1.1B-Chat-v1.0 deleted successfully",
  "model_id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
}
```

---

## Model Management

### Get Model Status
**Endpoint:** `GET /api/model-status`

Check available models and currently loaded model.

**N8n HTTP Request Node Settings:**
- Method: `GET`
- URL: `http://localhost:8787/api/model-status`
- Authentication: Bearer Token

**Example:**
```bash
curl "http://localhost:8787/api/model-status" \
  -H "Authorization: Bearer ${PROXY_API_KEY}"
```

**Response:**
```json
{
  "models_available": true,
  "models_dir_exists": true,
  "downloaded_models": [
    "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    "meta-llama/Llama-2-7b-chat-hf"
  ],
  "current_model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
  "vllm_healthy": true,
  "message": "Models found"
}
```

---

### Switch Model
**Endpoint:** `POST /api/switch-model`

Switch to a different downloaded model.

**N8n HTTP Request Node Settings:**
- Method: `POST`
- URL: `http://localhost:8787/api/switch-model`
- Authentication: Bearer Token
- Query Parameters:
  - `model_id`: Model to switch to

**Example:**
```bash
curl -X POST "http://localhost:8787/api/switch-model?model_id=meta-llama/Llama-2-7b-chat-hf" \
  -H "Authorization: Bearer ${PROXY_API_KEY}"
```

**Response:**
```json
{
  "status": "switching",
  "message": "Switching to meta-llama/Llama-2-7b-chat-hf",
  "model_id": "meta-llama/Llama-2-7b-chat-hf",
  "info": "vLLM is loading the new model. Check /api/model-loading-status for progress.",
  "estimated_time_seconds": 60
}
```

---

### Check Model Loading Status
**Endpoint:** `GET /api/model-loading-status`

Poll this endpoint after switching models to check when ready.

**N8n HTTP Request Node Settings:**
- Method: `GET`
- URL: `http://localhost:8787/api/model-loading-status`
- Authentication: Bearer Token

**Example:**
```bash
curl "http://localhost:8787/api/model-loading-status" \
  -H "Authorization: Bearer ${PROXY_API_KEY}"
```

**Response (Ready):**
```json
{
  "status": "ready",
  "model_loaded": true,
  "current_model": "meta-llama/Llama-2-7b-chat-hf",
  "message": "vLLM is ready"
}
```

**Response (Loading):**
```json
{
  "status": "loading",
  "model_loaded": false,
  "current_model": null,
  "message": "vLLM is starting up..."
}
```

---

## Chat Completion

### Chat Endpoint
**Endpoint:** `POST /api/chat`

OpenAI-compatible chat completion with streaming support.

**N8n HTTP Request Node Settings:**
- Method: `POST`
- URL: `http://localhost:8787/api/chat`
- Authentication: Bearer Token
- Body (JSON):
```json
{
  "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "max_tokens": 512,
  "stream": false
}
```

**Example:**
```bash
curl -X POST "http://localhost:8787/api/chat" \
  -H "Authorization: Bearer ${PROXY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    "messages": [{"role": "user", "content": "Hello!"}],
    "temperature": 0.7,
    "stream": false
  }'
```

---

## System Endpoints

### Health Check
**Endpoint:** `GET /api/healthz`

No authentication required.

**Example:**
```bash
curl "http://localhost:8787/api/healthz"
```

**Response:**
```json
{
  "status": "healthy",
  "gpu_available": true,
  "model_loaded": true,
  "upstream_healthy": true,
  "queue_size": 0,
  "details": {
    "models": ["TinyLlama/TinyLlama-1.1B-Chat-v1.0"]
  }
}
```

---

### Metrics
**Endpoint:** `GET /metrics`

Prometheus metrics endpoint. No authentication required.

**Example:**
```bash
curl "http://localhost:8787/metrics"
```

---

## Typical Workflows

### Workflow 1: Download and Switch to New Model

1. **Download model:**
   ```
   POST /api/download-model?model_id=MODEL_ID&auto=true
   ```

2. **Poll download progress (every 5 seconds):**
   ```
   GET /api/download-progress
   ```
   Until `status == "complete"`

3. **Switch to new model:**
   ```
   POST /api/switch-model?model_id=MODEL_ID
   ```

4. **Poll loading status (every 5 seconds):**
   ```
   GET /api/model-loading-status
   ```
   Until `status == "ready"`

5. **Start chatting:**
   ```
   POST /api/chat
   ```

### Workflow 2: Clean Up Old Models

1. **Check downloaded models:**
   ```
   GET /api/model-status
   ```

2. **Delete unused model:**
   ```
   DELETE /api/delete-model?model_id=MODEL_ID
   ```

---

## Error Responses

All endpoints return standard HTTP error codes with JSON bodies:

**404 Not Found:**
```json
{
  "detail": "Model not found: invalid-model-id"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Failed to download model: Connection timeout"
}
```

**502 Bad Gateway:**
```json
{
  "detail": "Failed to connect to vLLM server"
}
```
