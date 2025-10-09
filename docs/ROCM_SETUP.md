# ROCm Setup for AMD GPUs (Ryzen AI Max+ 395)

## Prerequisites

Your system has:
- AMD Ryzen AI Max+ 395 APU
- Radeon 8060S iGPU (gfx1151 - RDNA 3.5)
- ROCm 6.4.3 installed
- Up to 16GB VRAM available

## Step 1: Verify ROCm Installation

```bash
# Check ROCm version
pacman -Q | grep rocm

# Check GPU detection
/opt/rocm/bin/rocminfo | grep -i gfx

# Should show: gfx1151
```

## Step 2: Verify User Permissions

Your user needs to be in the `video` and `render` groups:

```bash
# Check current groups
groups

# Add yourself to groups (if not already)
sudo usermod -aG video,render $USER

# Log out and back in for changes to take effect
```

## Step 3: Test ROCm with Docker

```bash
# Test ROCm access in Docker
docker run --rm -it \
  --device=/dev/kfd --device=/dev/dri \
  --group-add video --group-add render \
  rocm/pytorch:latest \
  rocminfo | grep gfx

# Should show your GPU: gfx1151
```

## Step 4: Configure Environment

The `docker-compose.yml` has been configured with:
- **ROCm vLLM image**: `vllm/vllm-openai:v0.6.3.post1-rocm`
- **GFX override**: `HSA_OVERRIDE_GFX_VERSION=11.0.0` (gfx1151 compatibility)
- **Device access**: `/dev/kfd` and `/dev/dri`
- **Group permissions**: `video` and `render`

## Step 5: Start Services

```bash
# Configure your .env file
cp .env.example .env
# Edit .env: set PROXY_API_KEY and HF_TOKEN

# Start with a small model first (recommended for testing)
echo "DEFAULT_MODEL=Qwen/Qwen2.5-1.5B-Instruct" >> .env

# Start services
make up

# Watch logs (model loading takes 2-5 minutes)
make logs
```

## Recommended Models for 16GB VRAM

| Model | Size | VRAM Usage | Performance |
|-------|------|------------|-------------|
| Qwen2.5-1.5B-Instruct | 1.5B | ~3GB | Fast, good for testing |
| Phi-3-mini-4k | 3.8B | ~8GB | Excellent quality |
| Qwen2.5-7B-Instruct | 7B | ~14GB | Best quality (tight fit) |
| Mistral-7B-Instruct | 7B | ~14GB | Great general purpose |

**Start with 1.5B or 3.8B models to verify everything works!**

## Troubleshooting

### "Could not initialize ROCR runtime"

**Cause:** Incorrect permissions or device access

**Solution:**
```bash
# Verify groups
groups | grep -E "video|render"

# If missing, add and restart
sudo usermod -aG video,render $USER
# Log out and back in

# Verify devices exist
ls -la /dev/kfd /dev/dri/
```

### "GPU not detected" or "No HSA agents found"

**Cause:** GFX version mismatch

**Solution:**
The gfx1151 is very new. Try different GFX override values in `.env`:
```bash
# Add to .env
HSA_OVERRIDE_GFX_VERSION=11.0.0  # Current setting
# Or try:
# HSA_OVERRIDE_GFX_VERSION=11.5.1
# HSA_OVERRIDE_GFX_VERSION=11.0.1
```

Then restart: `make restart`

### "Out of memory" during model loading

**Cause:** Model too large for 16GB VRAM

**Solution:**
```bash
# Use smaller model
DEFAULT_MODEL=Qwen/Qwen2.5-1.5B-Instruct

# Or reduce context window
MAX_MODEL_LEN=2048
```

### Docker permission denied

**Cause:** User not in docker group

**Solution:**
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

## Performance Tips

### 1. Optimize Memory Usage
```bash
# In .env
MAX_MODEL_LEN=4096          # Reduce if needed
gpu-memory-utilization=0.85  # Increase from 0.75 if stable
```

### 2. Monitor VRAM Usage
```bash
# Install radeontop (optional)
sudo pacman -S radeontop

# Monitor in real-time
radeontop
```

### 3. Check Performance
```bash
# Run benchmark
make bench

# Check metrics
curl http://localhost:8787/metrics
```

## Next Steps

After successful startup:

1. **Test API**: `curl http://localhost:8787/api/healthz`
2. **Run frontend**: `make frontend`
3. **Try larger models**: Upgrade to 3.8B or 7B once stable

## Known Issues with gfx1151

The Radeon 8060S (gfx1151) is cutting edge and may have:
- Limited vLLM testing/optimization
- Potential ROCm compatibility quirks
- Performance may vary vs discrete GPUs

If you encounter issues:
1. Try the CPU fallback image temporarily
2. Check vLLM GitHub for gfx1151 support status
3. Consider reporting compatibility issues upstream

## Resources

- [ROCm Documentation](https://rocm.docs.amd.com/)
- [vLLM ROCm Support](https://docs.vllm.ai/en/latest/getting_started/amd-installation.html)
- [AMD GPU Compatibility](https://rocm.docs.amd.com/en/latest/release/gpu_os_support.html)
