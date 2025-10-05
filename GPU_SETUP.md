# GPU Setup for vLLM on Arch Linux

## Prerequisites

You need:
- NVIDIA GPU with 16GB+ VRAM (for 7B models)
- NVIDIA drivers installed
- Docker installed

## Step 1: Verify NVIDIA Drivers

```bash
nvidia-smi
```

You should see your GPU listed. If not, install NVIDIA drivers:

```bash
sudo pacman -S nvidia nvidia-utils
```

## Step 2: Install NVIDIA Container Toolkit

```bash
# Install the package
sudo pacman -S nvidia-container-toolkit
```

## Step 3: Configure Docker

```bash
# Configure Docker to use NVIDIA runtime
sudo nvidia-ctk runtime configure --runtime=docker

# Restart Docker daemon
sudo systemctl restart docker
```

## Step 4: Verify GPU Access in Docker

```bash
# Test that Docker can access the GPU
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

You should see the same output as the host `nvidia-smi` command.

## Step 5: Start vLLM Services

```bash
# From project root
make up

# Watch logs (model loading takes 1-5 minutes)
make logs
```

Wait until you see:
```
vllm-server     | INFO:     Application startup complete.
vllm-proxy-api  | INFO:     Application startup complete.
```

## Step 6: Test the API

```bash
# Check health
curl http://localhost:8787/api/healthz
```

Expected output:
```json
{
  "status": "healthy",
  "gpu_available": true,
  "model_loaded": true,
  "upstream_healthy": true
}
```

## Step 7: Run the Frontend

```bash
make frontend
```

## Troubleshooting

### "could not select device driver nvidia"

**Cause:** NVIDIA Container Toolkit not installed or Docker not configured

**Solution:**
```bash
# Install toolkit
sudo pacman -S nvidia-container-toolkit

# Configure Docker
sudo nvidia-ctk runtime configure --runtime=docker

# Restart Docker
sudo systemctl restart docker
```

### "CUDA driver version is insufficient"

**Cause:** NVIDIA drivers are outdated

**Solution:**
```bash
# Update drivers
sudo pacman -Syu nvidia nvidia-utils

# Reboot
sudo reboot
```

### "Out of memory" during model loading

**Cause:** GPU doesn't have enough VRAM

**Solution:** Reduce model size or context length in `.env`:
```bash
MAX_MODEL_LEN=4096  # Reduce from 8192
```

Or use a smaller model:
```bash
DEFAULT_MODEL=microsoft/Phi-3-mini-4k-instruct  # 3.8B parameters
```

### Docker daemon not starting after configuration

**Solution:**
```bash
# Check Docker status
sudo systemctl status docker

# View logs
sudo journalctl -u docker -n 50

# Reset Docker config if needed
sudo rm /etc/docker/daemon.json
sudo systemctl restart docker
```

## Verification Script

Run the verification script to check all prerequisites:

```bash
./verify_setup.sh
```

This will check:
- Docker installation
- Docker Compose
- NVIDIA GPU availability
- NVIDIA Container Toolkit
- Service status
- API health

## Alternative: CPU-Only Mode (Not Recommended)

If you don't have a GPU, you can run vLLM in CPU mode (very slow):

1. Remove GPU requirements from `docker-compose.yml`:
   ```yaml
   # Comment out or remove:
   deploy:
     resources:
       reservations:
         devices:
           - driver: nvidia
             count: all
             capabilities: [gpu]
   ```

2. Use CPU-compatible vLLM image:
   ```yaml
   image: vllm/vllm-openai:v0.11.0-cpu
   ```

**Warning:** CPU inference is 10-100x slower than GPU and not recommended for production.

## System Requirements

### Minimum (7B models)
- GPU: NVIDIA RTX 3090 (24GB VRAM)
- RAM: 32GB
- Storage: 50GB free (for Docker images + model cache)

### Recommended (7B models)
- GPU: NVIDIA A100 (40GB VRAM) or H100 (80GB VRAM)
- RAM: 64GB
- Storage: 100GB SSD

### For Larger Models (13B-70B)
- GPU: 2-8x A100 or H100 with NVLink
- RAM: 128GB+
- Storage: 200GB+ SSD

## GPU Memory Requirements by Model

| Model | Parameters | VRAM (FP16) | VRAM (INT8) | VRAM (INT4) |
|-------|-----------|-------------|-------------|-------------|
| Phi-3 Mini | 3.8B | ~8 GB | ~4 GB | ~2 GB |
| Llama 3.1 | 8B | ~16 GB | ~8 GB | ~4 GB |
| Mistral | 7B | ~14 GB | ~7 GB | ~4 GB |
| Llama 3.1 | 70B | ~140 GB | ~70 GB | ~35 GB |

**Note:** Add 2-4GB for KV cache depending on `MAX_MODEL_LEN`.

## Next Steps

After GPU setup is complete:

1. **Configure environment**: Edit `.env` with your API key and HF token
2. **Start services**: `make up`
3. **Run tests**: `make test`
4. **Launch frontend**: `make frontend`
5. **Monitor**: Check metrics at `http://localhost:8787/metrics`

## Additional Resources

- [NVIDIA Container Toolkit Docs](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
- [vLLM Installation Guide](https://docs.vllm.ai/en/latest/getting_started/installation.html)
- [Docker GPU Support](https://docs.docker.com/config/containers/resource_constraints/#gpu)
