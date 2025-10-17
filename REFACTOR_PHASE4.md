# Phase 4: Frontend Cleanup

**Risk Level:** 🟢 LOW  
**Estimated Time:** 1 hour  
**Can Break:** Frontend only (backend unaffected)  
**Prerequisites:** Phases 1-3 complete

---

## Overview

The frontend has root-level clutter and duplicate configuration management:
- **config.py** - Environment-based config (from .env)
- **settings.py** - User settings (stored in ~/.config)
- **llm_client.py** - API client (should be in utils/)
- **theme_loader.py** - Theme utilities (should be in utils/)

### Goals

1. **Consolidate utilities** into `frontend/utils/`
2. **Keep both config files** (they serve different purposes)
3. **Clean up imports** across the codebase
4. **Maintain backward compatibility**

### Why Keep Both Config Files?

- **config.py** → System configuration (API URLs, defaults) - READ ONLY
- **settings.py** → User preferences (temperature, etc.) - READ/WRITE

These serve different purposes and should remain separate.

---

## Step 1: Backup & Preparation

```bash
cd /home/tmo/Work/TalkTuah

git checkout -b refactor-phase4
git add -A
git commit -m "Before Phase 4: Frontend cleanup"
git tag phase4-start
```

---

## Step 2: Analyze Current Imports

### 2.1 Find all imports of files we're moving

```bash
cd frontend

# Find imports of llm_client
grep -rn "from llm_client\|import llm_client" . --include="*.py" | grep -v venv

# Find imports of theme_loader
grep -rn "from theme_loader\|import theme_loader" . --include="*.py" | grep -v venv
```

**Expected files to update:**
- `TuivLLM.py` - Main application
- `widgets/settings/*.py` - Settings widgets

---

## Step 3: Move llm_client.py to utils/

### 3.1 Move file

```bash
cd /home/tmo/Work/TalkTuah/frontend

# llm_client.py → utils/api_client.py (better name)
mv llm_client.py utils/api_client.py
```

### 3.2 Update utils/__init__.py

```bash
# Edit frontend/utils/__init__.py
cat > utils/__init__.py << 'EOF'
"""Utility functions and helpers for TuivLLM"""

from .markup import Markup
from .theme_helpers import get_theme_color, interpolate_color, rgb_to_hex
from .api_client import LLMClient

__all__ = [
    "Markup",
    "get_theme_color",
    "interpolate_color", 
    "rgb_to_hex",
    "LLMClient",
]
EOF
```

### 3.3 Update imports in TuivLLM.py

```bash
# Find the import line
grep -n "from llm_client import LLMClient" TuivLLM.py

# Update it
sed -i 's/from llm_client import LLMClient/from utils import LLMClient/' TuivLLM.py
```

**Or manually edit line ~14:**
```python
# OLD:
from llm_client import LLMClient

# NEW:
from utils import LLMClient
```

### 3.4 Update imports in widgets

```bash
# Check widgets/settings/ files
grep -rn "llm_client" widgets/settings/

# If found, update them:
find widgets/settings/ -name "*.py" -exec sed -i 's/from llm_client/from utils.api_client/g' {} \;
find widgets/settings/ -name "*.py" -exec sed -i 's/import llm_client/from utils import api_client/g' {} \;
```

---

## Step 4: Move theme_loader.py to utils/

### 4.1 Move file

```bash
mv theme_loader.py utils/theme.py
```

### 4.2 Update utils/__init__.py

```bash
cat > utils/__init__.py << 'EOF'
"""Utility functions and helpers for TuivLLM"""

from .markup import Markup
from .theme_helpers import get_theme_color, interpolate_color, rgb_to_hex
from .api_client import LLMClient
from .theme import ThemeLoader, get_theme, get_gradient_colors

__all__ = [
    "Markup",
    "get_theme_color",
    "interpolate_color",
    "rgb_to_hex",
    "LLMClient",
    "ThemeLoader",
    "get_theme",
    "get_gradient_colors",
]
EOF
```

### 4.3 Update imports in TuivLLM.py

```bash
# Find theme_loader imports
grep -n "from theme_loader" TuivLLM.py

# Update them
sed -i 's/from theme_loader import/from utils.theme import/g' TuivLLM.py
```

**Or manually edit (likely around line 15-17):**
```python
# OLD:
from theme_loader import ThemeLoader, get_theme, get_gradient_colors

# NEW:
from utils.theme import ThemeLoader, get_theme, get_gradient_colors
```

### 4.4 Update imports in widgets

```bash
# Check for theme_loader usage
grep -rn "theme_loader" widgets/

# Update if found
find widgets/ -name "*.py" -exec sed -i 's/from theme_loader/from utils.theme/g' {} \;
```

---

## Step 5: Clean Up Root Directory

### 5.1 Verify moves

```bash
cd /home/tmo/Work/TalkTuah/frontend

# Should NOT exist
ls -la llm_client.py theme_loader.py 2>/dev/null && echo "❌ Files still in root" || echo "✓ Files moved"

# Should exist
ls -la utils/api_client.py utils/theme.py && echo "✓ Files in utils/" || echo "❌ Missing files"
```

### 5.2 Current frontend structure

```bash
ls -1 frontend/
# Should show:
# TuivLLM.py
# config.py        # System config (keep)
# settings.py      # User settings (keep)
# version.py       # Version info (keep)
# run.sh          # Startup script (keep)
# requirements.txt # Dependencies (keep)
# utils/          # All utilities
# widgets/        # UI components
# styles/         # CSS/styling
# themes/         # Theme definitions
```

---

## Step 6: Update Documentation Comments

### 6.1 Add docstring to utils/api_client.py

```bash
# Add at top of file
cat > temp_header.txt << 'EOF'
"""
LLM API Client

Handles communication with the vLLM Proxy API including:
- Chat completions
- Model queries
- Settings integration
- Error handling

Moved from llm_client.py during Phase 4 refactoring.
"""
EOF

# Prepend to file
cat temp_header.txt utils/api_client.py > temp_file.py
mv temp_file.py utils/api_client.py
rm temp_header.txt
```

### 6.2 Add docstring to utils/theme.py

```bash
cat > temp_header.txt << 'EOF'
"""
Theme Loading and Management

Loads Omarchy theme configurations and provides gradient colors
for the TUI interface.

Moved from theme_loader.py during Phase 4 refactoring.
"""
EOF

cat temp_header.txt utils/theme.py > temp_file.py
mv temp_file.py utils/theme.py
rm temp_header.txt
```

---

## Step 7: Test Frontend

### 7.1 Check Python syntax

```bash
cd /home/tmo/Work/TalkTuah/frontend

# Check for syntax errors
python3 -m py_compile TuivLLM.py
python3 -m py_compile utils/*.py
python3 -m py_compile widgets/**/*.py
```

### 7.2 Test imports

```bash
# Test utils imports
python3 -c "from utils import LLMClient, ThemeLoader; print('✓ Utils imports work')"

# Test settings import (should still work)
python3 -c "from settings import get_settings; print('✓ Settings import works')"

# Test config import (should still work)  
python3 -c "from config import VLLM_API_URL; print('✓ Config import works')"
```

### 7.3 Run the application

```bash
cd /home/tmo/Work/TalkTuah

# Make sure backend is running
docker compose ps

# Start frontend
cd frontend
bash run.sh
```

**Test in TUI:**
1. ✅ Application starts without errors
2. ✅ Theme loads correctly (gradient colors)
3. ✅ Can send messages (API client works)
4. ✅ Settings dialog opens
5. ✅ Temperature slider works
6. ✅ Model switching works

---

## Step 8: Update Frontend README

```bash
cat >> frontend/README.md << 'EOF'

## Project Structure

```
frontend/
├── TuivLLM.py          # Main application entry point
├── config.py           # System configuration (API URLs, defaults)
├── settings.py         # User preferences (persistent settings)
├── version.py          # Version information
├── utils/              # Utility functions
│   ├── api_client.py   # LLM API client
│   ├── theme.py        # Theme loading
│   ├── theme_helpers.py # Color utilities
│   └── markup.py       # Text formatting
├── widgets/            # UI components
│   ├── chat/           # Chat interface
│   ├── layout/         # Layout components
│   └── settings/       # Settings dialog
├── styles/             # CSS styling
└── themes/             # Theme definitions
```

## Configuration Files

- **config.py** - System-level config (read from environment variables)
- **settings.py** - User-level settings (stored in `~/.config/tuivllm/`)

Both serve different purposes and are kept separate intentionally.
EOF
```

---

## Step 9: (Optional) Consolidate Config Logic

**OPTIONAL - Only if desired:**

If you want to merge config.py and settings.py logic, you could create a single configuration manager. However, this adds complexity and the current separation is clean.

**Recommendation:** Keep them separate as documented.

---

## Step 10: Commit Changes

```bash
cd /home/tmo/Work/TalkTuah

git add -A
git commit -m "Phase 4: Frontend cleanup - organize utils/, update imports"
git tag phase4-complete
```

---

## Rollback if Needed

```bash
cd /home/tmo/Work/TalkTuah/frontend

# Restore files
mv utils/api_client.py llm_client.py
mv utils/theme.py theme_loader.py

# Revert imports in TuivLLM.py
sed -i 's/from utils import LLMClient/from llm_client import LLMClient/' TuivLLM.py
sed -i 's/from utils.theme import/from theme_loader import/g' TuivLLM.py

# Rebuild utils/__init__.py without new exports
cat > utils/__init__.py << 'EOF'
"""Utility functions and helpers"""
from .markup import Markup
from .theme_helpers import get_theme_color, interpolate_color, rgb_to_hex

__all__ = [
    "Markup",
    "get_theme_color",
    "interpolate_color",
    "rgb_to_hex",
]
EOF
```

---

## Validation Checklist

- [ ] `llm_client.py` moved to `utils/api_client.py`
- [ ] `theme_loader.py` moved to `utils/theme.py`
- [ ] `utils/__init__.py` updated with exports
- [ ] All imports updated in `TuivLLM.py`
- [ ] All imports updated in `widgets/`
- [ ] No syntax errors (`python3 -m py_compile`)
- [ ] Frontend starts without errors
- [ ] Theme loads correctly
- [ ] API client works (can send messages)
- [ ] Settings dialog works
- [ ] No regression in functionality
- [ ] README updated with new structure
- [ ] Changes committed
- [ ] Tag `phase4-complete` created

---

## Final Frontend Structure

```
frontend/
├── TuivLLM.py              # Main app (18KB)
├── config.py               # System config ✓
├── settings.py             # User settings ✓
├── version.py              # Version info ✓
├── run.sh                  # Startup script ✓
├── requirements.txt        # Dependencies ✓
├── utils/                  # ✨ All utilities organized
│   ├── __init__.py
│   ├── api_client.py       # ✨ Moved from llm_client.py
│   ├── theme.py            # ✨ Moved from theme_loader.py
│   ├── theme_helpers.py
│   └── markup.py
├── widgets/                # UI components ✓
│   ├── chat/
│   ├── layout/
│   └── settings/
├── styles/                 # Styling ✓
└── themes/                 # Theme defs ✓
```

**Improvements:**
- ✅ Cleaner root directory (7 files → 6 files)
- ✅ All utilities organized in `utils/`
- ✅ Clear separation of concerns
- ✅ Easier to find and maintain code
- ✅ Consistent with backend structure

---

**Next:** Review REFACTOR_CHECKLIST.md and mark Phase 4 complete!

## 🎉 All Phases Complete!

After Phase 4:
1. ✅ Structure cleaned up (no misleading dirs)
2. ✅ API refactored (744 lines → 55 lines)
3. ✅ Duplicate logic eliminated (pure Python)
4. ✅ Frontend organized (utils consolidated)

**Time to delete the refactor checklists and celebrate!** 🎊
