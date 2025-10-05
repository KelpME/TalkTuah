# Talk-Tuah 🎤

A beautiful terminal UI chatbot with dynamic gradient text and Omarchy theme integration, powered by vLLM.

## ✨ Features

- 🎨 **Dynamic Gradient Text** - Stationary gradient that messages scroll through
- 🎭 **Omarchy Theme Integration** - Automatically syncs with your system theme
- ⚡ **Real-time Streaming** - Fast SSE-based responses
- 💾 **System Monitoring** - Live RAM and VRAM usage display
- 🔧 **vLLM Backend** - High-performance GPU inference
- 🐳 **Docker Compose** - Easy deployment with GPU support

## Quick Start

### Prerequisites

- Docker & Docker Compose with GPU support
- NVIDIA GPU with 16GB+ VRAM (for 7B models)
- NVIDIA Container Toolkit installed

### Setup

```bash
# 1. Clone
git clone https://github.com/KelpME/TalkTuah.git
cd TalkTuah

# 2. Configure
cp .env.example .env
# Edit .env: set PROXY_API_KEY and HF_TOKEN

# 3. Start backend
make up

# 4. Run TUI (in another terminal)
make frontend
```

That's it! The TUI will connect to the vLLM backend and you can start chatting.

## 🎨 Theme System

Talk-Tuah automatically syncs with your Omarchy theme:

```bash
# Your theme changes are detected automatically
omarchy theme set <theme-name>
# TUI updates colors in real-time!
```

**Gradient Colors:**
- Middle: Orange (gradient_mid)  
- Bottom: Green (gradient_bottom)

Messages scroll through the stationary gradient for a beautiful effect.

## ⌨️ Keyboard Shortcuts

- `Ctrl+C` / `Ctrl+Q` - Quit
- `Ctrl+L` - Clear chat
- `Ctrl+R` - Reconnect to backend
- `Enter` - Send message

## Configuration

### Environment Variables

{{ ... }}
Copy `.env.example` to `.env` and configure:

```bash
# Proxy API Configuration
PROXY_API_KEY=your-secret-key-here

# vLLM Configuration
OPENAI_BASE_URL=http://vllm:8000/v1
DEFAULT_MODEL=meta-llama/Meta-Llama-3.1-8B-Instruct
TP_SIZE=1
MAX_MODEL_LEN=8192

# HuggingFace Token (required for gated models)
HF_TOKEN=hf_your_token_here

# CORS (comma-separated origins)
CORS_ORIGINS=http://localhost:3000,http://localhost:8787

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
```

### Switching Models

To use a different model, update `DEFAULT_MODEL` in `.env`:

```bash
# Mistral 7B
DEFAULT_MODEL=mistralai/Mistral-7B-Instruct-v0.2

# Qwen 2.5
DEFAULT_MODEL=Qwen/Qwen2.5-7B-Instruct

# Phi-3
DEFAULT_MODEL=microsoft/Phi-3-mini-4k-instruct
```

**Important:**

- Check [vLLM supported models](https://docs.vllm.ai/en/latest/models/supported_models.html) for compatibility
- Gated models (Llama, Gemma) require `HF_TOKEN`
- Adjust `MAX_MODEL_LEN` based on model's context window
- For multi-GPU, set `TP_SIZE` to number of GPUs

## Docker Compose Services

### vLLM Service

- **Image:** `vllm/vllm-openai:v0.11.0` ([Release](https://github.com/vllm-project/vllm/releases/tag/v0.11.0))
- **Port:** 8000
- **GPU:** NVIDIA runtime with all GPUs
- **Health Check:** `/v1/models` endpoint
- **Volumes:** HuggingFace cache mounted

### API Service

- **Build:** `apps/api/Dockerfile`
- **Port:** 8787
- **Dependencies:** Waits for vLLM health check
- **Features:** Auth, rate limiting, CORS, streaming

## Makefile Commands

### Backend Commands

```bash
make up        # Start all services (vLLM + API)
make down      # Stop all services
make logs      # Follow logs
make restart   # Restart services
make build     # Rebuild API service
make clean     # Remove all containers and volumes
make test      # Run pytest tests
make bench     # Run benchmark
```

### Frontend Commands

```bash
make install-frontend  # Install TUI dependencies
make frontend          # Run terminal chat interface
```

## Testing

### Prerequisites

```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Ensure services are running
make up
```

### Run Tests

```bash
# All tests
make test

# Specific test
pytest tests/test_api.py::test_chat_stream -v

# With coverage
pytest tests/ --cov=apps/api --cov-report=html
```

### Test Coverage

- ✅ Health check
- ✅ Model listing
- ✅ Non-streaming chat
- ✅ Streaming chat with SSE
- ✅ Authentication (valid, invalid, missing)
- ✅ Parameter validation
- ✅ Error handling

## Benchmarking

Measure latency and throughput:

```bash
# Install benchmark dependencies
pip install -r bench/requirements.txt

# Run benchmark (10 runs, 2 warmup)
make bench

# Custom runs
python bench/latency.py --runs 20 --warmup 5
```

**Output:**

```
======================================================================
vLLM Chat API Benchmark
======================================================================
API URL: http://localhost:8787
Model: meta-llama/Meta-Llama-3.1-8B-Instruct
Warmup runs: 2
Benchmark runs: 10
======================================================================

Time to First Byte (TTFB):
  Mean:   0.234s
  Median: 0.228s
  P95:    0.312s

End-to-End Latency:
  Mean:   2.145s
  Median: 2.098s
  P95:    2.456s

Throughput:
  Mean:   45.3 tokens/s
  Median: 46.1 tokens/s
```

## Monitoring

### Prometheus Metrics

vLLM exposes Prometheus metrics at `http://localhost:8000/metrics`:

**Key Metrics:**

- `vllm:num_requests_running` - Active requests
- `vllm:num_requests_waiting` - Queue depth
- `vllm:time_to_first_token_seconds` - TTFB histogram
- `vllm:gpu_cache_usage_perc` - GPU KV cache utilization
- `vllm:generation_tokens_total` - Total tokens generated

**Setup Prometheus:**

```bash
docker run -d \
  --name prometheus \
  --network vllm-demo_default \
  -p 9090:9090 \
  -v $(pwd)/deploy/metrics/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

See [deploy/metrics/README.md](deploy/metrics/README.md) for detailed monitoring setup.

## Troubleshooting

### Model fails to load

**Symptoms:** vLLM container restarts, health check fails

**Solutions:**

1. Check HuggingFace token for gated models:
   ```bash
   # Verify token
   curl -H "Authorization: Bearer $HF_TOKEN" \
        https://huggingface.co/api/whoami
   ```

2. Check GPU memory:
   ```bash
   nvidia-smi
   # Reduce MAX_MODEL_LEN if OOM
   ```

3. Check logs:
   ```bash
   docker compose logs vllm
   ```

### Slow inference

**Solutions:**

1. Check GPU utilization:
   ```bash
   watch -n 1 nvidia-smi
   ```

2. Monitor metrics:
   ```bash
   curl http://localhost:8000/metrics | grep cache_usage
   ```

3. Reduce `MAX_MODEL_LEN` to free GPU memory
4. Consider quantized models (GPTQ, AWQ)

### Connection refused

**Symptoms:** API returns 502 Bad Gateway

**Solutions:**

1. Wait for vLLM to finish loading (1-5 minutes):
   ```bash
   docker compose ps
   # Wait for vllm to be "healthy"
   ```

2. Check vLLM logs:
   ```bash
   make logs
   ```

### Rate limiting

**Symptoms:** 429 Too Many Requests

**Solutions:**

1. Increase `RATE_LIMIT_PER_MINUTE` in `.env`
2. Implement client-side backoff

## Production Deployment

### Security Checklist

- ✅ Change `PROXY_API_KEY` to strong random value
- ✅ Configure `CORS_ORIGINS` to specific domains
- ✅ Use HTTPS reverse proxy (nginx, Traefik)
- ✅ Enable rate limiting per API key
- ✅ Restrict `/metrics` endpoint access
- ✅ Set up log aggregation
- ✅ Configure resource limits in Docker Compose

### Scaling

**Horizontal Scaling:**

```yaml
# docker-compose.yml
services:
  api:
    deploy:
      replicas: 3
```

**Multi-GPU:**

```bash
# .env
TP_SIZE=4  # Use 4 GPUs with tensor parallelism
```

**Load Balancing:**

Use nginx or Traefik to load balance across multiple API replicas.

## Terminal UI Frontend

A beautiful terminal-based chat interface is included:

```bash
# Install dependencies
make install-frontend

# Run the TUI
make frontend
```

**Features:**
- BTOP++ inspired design
- btop-style theme system (4 built-in themes + custom themes)
- Real-time streaming responses
- Conversation history
- Keyboard shortcuts (Ctrl+L clear, Ctrl+Q quit)
- Terminal color adaptation

**Themes:**
```bash
# Default: automatically uses your system's current theme (omarchy/btop)
color_theme = "system"  # Reads from ~/.config/omarchy/current/btop.theme

# Or use terminal ANSI colors
color_theme = "terminal"
```

**No theme duplication!** TuivLLM reads directly from your system's current theme. Switch themes once, affects all terminal apps.

See [frontend/README.md](frontend/README.md) and [frontend/THEMES.md](frontend/THEMES.md) for detailed documentation.

## Project Structure

```
.
├── apps/
│   └── api/              # FastAPI proxy service
│       ├── Dockerfile
│       ├── main.py       # API endpoints
│       ├── config.py     # Settings
│       ├── models.py     # Pydantic models
│       ├── auth.py       # Authentication
│       └── requirements.txt
├── frontend/             # Terminal UI chat interface
│   ├── TuivLLM.py       # Main TUI application
│   ├── llm_client.py    # vLLM API client
│   ├── config.py        # Frontend config
│   ├── run.sh           # Startup script
│   └── requirements.txt
├── services/
│   └── vllm/
│       └── README.md     # vLLM configuration docs
├── tests/
│   ├── conftest.py       # Test fixtures
│   ├── test_api.py       # API tests
│   └── requirements.txt
├── bench/
│   ├── latency.py        # Benchmark script
│   └── requirements.txt
├── deploy/
│   └── metrics/
│       ├── prometheus.yml
│       └── README.md
├── docker-compose.yml    # Service orchestration
├── Makefile              # Common commands
├── .env.example          # Configuration template
└── README.md             # This file
```

## Version Information

- **vLLM Version:** v0.11.0
- **Release Date:** October 2025
- **Release Page:** https://github.com/vllm-project/vllm/releases/tag/v0.11.0
- **Docker Image:** `vllm/vllm-openai:v0.11.0`
- **Python:** 3.11+
- **FastAPI:** 0.115.0
- **CUDA:** 12.1+ (via vLLM image)

## References

- [vLLM Documentation](https://docs.vllm.ai/en/latest/)
- [vLLM OpenAI-Compatible Server](https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html)
- [vLLM Docker Guide](https://docs.vllm.ai/en/latest/serving/deploying_with_docker.html)
- [vLLM Metrics](https://docs.vllm.ai/en/latest/serving/metrics.html)
- [vLLM Supported Models](https://docs.vllm.ai/en/latest/models/supported_models.html)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference/chat)

## License

MIT

## Support

For issues and questions:

1. Check [Troubleshooting](#troubleshooting) section
2. Review vLLM logs: `make logs`
3. Check vLLM GitHub issues: https://github.com/vllm-project/vllm/issues
4. Verify GPU compatibility and VRAM requirements

---

**Built with vLLM v0.11.0** | [GitHub](https://github.com/vllm-project/vllm) | [Documentation](https://docs.vllm.ai/)
