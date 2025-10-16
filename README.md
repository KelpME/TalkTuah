# Talk-Tuah

A beautiful terminal UI chatbot with dynamic gradient text and Omarchy theme integration, powered by vLLM.

## Features

- **Dynamic Gradient Text** - Stationary gradient that messages scroll through
- **Omarchy Theme Integration** - Automatically syncs with your system theme
- **Real-time Streaming** - Fast SSE-based responses
- **System Monitoring** - Live RAM and VRAM usage display
- **vLLM Backend** - High-performance GPU inference
- **Docker Compose** - Easy deployment with GPU support

## Quick Start

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

## Theme System

Talk-Tuah automatically syncs with your Omarchy theme:

```bash
# Your theme changes are detected automatically
omarchy theme set <theme-name>
# TUI updates colors in real-time!
```

**How it works:**

The gradient uses three colors from your Omarchy theme's `btop.theme` file:
- **Top of screen** → `theme[gradient_top]` (usually red/orange)
- **Middle of screen** → `theme[gradient_mid]` (usually teal/cyan)
- **Bottom of screen** → `theme[gradient_bottom]` (usually green)

Messages scroll through this stationary gradient - text changes color based on its position on screen, creating a beautiful flowing effect.

## Keyboard Shortcuts

- `Ctrl+C` / `Ctrl+Q` - Quit
- `Ctrl+L` - Clear chat
- `Ctrl+R` - Reconnect to backend
- `Enter` - Send message

## Configuration

Edit `.env` to configure:

```bash
# Model (see vLLM supported models)
DEFAULT_MODEL=Qwen/Qwen2.5-1.5B-Instruct

# API Key
PROXY_API_KEY=change-me-hehehoho

# HuggingFace Token (for gated models like Llama)
HF_TOKEN=hf_xxxxxxxxxxxxxxxxx
```

## Commands

```bash
make up           # Start backend
make down         # Stop backend
make logs         # View logs
make restart      # Restart services
make apply        # Apply TUI settings and restart
make frontend     # Run TUI
make sync-settings # Sync TUI settings to .env
make test         # Run tests
```

## Documentation

- [Documentation Index](docs/README.md) - Complete documentation hub
- [ROCm Setup](docs/setup/rocm.md) - AMD GPU configuration
- [GPU Memory](docs/setup/gpu-memory.md) - Memory allocation and N8n integration
- [Keyboard Shortcuts](docs/user/keyboard-shortcuts.md) - All commands and shortcuts
- [Themes](docs/user/themes.md) - Theme customization guide
- [Changelog](docs/changelog/CHANGELOG.md) - Version history

## Troubleshooting

**Backend won't start:**
```bash
# Check logs
make logs

# Verify GPU
nvidia-smi
```

**TUI can't connect:**
```bash
# Check backend health
curl http://localhost:8787/api/healthz
```

## Requirements

- Docker & Docker Compose with GPU support
- AMD Ryzen AI Max+ 395 APU with ROCm 6.4.3+
- Shared memory architecture (configurable GPU allocation)
- Python 3.11+ (for TUI)

## License

Apache 2.0

---

**Built with vLLM** | [GitHub](https://github.com/KelpME/TalkTuah)
