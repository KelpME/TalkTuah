# TuivLLM Themes - Quick Start

## 🎨 Try Different Themes

### 1. Use System Theme (Default) ⭐
**No configuration needed!** Just run:
```bash
make frontend
```

TuivLLM automatically reads colors from your system's current theme (`~/.config/omarchy/current/btop.theme`). When you switch themes system-wide, TuivLLM updates automatically!

### 2. Use Terminal Colors
```bash
cd frontend
echo 'color_theme = "terminal"' > tuivllm.conf
cd ..
make frontend
```
Uses ANSI colors that adapt to your terminal's color scheme.

### 3. Create Custom Theme
```bash
mkdir -p ~/.config/tuivllm/themes
cat > ~/.config/tuivllm/themes/mytheme.theme << 'EOF'
theme[user_color]="cyan"
theme[ai_color]="yellow"
theme[border_color]="blue"
EOF

cd frontend
echo 'color_theme = "mytheme"' > tuivllm.conf
cd ..
make frontend
```

## 🛠️ Create Your Own Theme

### Step 1: Copy a Template
```bash
mkdir -p ~/.config/tuivllm/themes
cp frontend/themes/terminal.theme ~/.config/tuivllm/themes/mytheme.theme
```

### Step 2: Edit Colors
```bash
nano ~/.config/tuivllm/themes/mytheme.theme
```

Change any colors you want:
```theme
theme[user_color]="#00ff00"      # Bright green for user
theme[ai_color]="#ff00ff"        # Magenta for AI
theme[border_color]="#00ffff"    # Cyan borders
```

### Step 3: Activate Your Theme
```bash
echo 'color_theme = "mytheme"' > frontend/tuivllm.conf
make frontend
```

## 🎯 Quick Color Reference

### ANSI Colors (Adapt to Terminal)
```
black, red, green, yellow, blue, magenta, cyan, white
bright_black, bright_red, bright_green, bright_yellow,
bright_blue, bright_magenta, bright_cyan, bright_white
```

### Hex Colors (Precise)
```
#ff5555  (red)
#50fa7b  (green)
#8be9fd  (cyan)
#bd93f9  (purple)
```

### RGB Colors
```
rgb(255,85,85)
rgb(80,250,123)
```

## 📋 Theme File Structure

Minimal theme file:
```theme
# My Theme
theme[user_color]="cyan"
theme[ai_color]="yellow"
theme[border_color]="blue"
theme[status_connected]="green"
theme[status_processing]="yellow"
theme[status_error]="red"
```

## 🔧 Configuration Options

Create `frontend/tuivllm.conf`:
```conf
# Theme to use
color_theme = "terminal"

# Show timestamps
show_timestamps = True

# Timestamp format
timestamp_format = "%H:%M:%S"

# Rounded corners
rounded_corners = True

# Max messages in history
max_history = 100
```

## 💡 Tips

1. **Terminal transparency**: Use empty string for background
   ```theme
   theme[main_bg]=""
   ```

2. **Match your terminal**: Use ANSI color names
   ```theme
   theme[user_color]="cyan"
   ```

3. **Precise colors**: Use hex values
   ```theme
   theme[user_color]="#00ffff"
   ```

4. **Test quickly**: Just edit `tuivllm.conf` and restart

## 🐛 Troubleshooting

**Theme not loading?**
- Check filename: `mytheme.theme` (not `.txt`)
- Check location: `~/.config/tuivllm/themes/` or `frontend/themes/`
- Check syntax: `theme[key]="value"`

**Colors look wrong?**
- For hex colors, set `truecolor = True` in config
- Some terminals don't support 24-bit color
- Try ANSI color names instead

**Want transparency?**
```conf
theme_background = False
```
And in theme:
```theme
theme[main_bg]=""
```

## 📚 More Info

- Full documentation: [THEMES.md](THEMES.md)
- Implementation details: [THEME_SYSTEM.md](THEME_SYSTEM.md)
- Frontend README: [README.md](README.md)

## 🎨 Theme Gallery

### Terminal (Default)
- Adapts to your terminal's color scheme
- Perfect for consistency
- Works everywhere

### Catppuccin
- Soothing pastel colors
- Light theme (Latte variant)
- Easy on the eyes

### Dracula
- Dark theme with vibrant accents
- Popular color scheme
- Great contrast

### Gruvbox
- Retro warm colors
- Dark theme
- Comfortable for long sessions

## 🚀 Next Steps

1. Try all built-in themes
2. Pick your favorite
3. Customize it to your taste
4. Share your theme with others!

Happy theming! 🎨
