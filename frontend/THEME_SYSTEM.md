# TuivLLM Theme System Implementation

## Overview

TuivLLM now has a btop-style configuration and theme system that allows users to customize colors and behavior through simple text files.

## Files Created

### Configuration
- `tuivllm.conf` - Main configuration file (btop-style)
- `theme_loader.py` - Python module to load config and themes

### Themes
- `themes/terminal.theme` - Default theme using ANSI colors
- `themes/catppuccin.theme` - Catppuccin Latte theme
- `themes/dracula.theme` - Dracula theme
- `themes/gruvbox.theme` - Gruvbox Dark theme

### Documentation
- `THEMES.md` - Complete theme system documentation

## How It Works

### 1. Configuration Loading

The `theme_loader.py` module provides a `ThemeLoader` class that:
- Searches for config files in multiple locations
- Parses btop-style configuration syntax
- Provides type-safe accessors (get_bool, get_int, get_color)

```python
from theme_loader import get_theme_loader

theme = get_theme_loader()
user_color = theme.get_color("user_color", "cyan")
show_timestamps = theme.get_bool("show_timestamps", True)
```

### 2. Theme Files

Theme files use the same format as btop:

```
# Comment
theme[key]="value"
```

Supported color formats:
- ANSI names: `"cyan"`, `"bright_red"`, etc.
- Hex colors: `"#ff5555"`
- RGB: `"rgb(255,85,85)"`

### 3. Integration with TuivLLM

The `TuivLLM.py` file now:
- Imports `theme_loader`
- Loads theme colors dynamically in `ChatMessage.render()`
- Can be extended to use theme colors in CSS

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `color_theme` | string | `"terminal"` | Theme file to load |
| `theme_background` | bool | `True` | Show theme background |
| `truecolor` | bool | `True` | Use 24-bit colors |
| `rounded_corners` | bool | `True` | Rounded message boxes |
| `show_timestamps` | bool | `True` | Show message timestamps |
| `timestamp_format` | string | `"%H:%M:%S"` | strftime format |
| `max_history` | int | `100` | Max messages (0=unlimited) |
| `auto_scroll` | bool | `True` | Auto-scroll to bottom |
| `show_connection_status` | bool | `True` | Show status bar |
| `vim_keys` | bool | `False` | Vim keybindings |

## Theme Colors

| Key | Description | Default |
|-----|-------------|---------|
| `main_bg` | Background color | `""` (transparent) |
| `main_fg` | Text color | `""` (terminal default) |
| `user_color` | User message box | `"cyan"` |
| `ai_color` | AI message box | `"yellow"` |
| `system_color` | System messages | `"bright_black"` |
| `border_color` | Container borders | `"cyan"` |
| `status_connected` | Connected status | `"green"` |
| `status_processing` | Processing status | `"yellow"` |
| `status_error` | Error status | `"red"` |
| `scrollbar_color` | Scrollbar | `"cyan"` |
| `scrollbar_hover` | Scrollbar hover | `"bright_cyan"` |
| `scrollbar_active` | Scrollbar active | `"bright_cyan"` |
| `input_border` | Input box border | `"cyan"` |
| `timestamp_color` | Timestamp text | `"bright_black"` |

## Usage

### For Users

1. **Use default theme** (terminal colors):
   - No configuration needed
   - Colors adapt to your terminal theme

2. **Switch to a built-in theme**:
   ```bash
   # Edit tuivllm.conf
   color_theme = "catppuccin"
   ```

3. **Create custom theme**:
   ```bash
   mkdir -p ~/.config/tuivllm/themes
   cp themes/terminal.theme ~/.config/tuivllm/themes/mytheme.theme
   # Edit mytheme.theme
   # Set color_theme = "mytheme" in tuivllm.conf
   ```

### For Developers

To add theme support to a new component:

```python
from theme_loader import get_theme_loader

class MyWidget(Static):
    def render(self):
        theme = get_theme_loader()
        color = theme.get_color("my_color", "white")
        return f"[{color}]Styled text[/]"
```

## Future Enhancements

Potential additions:
- [ ] Runtime theme switching (no restart)
- [ ] Theme preview command
- [ ] More built-in themes
- [ ] Theme validation tool
- [ ] CSS variable integration
- [ ] Gradient support
- [ ] Animation settings
- [ ] Font settings

## Comparison with btop

| Feature | btop | TuivLLM | Status |
|---------|------|---------|--------|
| Config file | ✅ | ✅ | Implemented |
| Theme files | ✅ | ✅ | Implemented |
| Multiple locations | ✅ | ✅ | Implemented |
| Color formats | ✅ | ✅ | Implemented |
| Runtime reload | ✅ | ⏳ | Planned |
| Presets | ✅ | ❌ | Not needed |
| Graph symbols | ✅ | ❌ | Not applicable |

## Testing

To test the theme system:

1. **Test default theme**:
   ```bash
   make frontend
   ```

2. **Test theme switching**:
   ```bash
   # Edit tuivllm.conf
   color_theme = "dracula"
   make frontend
   ```

3. **Test custom theme**:
   ```bash
   cp themes/terminal.theme themes/test.theme
   # Modify test.theme
   # Set color_theme = "test"
   make frontend
   ```

## Notes

- The theme system is fully backward compatible
- If no config/theme is found, sensible defaults are used
- ANSI colors adapt to terminal themes automatically
- Hex colors provide precise control but don't adapt
- Empty string for background enables transparency

## Credits

Inspired by:
- [btop++](https://github.com/aristocratos/btop) - Configuration system
- [Catppuccin](https://github.com/catppuccin/catppuccin) - Color palette
- [Dracula](https://draculatheme.com/) - Color palette
- [Gruvbox](https://github.com/morhetz/gruvbox) - Color palette
