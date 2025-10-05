# vLLM Chat Backend - Quick Reference

## 🚀 Quick Start

```bash
cp .env.example .env        # Configure
make up                     # Start services
make logs                   # Watch startup
make frontend               # Launch TUI
```

## 🔧 Common Commands

| Command | Description |
|---------|-------------|
| `make up` | Start all services |
| `make down` | Stop all services |
| `make logs` | Follow logs |
| `make restart` | Restart services |
| `make test` | Run tests |
| `make bench` | Run benchmark |
| `make frontend` | Launch TUI |
| `make clean` | Remove everything |

## 🌐 Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/chat` | POST | ✅ | Chat completions |
| `/api/models` | GET | ✅ | List models |
| `/api/healthz` | GET | ❌ | Health check |
| `/metrics` | GET | ❌ | Prometheus metrics |

## 🔑 Environment Variables

```bash
# Required
PROXY_API_KEY=your-secret-key
HF_TOKEN=hf_your_token

# Optional
DEFAULT_MODEL=meta-llama/Meta-Llama-3.1-8B-Instruct
MAX_MODEL_LEN=8192
TP_SIZE=1
CORS_ORIGINS=*
RATE_LIMIT_PER_MINUTE=60
```

## 📡 API Examples

### Chat (Streaming)
```bash
curl -N -H "Authorization: Bearer $PROXY_API_KEY" \
     -H "Content-Type: application/json" \
     -X POST http://localhost:8787/api/chat \
     -d '{"model":"meta-llama/Meta-Llama-3.1-8B-Instruct","messages":[{"role":"user","content":"Hello"}]}'
```

### Chat (Non-Streaming)
```bash
curl -H "Authorization: Bearer $PROXY_API_KEY" \
     -H "Content-Type: application/json" \
     -X POST http://localhost:8787/api/chat \
     -d '{"model":"meta-llama/Meta-Llama-3.1-8B-Instruct","messages":[{"role":"user","content":"Hello"}],"stream":false}'
```

### List Models
```bash
curl -H "Authorization: Bearer $PROXY_API_KEY" \
     http://localhost:8787/api/models
```

### Health Check
```bash
curl http://localhost:8787/api/healthz
```

### Metrics
```bash
curl http://localhost:8787/metrics
```

## ⌨️ TUI Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Enter` | Send message |
| `Ctrl+C` / `Ctrl+Q` | Quit |
| `Ctrl+L` | Clear chat |
| `Ctrl+R` | Reconnect |

## 🔍 Troubleshooting

### Services won't start
```bash
docker compose ps          # Check status
docker compose logs vllm   # Check vLLM logs
nvidia-smi                 # Check GPU
```

### Model not loading
```bash
# Check HF token
curl -H "Authorization: Bearer $HF_TOKEN" https://huggingface.co/api/whoami

# Reduce memory
MAX_MODEL_LEN=4096 make restart
```

### API errors
```bash
# Check health
curl http://localhost:8787/api/healthz

# Check logs
make logs

# Verify API key
echo $PROXY_API_KEY
```

### Frontend won't connect
```bash
# Check backend
curl http://localhost:8787/api/healthz

# Check env vars
cat .env | grep PROXY_API_KEY

# Reinstall deps
make install-frontend
```

## 📊 Monitoring

### Key Metrics
```bash
# Queue depth
curl -s http://localhost:8000/metrics | grep num_requests_waiting

# GPU cache usage
curl -s http://localhost:8000/metrics | grep gpu_cache_usage_perc

# Request rate
curl -s http://localhost:8000/metrics | grep request_success_total
```

## 🔄 Model Switching

Edit `.env`:
```bash
# Mistral 7B
DEFAULT_MODEL=mistralai/Mistral-7B-Instruct-v0.2

# Qwen 2.5
DEFAULT_MODEL=Qwen/Qwen2.5-7B-Instruct

# Phi-3
DEFAULT_MODEL=microsoft/Phi-3-mini-4k-instruct
```

Then restart:
```bash
make restart
```

## 🐳 Docker Commands

```bash
# View containers
docker compose ps

# View logs (specific service)
docker compose logs -f vllm
docker compose logs -f api

# Restart specific service
docker compose restart vllm
docker compose restart api

# Rebuild
docker compose build api
docker compose up -d --force-recreate api

# Clean everything
docker compose down -v --remove-orphans
```

## 🧪 Testing

```bash
# All tests
pytest tests/ -v

# Specific test
pytest tests/test_api.py::test_chat_stream -v

# With output
pytest tests/ -v -s

# Coverage
pytest tests/ --cov=apps/api
```

## 📈 Benchmarking

```bash
# Default (10 runs, 2 warmup)
python bench/latency.py

# Custom
python bench/latency.py --runs 20 --warmup 5
```

## 🔐 Security Checklist

- [ ] Change `PROXY_API_KEY` from default
- [ ] Set `CORS_ORIGINS` to specific domains
- [ ] Use HTTPS in production
- [ ] Restrict `/metrics` endpoint
- [ ] Set up rate limiting
- [ ] Enable Docker resource limits
- [ ] Use secrets management (not .env in prod)

## 📁 Important Files

| File | Purpose |
|------|---------|
| `.env` | Configuration |
| `docker-compose.yml` | Service definitions |
| `Makefile` | Common commands |
| `README.md` | Full documentation |
| `QUICKSTART.md` | Setup guide |
| `verify_setup.sh` | System check |

## 🆘 Getting Help

1. Run `./verify_setup.sh` to check setup
2. Check `make logs` for errors
3. Review `README.md` troubleshooting section
4. Check vLLM docs: https://docs.vllm.ai/
5. GitHub issues: https://github.com/vllm-project/vllm/issues

## 📦 Versions

- **vLLM:** v0.11.0
- **FastAPI:** 0.115.0
- **Textual:** 0.47.1
- **Python:** 3.11+
- **CUDA:** 12.1+ (via vLLM image)

## 🎯 Ports

| Service | Port | Access |
|---------|------|--------|
| vLLM | 8000 | Internal |
| API Proxy | 8787 | External |
| Prometheus | 9090 | Optional |

---

**Quick Links:**
- [Full README](README.md)
- [Quick Start](QUICKSTART.md)
- [Frontend Docs](frontend/README.md)
- [Integration Summary](INTEGRATION_SUMMARY.md)
