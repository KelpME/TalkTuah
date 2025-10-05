# TuivLLM Changelog

## [Unreleased] - 2025-10-04

### Added - Omarchy Integration 🎨

**Major Feature: Live Theme Reload with Omarchy Integration**

- **Automatic File Watching**
  - Watches `~/.config/omarchy/current/theme/btop.theme` for changes
  - Detects theme switches in real-time
  - Reloads colors automatically without restart
  - Shows notification when theme updates

- **Zero Configuration**
  - No Omarchy script modifications needed
  - Piggybacks off btop's reload mechanism
  - Graceful fallback if Omarchy not installed
  - Works out of the box

**Major Feature: btop-style Configuration and Theme System**

- **Configuration System**
  - Added `tuivllm.conf` for btop-style configuration
  - Added `tuivllm.conf.example` with detailed comments
  - Configuration search in multiple locations (`~/.config/tuivllm/` and `./`)
  - Support for boolean, integer, and string config values
  - 10+ configuration options (theme, timestamps, history, etc.)

- **Theme System**
  - Added `theme_loader.py` module for loading themes
  - Theme files use btop-style `theme[key]="value"` syntax
  - Support for ANSI colors (adapt to terminal)
  - Support for hex colors (#RRGGBB)
  - Support for RGB colors (rgb(r,g,b))
  - Theme search in multiple locations

- **Built-in Themes**
  - `terminal` - Default theme using ANSI colors
  - `catppuccin` - Catppuccin Latte color scheme
  - `dracula` - Dracula theme
  - `gruvbox` - Gruvbox Dark theme

- **Theme Colors**
  - User message box color
  - AI message box color
  - System message color
  - Border colors
  - Status bar colors (connected, processing, error)
  - Scrollbar colors
  - Input box border
  - Timestamp color

- **Documentation**
  - Added `THEMES.md` - Complete theme system guide
  - Added `THEME_SYSTEM.md` - Implementation details
  - Added `QUICKSTART_THEMES.md` - Quick start guide
  - Updated `README.md` with theme information

- **Integration**
  - Updated `TuivLLM.py` to use theme loader
  - Dynamic color loading in `ChatMessage.render()`
  - Backward compatible with existing installations

### Changed

- Updated `.gitignore` to exclude user configs but include built-in themes
- Updated frontend README with theme section
- Updated main project README with theme information

### Technical Details

**Files Added:**
- `tuivllm.conf.example` - Example configuration
- `theme_loader.py` - Theme loading module with Omarchy integration
- `themes/terminal.theme` - Fallback theme
- `THEMES.md` - Theme documentation
- `THEME_SYSTEM.md` - Implementation guide
- `SYSTEM_THEME.md` - Omarchy integration guide
- `SYSTEM_INTEGRATION.md` - Implementation summary
- `OMARCHY_INTEGRATION.md` - Live reload documentation
- `QUICKSTART_THEMES.md` - Quick start guide
- `CHANGELOG.md` - This file

**Files Modified:**
- `TuivLLM.py` - Added file watcher and live theme reload
- `theme_loader.py` - Added system theme loading from Omarchy
- `requirements.txt` - Added watchdog dependency
- `README.md` - Added Omarchy integration info
- `../.gitignore` - Added theme-related entries

**Files Removed:**
- `themes/catppuccin.theme` - No longer needed (use system theme)
- `themes/dracula.theme` - No longer needed (use system theme)
- `themes/gruvbox.theme` - No longer needed (use system theme)

**Configuration Options:**
- `color_theme` - Theme name to load
- `theme_background` - Show theme background
- `truecolor` - Use 24-bit colors
- `rounded_corners` - Rounded message boxes
- `show_timestamps` - Show message timestamps
- `timestamp_format` - Timestamp format string
- `max_history` - Maximum messages in history
- `auto_scroll` - Auto-scroll to bottom
- `show_connection_status` - Show status bar
- `vim_keys` - Vim keybindings (planned)

**Theme Properties:**
- `main_bg` - Background color
- `main_fg` - Text color
- `user_color` - User message box
- `ai_color` - AI message box
- `system_color` - System messages
- `border_color` - Container borders
- `status_connected` - Connected status
- `status_processing` - Processing status
- `status_error` - Error status
- `scrollbar_color` - Scrollbar
- `scrollbar_hover` - Scrollbar hover
- `scrollbar_active` - Scrollbar active
- `input_border` - Input box border
- `timestamp_color` - Timestamp text

### Future Enhancements

Planned features:
- [ ] Runtime theme switching (no restart)
- [ ] Theme preview command
- [ ] More built-in themes (Nord, Tokyo Night, etc.)
- [ ] Theme validation tool
- [ ] CSS variable integration
- [ ] Gradient support
- [ ] Animation settings
- [ ] Font settings
- [ ] Vim keybindings implementation

---

## [Previous] - Before 2025-10-04

### Initial Release

- Terminal UI chat interface
- vLLM API integration
- Authentication support
- Conversation history
- Keyboard shortcuts
- BTOP++ inspired design
- Real-time streaming
