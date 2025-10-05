# Talk-Tuah 🎤

A beautiful terminal UI chatbot with dynamic gradient text and Omarchy theme integration, powered by vLLM.

## ✨ Features

- 🎨 **Dynamic Gradient Text** - Stationary gradient that messages scroll through
- 🎭 **Omarchy Theme Integration** - Automatically syncs with your system theme
- ⚡ **Real-time Streaming** - Fast SSE-based responses
- 💾 **System Monitoring** - Live RAM and VRAM usage display
- 🔧 **vLLM Backend** - High-performance GPU inference
- 🐳 **Docker Compose** - Easy deployment with GPU support

## 🚀 Quick Start

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
- Top of screen: Red (gradient_top)
- Middle: Orange (gradient_mid)  
- Bottom: Green (gradient_bottom)

Messages scroll through the stationary gradient for a beautiful effect.

## ⌨️ Keyboard Shortcuts

- `Ctrl+C` / `Ctrl+Q` - Quit
- `Ctrl+L` - Clear chat
- `Ctrl+R` - Reconnect to backend
- `Enter` - Send message

## 📝 Configuration

Edit `.env` to configure:

```bash
# Model (see vLLM supported models)
DEFAULT_MODEL=Qwen/Qwen2.5-1.5B-Instruct

# API Key
PROXY_API_KEY=change-me-hehehoho

# HuggingFace Token (for gated models like Llama)
HF_TOKEN=hf_xxxxxxxxxxxxxxxxx
```

## 🛠️ Commands

```bash
make up           # Start backend
make down         # Stop backend
make logs         # View logs
make frontend     # Run TUI
make test         # Run tests
```

## 📚 Documentation

- [GPU Setup](docs/GPU_SETUP.md) - NVIDIA GPU configuration
- [Cheatsheet](docs/CHEATSHEET.md) - All commands and shortcuts
- [Themes](docs/THEMES.md) - Theme customization guide
- [Changelog](docs/CHANGELOG.md) - Version history

## 🐛 Troubleshooting

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

## 📦 Requirements

- Docker & Docker Compose with GPU support
- NVIDIA GPU with 16GB+ VRAM (for 7B models)
- NVIDIA Container Toolkit
- Python 3.11+ (for TUI)

## 📄 License

MIT

---

**Built with vLLM** | [GitHub](https://github.com/KelpME/TalkTuah)
