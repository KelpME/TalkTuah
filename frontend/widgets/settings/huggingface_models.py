"""Comprehensive HuggingFace models with metadata for autocomplete"""

# Model database: {model_id: {"vram": "XGB", "params": "XB", "category": "...", "gated": bool|str, "max_tokens": int}}
# gated values: False (public), "auto" (terms required), "manual" (approval required)
# max_tokens: Maximum context length supported by the model
MODEL_DATABASE = {
    # ===== TINY MODELS (~2-4GB VRAM) =====
    "Qwen/Qwen2.5-0.5B-Instruct": {"vram": "2GB", "params": "0.5B", "category": "General", "gated": False, "max_tokens": 32768},
    "TinyLlama/TinyLlama-1.1B-Chat-v1.0": {"vram": "3GB", "params": "1.1B", "category": "General", "gated": False, "max_tokens": 2048},
    "meta-llama/Llama-3.2-1B-Instruct": {"vram": "3GB", "params": "1B", "category": "General", "gated": "auto", "max_tokens": 131072},
    "deepseek-ai/deepseek-coder-1.3b-instruct": {"vram": "3GB", "params": "1.3B", "category": "Code", "gated": False, "max_tokens": 16384},
    
    # ===== SMALL MODELS (~4-8GB VRAM) =====
    "Qwen/Qwen2.5-1.5B-Instruct": {"vram": "4GB", "params": "1.5B", "category": "General", "gated": False, "max_tokens": 32768},
    "stabilityai/stablelm-2-1_6b": {"vram": "4GB", "params": "1.6B", "category": "General", "gated": False, "max_tokens": 4096},
    "google/gemma-2-2b-it": {"vram": "5GB", "params": "2B", "category": "General", "gated": "auto", "max_tokens": 8192},
    "microsoft/phi-2": {"vram": "6GB", "params": "2.7B", "category": "General", "gated": False, "max_tokens": 2048},
    "Qwen/Qwen2.5-3B-Instruct": {"vram": "7GB", "params": "3B", "category": "General", "gated": False, "max_tokens": 32768},
    "meta-llama/Llama-3.2-3B-Instruct": {"vram": "7GB", "params": "3B", "category": "General", "gated": "auto", "max_tokens": 131072},
    "stabilityai/stablelm-zephyr-3b": {"vram": "7GB", "params": "3B", "category": "General", "gated": False, "max_tokens": 4096},
    
    # ===== MEDIUM MODELS (~8-12GB VRAM) =====
    "microsoft/Phi-3-mini-4k-instruct": {"vram": "8GB", "params": "3.8B", "category": "General", "gated": False, "max_tokens": 4096},
    "microsoft/Phi-3-mini-128k-instruct": {"vram": "8GB", "params": "3.8B", "category": "General", "gated": False, "max_tokens": 131072},
    "microsoft/Phi-3.5-mini-instruct": {"vram": "8GB", "params": "3.8B", "category": "General", "gated": False, "max_tokens": 131072},
    "Qwen/Qwen2.5-Coder-7B-Instruct": {"vram": "10GB", "params": "7B", "category": "Code", "gated": False, "max_tokens": 131072},
    
    # ===== LARGE MODELS (~12-20GB VRAM) =====
    "Qwen/Qwen2.5-7B-Instruct": {"vram": "15GB", "params": "7B", "category": "General", "gated": False, "max_tokens": 131072},
    "meta-llama/Meta-Llama-3.1-8B-Instruct": {"vram": "16GB", "params": "8B", "category": "General", "gated": "auto", "max_tokens": 131072},
    "mistralai/Mistral-7B-Instruct-v0.3": {"vram": "15GB", "params": "7B", "category": "General", "gated": "auto", "max_tokens": 32768},
    "mistralai/Mistral-Nemo-Instruct-2407": {"vram": "15GB", "params": "12B", "category": "General", "gated": "auto", "max_tokens": 131072},
    "google/gemma-2-9b-it": {"vram": "18GB", "params": "9B", "category": "General", "gated": "auto", "max_tokens": 8192},
    "deepseek-ai/deepseek-coder-6.7b-instruct": {"vram": "14GB", "params": "6.7B", "category": "Code", "gated": False, "max_tokens": 16384},
    "HuggingFaceH4/zephyr-7b-beta": {"vram": "15GB", "params": "7B", "category": "General", "gated": False, "max_tokens": 32768},
    "codellama/CodeLlama-7b-Instruct-hf": {"vram": "15GB", "params": "7B", "category": "Code", "gated": "auto", "max_tokens": 16384},
    
    # ===== EXTRA LARGE MODELS (~24-40GB VRAM) =====
    "Qwen/Qwen2.5-14B-Instruct": {"vram": "28GB", "params": "14B", "category": "General", "gated": False, "max_tokens": 131072},
    "microsoft/Phi-3-medium-4k-instruct": {"vram": "28GB", "params": "14B", "category": "General", "gated": False, "max_tokens": 4096},
    "google/gemma-2-27b-it": {"vram": "54GB", "params": "27B", "category": "General", "gated": "auto", "max_tokens": 8192},
    "Qwen/Qwen2.5-32B-Instruct": {"vram": "64GB", "params": "32B", "category": "General", "gated": False, "max_tokens": 131072},
    "deepseek-ai/deepseek-coder-33b-instruct": {"vram": "66GB", "params": "33B", "category": "Code", "gated": False, "max_tokens": 16384},
    "codellama/CodeLlama-34b-Instruct-hf": {"vram": "68GB", "params": "34B", "category": "Code", "gated": "auto", "max_tokens": 16384},
    
    # ===== MIXTURE OF EXPERTS (~40-80GB VRAM) =====
    "mistralai/Mixtral-8x7B-Instruct-v0.1": {"vram": "90GB", "params": "47B", "category": "MoE", "gated": "auto", "max_tokens": 32768},
    "mistralai/Mixtral-8x22B-Instruct-v0.1": {"vram": "180GB", "params": "141B", "category": "MoE", "gated": "auto", "max_tokens": 65536},
    
    # ===== HUGE MODELS (~80GB+ VRAM) =====
    "Qwen/Qwen2.5-72B-Instruct": {"vram": "144GB", "params": "72B", "category": "General", "gated": False, "max_tokens": 131072},
    "meta-llama/Meta-Llama-3.1-70B-Instruct": {"vram": "140GB", "params": "70B", "category": "General", "gated": "auto", "max_tokens": 131072},
    "deepseek-ai/deepseek-llm-67b-chat": {"vram": "134GB", "params": "67B", "category": "General", "gated": False, "max_tokens": 4096},
    "meta-llama/Llama-3.1-405B-Instruct": {"vram": "810GB", "params": "405B", "category": "General", "gated": "manual", "max_tokens": 131072},
    "deepseek-ai/DeepSeek-V3": {"vram": "1.4TB", "params": "685B", "category": "MoE", "gated": False, "max_tokens": 65536},
    
    # ===== SPECIALIZED CODE MODELS =====
    "Qwen/Qwen2.5-Coder-1.5B-Instruct": {"vram": "4GB", "params": "1.5B", "category": "Code", "gated": False, "max_tokens": 131072},
    "Qwen/Qwen2.5-Coder-3B-Instruct": {"vram": "7GB", "params": "3B", "category": "Code", "gated": False, "max_tokens": 131072},
    "Qwen/Qwen2.5-Coder-14B-Instruct": {"vram": "28GB", "params": "14B", "category": "Code", "gated": False, "max_tokens": 131072},
    "Qwen/Qwen2.5-Coder-32B-Instruct": {"vram": "64GB", "params": "32B", "category": "Code", "gated": False, "max_tokens": 131072},
    "01-ai/Yi-6B-Chat": {"vram": "12GB", "params": "6B", "category": "General", "gated": False, "max_tokens": 4096},
    "01-ai/Yi-34B-Chat": {"vram": "68GB", "params": "34B", "category": "General", "gated": False, "max_tokens": 4096},
}

# Legacy list for backward compatibility
POPULAR_MODELS = list(MODEL_DATABASE.keys())


def get_model_info(model_id: str) -> dict:
    """Get metadata for a specific model"""
    return MODEL_DATABASE.get(model_id, {"vram": "Unknown", "params": "Unknown", "category": "Unknown", "max_tokens": 4096})


def format_model_suggestion(model_id: str) -> str:
    """Format model name with VRAM requirement and gated status for display"""
    info = get_model_info(model_id)
    base = f"{model_id} ({info['vram']}, {info['params']})"
    
    # Add gated indicator
    gated = info.get('gated', False)
    if gated == 'auto':
        return f"{base} [Terms]"
    elif gated == 'manual':
        return f"{base} [Approval]"
    else:
        return base


def get_autocomplete_suggestions(partial: str) -> list[str]:
    """Get autocomplete suggestions with VRAM info for partial model name"""
    if not partial:
        return []
    
    partial_lower = partial.lower()
    matches = []
    
    # Find all models that contain the partial string
    for model in POPULAR_MODELS:
        if partial_lower in model.lower():
            matches.append(model)
    
    return matches


def get_autocomplete_suggestion(partial: str) -> str:
    """Get first autocomplete suggestion (for backwards compatibility)"""
    suggestions = get_autocomplete_suggestions(partial)
    return suggestions[0] if suggestions else ""
