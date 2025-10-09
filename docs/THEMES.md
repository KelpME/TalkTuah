# TuivLLM Themes

TuivLLM uses a btop-style configuration and theme system that allows you to customize colors and behavior.

## Configuration File

The main configuration file is `tuivllm.conf` and can be placed in:
- `~/.config/tuivllm/tuivllm.conf` (user config)
- `./tuivllm.conf` (local config in frontend directory)

### Configuration Options

```conf
#* Name of a theme file
color_theme = "terminal"

#* Show theme background (False for transparency)
theme_background = True

#* Use 24-bit truecolor
truecolor = True

#* Rounded corners on message boxes
rounded_corners = True

#* Show timestamps on messages
show_timestamps = True

#* Timestamp format (strftime)
timestamp_format = "%H:%M:%S"

#* Maximum messages in history (0 = unlimited)
max_history = 100

#* Auto-scroll to bottom
auto_scroll = True

#* Show connection status
show_connection_status = True

#* Enable vim keybindings
vim_keys = False
```

## Theme Files

Theme files define colors for the TUI and should be placed in:
- `~/.config/tuivllm/themes/` (user themes)
- `./themes/` (bundled themes)

### Theme Format

Themes use the same format as btop themes:

```theme
# Comment lines start with #

# Main background (empty for terminal default/transparent)
theme[main_bg]=""

# Main text color
theme[main_fg]=""

# User message box color
theme[user_color]="cyan"

# AI message box color
theme[ai_color]="yellow"

# System message color
theme[system_color]="bright_black"

# Border colors
theme[border_color]="cyan"

# Status bar colors
theme[status_connected]="green"
theme[status_processing]="yellow"
theme[status_error]="red"

# Scrollbar colors
theme[scrollbar_color]="cyan"
theme[scrollbar_hover]="bright_cyan"
theme[scrollbar_active]="bright_cyan"

# Input box border
theme[input_border]="cyan"

# Timestamp color
theme[timestamp_color]="bright_black"
```

## Built-in Themes

### system (default) ⭐
**Automatically uses your system's current theme!**

Reads colors from `~/.config/omarchy/current/btop.theme` (or btop's current theme). When you switch themes system-wide, TuivLLM automatically picks up the new colors. No duplication needed!

See [SYSTEM_THEME.md](SYSTEM_THEME.md) for details.

### terminal
Uses ANSI colors that adapt to your terminal's color scheme. Perfect for maintaining consistency with your terminal theme when you don't use omarchy/btop.

## Color Formats

Colors can be specified in multiple formats:

### ANSI Color Names
These adapt to your terminal's color scheme:
- `black`, `red`, `green`, `yellow`, `blue`, `magenta`, `cyan`, `white`
- `bright_black`, `bright_red`, `bright_green`, etc.

### Hex Colors
24-bit truecolor (requires `truecolor = True`):
- `#ff5555`
- `#50fa7b`
### RGB Colors
- `rgb(255,85,85)`

## How It Works

**Default Behavior (Recommended):**
- TuivLLM automatically reads from `~/.config/omarchy/current/btop.theme`
- When you change your Omarchy theme with `omarchy theme set <name>`, TuivLLM updates in real-time
- No configuration needed!

**Custom Themes (Optional):**

If you want a theme different from your system theme:

1. Create your theme file in `frontend/themes/my-custom-theme.theme`:
   ```theme
   # My Custom Theme
   theme[main_bg]="#1a1b26"
   theme[main_fg]="#c0caf5"
   theme[user_color]="#7aa2f7"
   theme[ai_color]="#bb9af7"
   # ... etc
   ```

2. Edit `frontend/tuivllm.conf.example` (or create `frontend/tuivllm.conf`):
   ```ini
   color_theme = "my-custom-theme"
   ```

3. Restart TuivLLM

## Creating Your Own Theme

Example custom theme:

```theme
# My Custom Theme
theme[main_bg]="#1a1b26"
theme[main_fg]="#c0caf5"
theme[user_color]="#7aa2f7"
theme[ai_color]="#bb9af7"
theme[system_color]="#565f89"
theme[border_color]="#7dcfff"
theme[status_connected]="#9ece6a"
theme[status_processing]="#e0af68"
theme[status_error]="#f7768e"
theme[scrollbar_color]="#7dcfff"
theme[scrollbar_hover]="#7aa2f7"
theme[scrollbar_active]="#bb9af7"
theme[input_border]="#7dcfff"
theme[timestamp_color]="#565f89"
```

## Switching Themes

To switch themes:

1. Edit `tuivllm.conf`
2. Change `color_theme = "themename"`
3. Restart TuivLLM

Or use the built-in command (if implemented):
```
/theme catppuccin
```

## Theme Locations

TuivLLM searches for themes in this order:
1. `~/.config/tuivllm/themes/` (user themes - highest priority)
2. `./themes/` (bundled themes)

## Tips

- Use `theme[main_bg]=""` for terminal transparency
- ANSI colors (`cyan`, `yellow`, etc.) adapt to your terminal theme
- Hex colors give you precise control but don't adapt to terminal themes
- Test your theme in different terminals to ensure compatibility

## Troubleshooting

**Theme not loading:**
- Check file is named `themename.theme`
- Verify it's in the correct directory
- Check for syntax errors in the theme file

**Colors look wrong:**
- If using hex colors, ensure `truecolor = True` in config
- Some terminals don't support 24-bit color
- Try using ANSI color names instead

**Transparency not working:**
- Set `theme[main_bg]=""`
- Set `theme_background = False` in config
- Ensure your terminal supports transparency

## Contributing Themes

If you create a theme you'd like to share:
1. Test it in multiple terminals
2. Add comments explaining the color scheme
3. Submit a pull request or issue with your theme file

## References

- [Rich Color Documentation](https://rich.readthedocs.io/en/stable/appendix/colors.html)
- [Textual Styling](https://textual.textualize.io/guide/styles/)
- [btop Themes](https://github.com/aristocratos/btop#themes)
