# System Theme Integration - Implementation Summary

## Overview

TuivLLM now integrates directly with your system's theme manager (omarchy/btop), eliminating theme duplication and ensuring visual consistency across all terminal applications.

## What Changed

### Before: Theme Duplication ❌
```
~/.config/btop/themes/dracula.theme
~/.config/tuivllm/themes/dracula.theme    # Duplicate!
~/.config/tuivllm/themes/catppuccin.theme # Duplicate!
~/.config/tuivllm/themes/gruvbox.theme    # Duplicate!
```

### After: Single Source of Truth ✅
```
~/.config/omarchy/current/btop.theme      # One theme
# TuivLLM reads from this automatically
# btop reads from this
# All terminal apps can share this
```

## How It Works

1. **Default behavior** (`color_theme = "system"`):
   - Reads `~/.config/omarchy/current/btop.theme`
   - Parses btop theme format
   - Maps btop colors to TuivLLM UI elements
   - Updates automatically when you switch system themes

2. **Fallback behavior**:
   - If no system theme found → uses terminal ANSI colors
   - If terminal.theme exists → uses that
   - Always has sensible defaults

3. **Custom themes still supported**:
   - Create `~/.config/tuivllm/themes/custom.theme`
   - Set `color_theme = "custom"`
   - Overrides system theme

## Color Mapping Logic

```python
# User messages → CPU box color (typically blue/cyan)
user_color = btop_theme["cpu_box"]

# AI messages → Memory box color (typically green/purple)
ai_color = btop_theme["mem_box"]

# Borders → Divider line color
border_color = btop_theme["div_line"]

# Status indicators → Temperature gradient
status_connected = btop_theme["temp_start"]  # Green
status_processing = btop_theme["temp_mid"]   # Yellow
status_error = btop_theme["temp_end"]        # Red

# And more...
```

## Files Modified

### Core Implementation
- `theme_loader.py`:
  - Added `_load_system_theme()` method
  - Added `_parse_btop_theme()` method
  - Added `_map_btop_to_tuivllm()` method
  - Changed default from `"terminal"` to `"system"`

### Configuration
- `tuivllm.conf.example`:
  - Updated default to `color_theme = "system"`
  - Added documentation about system theme

### Themes Cleaned Up
- **Removed**: `catppuccin.theme`, `dracula.theme`, `gruvbox.theme`
- **Kept**: `terminal.theme` (fallback for non-omarchy users)

### Documentation
- Created `SYSTEM_THEME.md` - System integration guide
- Updated `THEMES.md` - Reflects new default
- Updated `QUICKSTART_THEMES.md` - New workflow
- Updated `README.md` - System theme info
- Updated main `README.md` - Project-level docs

## Benefits

### For Users
✅ **Zero configuration** - Works out of the box  
✅ **Automatic synchronization** - Change theme once, affects everything  
✅ **No duplication** - One theme file for all apps  
✅ **Consistent look** - All terminal apps match  
✅ **Less maintenance** - Fewer files to manage  

### For Developers
✅ **Less code to maintain** - No bundled themes  
✅ **Smaller repository** - Removed redundant files  
✅ **Better integration** - Follows system conventions  
✅ **Extensible** - Easy to add more theme sources  

## Usage Examples

### Example 1: Default (System Theme)
```bash
# No configuration needed
make frontend
# Automatically uses ~/.config/omarchy/current/btop.theme
```

### Example 2: Switch System Theme
```bash
# Switch theme system-wide (using omarchy or btop)
omarchy theme nord

# Run TuivLLM - colors automatically update
make frontend
```

### Example 3: Custom Theme
```bash
# Create custom theme
mkdir -p ~/.config/tuivllm/themes
cat > ~/.config/tuivllm/themes/custom.theme << 'EOF'
theme[user_color]="#00ff00"
theme[ai_color]="#ff00ff"
EOF

# Use custom theme
echo 'color_theme = "custom"' > frontend/tuivllm.conf
make frontend
```

### Example 4: Terminal ANSI Colors
```bash
# Use terminal's ANSI colors instead of system theme
echo 'color_theme = "terminal"' > frontend/tuivllm.conf
make frontend
```

## Technical Details

### Theme Search Order
1. Check if `theme_name == "system"`
2. If yes:
   - Try `~/.config/omarchy/current/btop.theme`
   - Try `~/.config/btop/themes/current.theme`
   - Fallback to terminal ANSI colors
3. If no:
   - Try `~/.config/tuivllm/themes/{theme_name}.theme`
   - Try `./themes/{theme_name}.theme`
   - Fallback to defaults

### btop Theme Parser
- Handles `theme[key]="value"` syntax
- Strips quotes and whitespace
- Ignores comments (`#`)
- Returns dict of key-value pairs

### Color Mapper
- Maps 14 btop colors to TuivLLM elements
- Provides sensible fallbacks for each
- Preserves hex colors, ANSI names, RGB values

## Compatibility

### Works With
✅ omarchy theme manager  
✅ btop++ themes  
✅ Any btop-compatible theme  
✅ Custom themes  
✅ Terminal ANSI colors  

### Fallback Chain
```
system theme → btop theme → terminal colors → hardcoded defaults
```

## Migration Guide

### For Existing Users

**If you had custom themes:**
```bash
# Old location
~/.config/tuivllm/themes/mytheme.theme

# Still works! No changes needed
color_theme = "mytheme"
```

**If you used bundled themes:**
```bash
# Old: color_theme = "dracula"
# New: Use system theme instead

# Option 1: Switch to system theme
color_theme = "system"
# Then switch your system theme to dracula

# Option 2: Create custom theme
cp old_dracula.theme ~/.config/tuivllm/themes/dracula.theme
color_theme = "dracula"
```

**If you had no config:**
```bash
# Old: Used terminal colors
# New: Uses system theme (better!)
# No action needed - automatic upgrade
```

## Testing

Test the system theme integration:

```bash
# Test system theme loading
cd frontend
python3 << 'EOF'
from theme_loader import get_theme_loader
loader = get_theme_loader()
print("Theme:", loader.config.get("color_theme"))
print("Colors loaded:", len(loader.theme))
print("User color:", loader.get_color("user_color"))
print("AI color:", loader.get_color("ai_color"))
EOF
```

Expected output:
```
Theme: system
Colors loaded: 14
User color: <color from btop theme>
AI color: <color from btop theme>
```

## Future Enhancements

Potential improvements:
- [ ] Watch btop theme file for changes (auto-reload)
- [ ] Support more theme managers (kitty, alacritty, etc.)
- [ ] Theme preview command
- [ ] Color contrast validation
- [ ] Theme export/import

## Summary

✅ **Implemented**: System theme integration  
✅ **Default**: Reads from `~/.config/omarchy/current/btop.theme`  
✅ **Cleaned**: Removed duplicate theme files  
✅ **Documented**: Complete guides and examples  
✅ **Tested**: Works with omarchy/btop themes  
✅ **Backward compatible**: Custom themes still work  

**Result**: TuivLLM now seamlessly integrates with your system's theme, providing a consistent terminal experience with zero configuration!
