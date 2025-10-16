# TuivLLM - Terminal UI Chat Interface

Beautiful terminal-based chat interface for vLLM, built with [Textual](https://textual.textualize.io/).

## Features

- 🎨 **BTOP++ Inspired Design** - Modern, aesthetic terminal UI
- 🎨 **Theme System** - btop-style configuration with multiple themes
- 💬 **Real-time Chat** - Interactive conversation with vLLM models
- 🔐 **Authenticated** - Secure connection to vLLM proxy API
- 📝 **Conversation History** - Maintains context across messages
- ⌨️ **Keyboard Shortcuts** - Efficient terminal navigation
- 🎯 **Configurable** - Easy model and endpoint switching
- 🌈 **Terminal Colors** - Adapts to your terminal's color scheme

## Screenshots

```
┌─────────────────────────────────────────────────────────────────┐
│ TuivLLM ── AI Chat Terminal                          11:30:45   │
├─────────────────────────────────────────────────────────────────┤
│ ╭──┤ STATUS ├── ● Connected │ Endpoint: http://localhost:8787  │
│                                                                  │
│ ╮ CONVERSATION ╭                                                │
│ ┌──────────────────────────────────────────────────────────────┐│
│ │ ╭──┤ YOU │ 11:30:12 ├─────────────────────────────────────╮ ││
│ │ │ What is quantum computing?                              │ ││
│ │ ╰─────────────────────────────────────────────────────────╯ ││
│ │                                                              ││
│ │ ╭──┤ AI │ 11:30:15 ├──────────────────────────────────────╮ ││
│ │ │ Quantum computing is a type of computing that uses      │ ││
│ │ │ quantum-mechanical phenomena to perform operations...   │ ││
│ │ ╰─────────────────────────────────────────────────────────╯ ││
│ └──────────────────────────────────────────────────────────────┘│
│                                                                  │
│ ╮ INPUT ╭                                                       │
│ ┌──────────────────────────────────────────────────────────────┐│
│ │ Type your message here... (Enter to send, Ctrl+L to clear)  ││
│ └──────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│ Ctrl+C Quit │ Ctrl+L Clear │ Ctrl+R Reconnect                  │
└─────────────────────────────────────────────────────────────────┘
```

## Installation

### Option 1: Quick Install (Recommended)

From the project root:

```bash
make install-frontend
```

### Option 2: Manual Install

```bash
cd frontend
pip install -r requirements.txt
```

### Option 3: Virtual Environment

```bash
cd frontend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

### Prerequisites

Ensure the vLLM backend is running:

```bash
# From project root
make up

# Wait for services to be healthy
make logs
```

### Run the TUI

**Option 1: Using Makefile (from project root)**

```bash
make frontend
```

**Option 2: Using run script**

```bash
cd frontend
bash run.sh
```

**Option 3: Direct Python**

```bash
cd frontend
python TuivLLM.py
```

## Configuration

### Themes and Appearance

TuivLLM uses a btop-style configuration system with theme support.

**Quick start:**

```bash
# Copy example config
cp tuivllm.conf.example tuivllm.conf

# Edit to change theme
# Available themes: terminal, catppuccin, dracula, gruvbox
color_theme = "dracula"
```

**Built-in themes:**
- `system` - Automatically uses your system's current theme (omarchy/btop) ⭐ **Default**
- `terminal` - Uses ANSI colors that adapt to your terminal

**Live theme reload!** TuivLLM watches `~/.config/omarchy/current/theme/btop.theme` and updates colors in real-time when you switch themes. No restart needed!

**Zero configuration:** Just run TuivLLM and it automatically matches your Omarchy theme. Switch themes with `omarchy-theme-next` and watch TuivLLM update instantly.

### API Configuration

The frontend reads API configuration from environment variables. These can be set in the parent `.env` file or exported directly.

### Environment Variables

```bash
# vLLM Proxy API URL
VLLM_API_URL=http://localhost:8787/api

# API Authentication Key
PROXY_API_KEY=your-secret-key-here

# Model to use
DEFAULT_MODEL=meta-llama/Meta-Llama-3.1-8B-Instruct
```

### Editing config.py

You can also edit `frontend/config.py` directly:

```python
# vLLM Proxy API Configuration
VLLM_API_URL = "http://localhost:8787/api"
VLLM_API_KEY = "your-secret-key-here"
VLLM_MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct"

# Request Configuration
LMSTUDIO_TIMEOUT = 60.0
LMSTUDIO_MAX_TOKENS = 500
LMSTUDIO_TEMPERATURE = 0.7
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Send message |
| `Ctrl+C` or `Ctrl+Q` | Quit application |
| `Ctrl+L` | Clear chat history |
| `Ctrl+R` | Reconnect to API |
| `Tab` | Navigate between widgets |

## Features

### Conversation History

The TUI maintains conversation context automatically:
- Last 10 messages kept in memory
- System prompt included for consistency
- Clear history with `Ctrl+L`

### Error Handling

Graceful error messages for common issues:
- Connection failures → Instructions to start backend
- Timeouts → Suggestions to reduce max_tokens
- Auth errors → Check API key configuration

### Status Bar

Real-time connection status:
- 🟢 **Connected** - API is responding
- 🟡 **Processing** - Waiting for model response
- 🔴 **Error** - Connection or API issue

## Troubleshooting

### "Cannot connect to vLLM API"

**Solution:**

1. Ensure backend is running:
   ```bash
   make up
   ```

2. Check health:
   ```bash
   curl http://localhost:8787/api/healthz
   ```

3. Verify logs:
   ```bash
   make logs
   ```

### "Error: API returned status 401"

**Solution:** Check your API key in `.env`:

```bash
# .env
PROXY_API_KEY=your-actual-key-here
```

### "Request timed out"

**Solutions:**

1. Reduce `max_tokens` in `config.py`:
   ```python
   LMSTUDIO_MAX_TOKENS = 256  # Lower value
   ```

2. Check GPU utilization:
   ```bash
   nvidia-smi
   ```

3. Monitor vLLM metrics:
   ```bash
   curl http://localhost:8000/metrics | grep queue
   ```

### Terminal Display Issues

**Solution:** Ensure terminal supports Unicode and colors:

```bash
# Set terminal to UTF-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# Use a modern terminal emulator
# Recommended: iTerm2 (macOS), Windows Terminal, Alacritty, Kitty
```

## Development

### Project Structure

```
frontend/
├── TuivLLM.py          # Main TUI application
├── llm_client.py       # vLLM API client
├── config.py           # Configuration
├── requirements.txt    # Python dependencies
├── run.sh             # Startup script
├── Dockerfile         # Container image (optional)
└── README.md          # This file
```

### Customization

**Change Colors:**

Edit `config.py`:

```python
COLORS = {
    "positive": "green",
    "neutral": "yellow", 
    "negative": "red",
    "primary": "cyan",
}
```

**Modify System Prompt:**

Edit `config.py`:

```python
LLM_SYSTEM_PROMPT = """Your custom system prompt here."""
```

**Adjust Timeouts:**

Edit `config.py`:

```python
LMSTUDIO_TIMEOUT = 120.0  # Increase for longer responses
```

## Dependencies

- **textual** (0.47.1) - TUI framework
- **httpx** (0.27.2) - Async HTTP client
- **rich** (13.7.0) - Terminal formatting
- **python-dotenv** (1.0.1) - Environment variable loading

## Integration with Backend

The TUI connects to the vLLM proxy API:

```
TuivLLM (frontend) → FastAPI Proxy (apps/api) → vLLM Server (services/vllm)
     Port: N/A           Port: 8787                  Port: 8000
```

**API Endpoints Used:**

- `POST /api/chat` - Send messages and receive responses
- Authentication via `Bearer` token in `Authorization` header

## Docker Support (Optional)

Build and run in Docker:

```bash
# Build image
docker build -t tuivllm frontend/

# Run with host network (for API access)
docker run -it --rm \
  --network host \
  -e PROXY_API_KEY=your-key \
  tuivllm
```

## License

MIT

## Credits

- Built with [Textual](https://textual.textualize.io/)
- Inspired by [BTOP++](https://github.com/aristocratos/btop) design
- Powered by [vLLM](https://github.com/vllm-project/vllm)
