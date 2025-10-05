# System Theme Integration

TuivLLM automatically reads colors from your system's current theme, just like btop does.

## How It Works

When you set `color_theme = "system"` (the default), TuivLLM:

1. **Reads your current theme** from `~/.config/omarchy/current/theme/btop.theme`
2. **Maps btop colors** to TuivLLM UI elements
3. **Watches for theme changes** using a file watcher
4. **Reloads automatically** when you switch Omarchy themes - no restart needed!

## Benefits

✅ **No theme duplication** - One theme for all your terminal apps  
✅ **Automatic synchronization** - Change theme once, affects everything  
✅ **Consistent look** - TuivLLM matches btop, terminals, etc.  
✅ **Zero configuration** - Works out of the box  

## Color Mapping

TuivLLM intelligently maps btop theme colors:

| TuivLLM Element | btop Color | Fallback |
|-----------------|------------|----------|
| User messages | `cpu_box` | `cyan` |
| AI messages | `mem_box` | `yellow` |
| System messages | `inactive_fg` | `bright_black` |
| Borders | `div_line` | `cyan` |
| Connected status | `temp_start` | `green` |
| Processing status | `temp_mid` | `yellow` |
| Error status | `temp_end` | `red` |
| Scrollbar | `process_start` | `cyan` |
| Scrollbar hover | `process_mid` | `bright_cyan` |
| Scrollbar active | `process_end` | `bright_cyan` |
| Input border | `hi_fg` | `cyan` |
| Timestamps | `graph_text` | `bright_black` |

## Configuration

### Use System Theme (Default)

```conf
# tuivllm.conf
color_theme = "system"
```

This reads from `~/.config/omarchy/current/btop.theme`

### Use Terminal Colors

```conf
# tuivllm.conf
color_theme = "terminal"
```

This uses ANSI colors that adapt to your terminal's color scheme.

### Use Custom Theme

```conf
# tuivllm.conf
color_theme = "mytheme"
```

Create `~/.config/tuivllm/themes/mytheme.theme` with your custom colors.

## Theme Locations

TuivLLM searches for btop themes in:

1. `~/.config/omarchy/current/btop.theme` (omarchy current theme)
2. `~/.config/btop/themes/current.theme` (btop current theme)

If no system theme is found, it falls back to terminal ANSI colors.

## Example: Switching System Themes

When you switch themes in Omarchy:

```bash
# Switch to dracula theme system-wide
omarchy-theme-set dracula

# TuivLLM automatically detects the change and reloads!
# No restart needed - colors update in real-time
```

Or cycle themes with your hotkey (e.g., Super + Ctrl + Shift + Space):
```bash
omarchy-theme-next
# TuivLLM instantly updates to match!
```

No need to configure or restart TuivLLM separately!

## Workflow

1. **Install Omarchy** or configure btop themes
2. **Run TuivLLM** once - it starts watching for theme changes
3. **Switch themes** anytime using `omarchy-theme-set` or `omarchy-theme-next`
4. **TuivLLM updates instantly** - no restart needed!
5. **Enjoy consistency** across all terminal apps

## Live Theme Reload

TuivLLM uses a file watcher to detect when Omarchy changes themes:

- **Automatic detection**: Watches `~/.config/omarchy/current/theme/btop.theme`
- **Instant reload**: Colors update in real-time when you switch themes
- **No restart needed**: Keep chatting while themes change
- **Visual feedback**: Shows a notification when theme updates

This means you can:
- Cycle through themes with your hotkey
- See TuivLLM colors update immediately
- Test different themes without interrupting your workflow

## Fallback Behavior

If TuivLLM can't find a system theme:

1. Tries `~/.config/omarchy/current/btop.theme`
2. Tries `~/.config/btop/themes/current.theme`
3. Falls back to terminal ANSI colors
4. Uses hardcoded defaults as last resort

## Custom Theme Override

You can still create custom themes if you want TuivLLM to look different from your system theme:

```bash
# Create custom theme
mkdir -p ~/.config/tuivllm/themes
cat > ~/.config/tuivllm/themes/custom.theme << 'EOF'
theme[user_color]="#00ff00"
theme[ai_color]="#ff00ff"
theme[border_color]="#00ffff"
EOF

# Use custom theme
echo 'color_theme = "custom"' > frontend/tuivllm.conf
```

## Troubleshooting

**Colors not updating?**
- Check if `~/.config/omarchy/current/btop.theme` exists
- Verify the file has valid btop theme syntax
- Try `color_theme = "terminal"` as fallback

**Want to see what colors are loaded?**
```bash
cd frontend
python3 -c "from theme_loader import get_theme_loader; t = get_theme_loader(); print(t.theme)"
```

**Theme file not found?**
- TuivLLM will use terminal ANSI colors
- This is normal if you don't use omarchy/btop
- Set `color_theme = "terminal"` explicitly

## Benefits of System Theme Integration

### Before (Duplicated Themes)
```
~/.config/btop/themes/dracula.theme
~/.config/tuivllm/themes/dracula.theme  ❌ Duplicate!
~/.config/alacritty/dracula.yml         ❌ Duplicate!
```

### After (Single Source of Truth)
```
~/.config/omarchy/current/btop.theme    ✅ One theme
# TuivLLM reads from this automatically
# btop reads from this
# Other apps can read from this too
```

## Advanced: Custom Color Mapping

If you want different color mappings, create a custom theme:

```theme
# ~/.config/tuivllm/themes/custom.theme
# Override specific colors while keeping others from system theme

theme[user_color]="bright_blue"
theme[ai_color]="bright_magenta"
# Other colors will use system theme defaults
```

Then:
```conf
color_theme = "custom"
```

## See Also

- [THEMES.md](THEMES.md) - Complete theme documentation
- [QUICKSTART_THEMES.md](QUICKSTART_THEMES.md) - Quick start guide
- [btop themes](https://github.com/aristocratos/btop#themes)
- [omarchy](https://github.com/omarchy) - Theme manager
