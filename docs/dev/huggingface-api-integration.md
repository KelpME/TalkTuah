# HuggingFace API Integration

## Getting All Models from HuggingFace

### HuggingFace API Endpoints

**List Models API:**
```bash
# Get all text-generation models
curl "https://huggingface.co/api/models?filter=text-generation&sort=downloads&direction=-1&limit=100"

# Get models with specific tags
curl "https://huggingface.co/api/models?filter=text-generation&search=instruct&limit=100"
```

**Model Details API:**
```bash
# Get model info including gated status
curl "https://huggingface.co/api/models/meta-llama/Llama-3.1-8B-Instruct"
```

### Response Structure

```json
{
  "id": "meta-llama/Llama-3.1-8B-Instruct",
  "modelId": "meta-llama/Llama-3.1-8B-Instruct",
  "author": "meta-llama",
  "gated": "auto",  // or "manual" or false
  "downloads": 1234567,
  "likes": 5678,
  "private": false,
  "tags": ["text-generation", "llama-3", "conversational"],
  "pipeline_tag": "text-generation",
  "library_name": "transformers"
}
```

### Gated Status Values

- **false** - Public, no permission needed
- **"auto"** - Auto-approved after accepting terms
- **"manual"** - Requires manual approval from model owner

## Implementation Options

### Option 1: Static Curated List (Current)
**Pros:**
- Fast, no API calls needed
- Works offline
- Controlled quality

**Cons:**
- Needs manual updates
- Limited selection
- No gated status tracking

### Option 2: Dynamic API Fetching
**Pros:**
- Always up-to-date
- Complete model catalog
- Automatic gated detection

**Cons:**
- Requires internet
- API rate limits
- Slower initial load

### Option 3: Hybrid (Recommended)
**Pros:**
- Curated default list
- Optional API search
- Best of both worlds

**Cons:**
- More complex

## Python Implementation

### Fetch Models from API

```python
import httpx
from typing import List, Dict

async def fetch_hf_models(
    limit: int = 100,
    filter_tag: str = "text-generation",
    search: str = "",
    sort: str = "downloads"
) -> List[Dict]:
    """Fetch models from HuggingFace API"""
    
    url = "https://huggingface.co/api/models"
    params = {
        "filter": filter_tag,
        "sort": sort,
        "direction": "-1",
        "limit": limit
    }
    
    if search:
        params["search"] = search
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            return []


async def get_model_details(model_id: str) -> Dict:
    """Get detailed model info including gated status"""
    
    url = f"https://huggingface.co/api/models/{model_id}"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {}


def is_model_gated(model_data: Dict) -> bool:
    """Check if model requires permission"""
    gated = model_data.get("gated", False)
    return gated in ["auto", "manual", True]


def get_gated_type(model_data: Dict) -> str:
    """Get type of gating"""
    gated = model_data.get("gated", False)
    
    if gated == "auto":
        return "Terms Required"
    elif gated == "manual":
        return "Approval Required"
    elif gated is True:
        return "Restricted"
    else:
        return "Public"
```

### Enhanced Model Database with Gated Status

```python
MODEL_DATABASE = {
    # Public models
    "Qwen/Qwen2.5-1.5B-Instruct": {
        "vram": "4GB",
        "params": "1.5B",
        "category": "General",
        "gated": False
    },
    
    # Auto-approved (terms required)
    "meta-llama/Llama-3.1-8B-Instruct": {
        "vram": "16GB",
        "params": "8B",
        "category": "General",
        "gated": "auto"  # Accept terms on HuggingFace
    },
    
    # Manual approval required
    "meta-llama/Llama-3.1-405B-Instruct": {
        "vram": "810GB",
        "params": "405B",
        "category": "General",
        "gated": "manual"  # Request access from Meta
    },
}
```

## UI Display Options

### Indicator Styles

**Bracket Suffix:**
```
meta-llama/Llama-3.1-8B-Instruct (16GB, 8B) [Terms]
meta-llama/Llama-3.1-405B-Instruct (810GB, 405B) [Approval]
Qwen/Qwen2.5-1.5B-Instruct (4GB, 1.5B)
```

**Color Coding:**
```python
# Green: Public
# Yellow: Auto-approved (terms)
# Red: Manual approval
```

**Icon/Symbol:**
```
[LOCK] meta-llama/Llama-3.1-8B-Instruct (16GB, 8B)
[KEY] meta-llama/Llama-3.1-405B-Instruct (810GB, 405B)
      Qwen/Qwen2.5-1.5B-Instruct (4GB, 1.5B)
```

## Current Models with Gated Status

### Gated Models (Auto-Approved)
- meta-llama/Meta-Llama-3.1-8B-Instruct
- meta-llama/Meta-Llama-3.1-70B-Instruct
- meta-llama/Llama-3.1-405B-Instruct
- meta-llama/Llama-3.2-1B-Instruct
- meta-llama/Llama-3.2-3B-Instruct
- google/gemma-2-2b-it
- google/gemma-2-9b-it
- google/gemma-2-27b-it
- mistralai/Mistral-7B-Instruct-v0.3
- mistralai/Mistral-Nemo-Instruct-2407
- mistralai/Mixtral-8x7B-Instruct-v0.1
- mistralai/Mixtral-8x22B-Instruct-v0.1

### Public Models (No Restriction)
- Qwen/* (all Qwen models)
- microsoft/Phi-* (most Phi models)
- deepseek-ai/* (most DeepSeek models)
- TinyLlama/*
- stabilityai/*
- HuggingFaceH4/*
- codellama/* (some restricted)
- 01-ai/Yi-*

## Recommended Implementation

Add gated status to current database and display it in the UI:

```python
def format_model_suggestion(model_id: str) -> str:
    """Format model with VRAM, params, and gated status"""
    info = get_model_info(model_id)
    
    base = f"{model_id} ({info['vram']}, {info['params']})"
    
    if info.get('gated') == 'auto':
        return f"{base} [Terms]"
    elif info.get('gated') == 'manual':
        return f"{base} [Approval]"
    else:
        return base
```

## N8n Integration

When downloading gated models via API, HuggingFace token is required:

```bash
# Download with token
curl -H "Authorization: Bearer hf_YOUR_TOKEN" \
     https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct
```

Add token configuration to settings for N8n workflows.
