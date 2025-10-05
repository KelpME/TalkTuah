# vLLM Service Configuration

This directory contains configuration and documentation for the vLLM OpenAI-compatible server.

## Docker Image

**Pinned Version:** `vllm/vllm-openai:v0.11.0`

- **Release Date:** Latest stable release as of October 2025
- **Release Page:** https://github.com/vllm-project/vllm/releases/tag/v0.11.0
- **Docker Hub:** https://hub.docker.com/r/vllm/vllm-openai/tags

## Configuration

The vLLM server is configured via environment variables in `.env`:

### Model Configuration

- `DEFAULT_MODEL`: HuggingFace model ID (default: `meta-llama/Meta-Llama-3.1-8B-Instruct`)
- `MAX_MODEL_LEN`: Maximum sequence length (default: `8192`)
- `TP_SIZE`: Tensor parallel size for multi-GPU (default: `1`)

### Authentication

- `HF_TOKEN`: HuggingFace token for gated models (required for Llama models)

## Switching Models

To use a different model, update `DEFAULT_MODEL` in your `.env` file:

```bash
# Example: Use Mistral 7B
DEFAULT_MODEL=mistralai/Mistral-7B-Instruct-v0.2

# Example: Use Qwen 2.5
DEFAULT_MODEL=Qwen/Qwen2.5-7B-Instruct

# Example: Use Phi-3
DEFAULT_MODEL=microsoft/Phi-3-mini-4k-instruct
```

**Important Notes:**

1. Model compatibility depends on the vLLM version (v0.11.0)
2. Check [vLLM supported models](https://docs.vllm.ai/en/latest/models/supported_models.html)
3. Gated models (e.g., Llama) require `HF_TOKEN`
4. Adjust `MAX_MODEL_LEN` based on model's context window
5. For multi-GPU setups, set `TP_SIZE` to number of GPUs

## Endpoints

The vLLM server exposes OpenAI-compatible endpoints on port 8000:

- `GET /v1/models` - List loaded models
- `POST /v1/chat/completions` - Chat completions (streaming & non-streaming)
- `POST /v1/completions` - Text completions
- `GET /metrics` - Prometheus metrics
- `GET /health` - Health check

## Metrics

vLLM exposes Prometheus metrics at `http://localhost:8000/metrics`:

- `vllm:num_requests_running` - Currently running requests
- `vllm:num_requests_waiting` - Requests in queue
- `vllm:gpu_cache_usage_perc` - GPU KV cache utilization
- `vllm:time_to_first_token_seconds` - TTFB latency
- `vllm:time_per_output_token_seconds` - Token generation latency

See [vLLM Metrics Documentation](https://docs.vllm.ai/en/latest/serving/metrics.html) for full list.

## GPU Requirements

- **Minimum:** 1x NVIDIA GPU with 16GB+ VRAM for 7B models
- **Recommended:** 1x A100 (40GB) or 1x H100 (80GB) for larger models
- **Multi-GPU:** Set `TP_SIZE` to number of GPUs for tensor parallelism

## Troubleshooting

### Model fails to load

1. Check `HF_TOKEN` is set for gated models
2. Verify GPU memory is sufficient
3. Reduce `MAX_MODEL_LEN` if OOM
4. Check vLLM logs: `docker compose logs vllm`

### Slow inference

1. Check GPU utilization: `nvidia-smi`
2. Monitor metrics at `/metrics`
3. Adjust `MAX_MODEL_LEN` to reduce memory pressure
4. Consider using quantized models (GPTQ, AWQ)

### Connection refused

1. Wait for health check to pass: `docker compose ps`
2. Model loading can take 1-5 minutes
3. Check logs for errors: `make logs`
