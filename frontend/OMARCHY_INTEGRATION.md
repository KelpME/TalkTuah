# Omarchy Integration - Live Theme Reload

TuivLLM seamlessly integrates with Omarchy's theme system using **automatic file watching** - no manual scripts or modifications needed!

## How It Works

### The Elegant Solution

Instead of modifying Omarchy's `omarchy-theme-set` script, TuivLLM **piggybacks off btop's reload mechanism** by watching the same theme file:

```
User switches theme
    ↓
omarchy-theme-set gruvbox
    ↓
Updates ~/.config/omarchy/current/theme symlink
    ↓
pkill -SIGUSR2 btop  ← Omarchy reloads btop
    ↓
TuivLLM's file watcher detects btop.theme changed
    ↓
TuivLLM reloads colors automatically
    ↓
Shows notification: "Theme updated"
```

### Key Components

**1. File Watcher (`OmarchyThemeWatcher`)**
```python
class OmarchyThemeWatcher(FileSystemEventHandler):
    """Watches for Omarchy theme changes"""
    
    def on_modified(self, event):
        if Path(event.src_path).name == 'btop.theme':
            self.app.reload_theme_colors()
```

**2. Automatic Startup**
- TuivLLM checks if `~/.config/omarchy/current/theme/` exists
- If found, starts watching for changes
- If not found, gracefully falls back to terminal colors

**3. Live Reload**
- Detects when `btop.theme` is modified
- Reloads theme from `theme_loader`
- Refreshes all chat messages with new colors
- Shows user notification

## Benefits

✅ **Zero Omarchy modification** - No changes to `omarchy-theme-set`  
✅ **Automatic detection** - Watches the same file btop uses  
✅ **Live reload** - Updates in real-time, no restart  
✅ **Graceful fallback** - Works without Omarchy installed  
✅ **Clean integration** - Follows Omarchy's existing patterns  

## User Experience

### Before (Manual)
```bash
omarchy-theme-set dracula
# User has to restart TuivLLM to see new colors
make frontend
```

### After (Automatic)
```bash
omarchy-theme-set dracula
# TuivLLM instantly updates!
# Notification: "Theme updated"
# Keep chatting with new colors
```

### Hotkey Support
```bash
# User presses Super + Ctrl + Shift + Space
omarchy-theme-next
# TuivLLM updates immediately
# All terminal apps synchronized
```

## Technical Details

### Dependencies
- `watchdog==4.0.0` - File system event monitoring

### Watched Path
```
~/.config/omarchy/current/theme/btop.theme
```

### Events Monitored
- `on_modified` - File content changed
- `on_created` - Symlink recreated

### Thread Safety
- Uses `call_from_thread()` to safely update UI from watcher thread
- Observer properly cleaned up on app exit

### Performance
- Minimal overhead (only watches one directory)
- No polling - event-driven
- Instant detection (<100ms typically)

## Comparison with Other Approaches

### Approach 1: Modify omarchy-theme-set ❌
**Pros:** Direct integration  
**Cons:** Requires modifying Omarchy, maintenance burden

### Approach 2: Signal handling (SIGUSR2) ❌
**Pros:** Fast  
**Cons:** Process name conflicts, signal handling complexity

### Approach 3: File watching (Implemented) ✅
**Pros:** 
- No Omarchy modification
- Works even if TuivLLM starts after theme change
- Clean, maintainable
- Follows Unix philosophy

**Cons:**
- Requires watchdog dependency (acceptable trade-off)

## Installation

No special installation needed! Just:

```bash
# Install dependencies
make install-frontend

# Run TuivLLM
make frontend

# Switch Omarchy themes - TuivLLM updates automatically!
omarchy-theme-next
```

## Fallback Behavior

If Omarchy is not installed:
1. TuivLLM checks for `~/.config/omarchy/current/theme/`
2. If not found, skips file watcher setup
3. Falls back to `color_theme = "terminal"` (ANSI colors)
4. Still fully functional, just no live reload

## Future Enhancements

Potential improvements:
- [ ] Watch multiple theme sources (btop, kitty, alacritty)
- [ ] Debounce rapid theme changes
- [ ] Theme transition animations
- [ ] Custom reload callbacks

## Summary

TuivLLM achieves **seamless Omarchy integration** without modifying any Omarchy scripts. By watching the same `btop.theme` file that Omarchy updates, TuivLLM automatically detects theme changes and reloads in real-time.

**Result:** Zero-configuration, live-reloading theme synchronization across all terminal applications!
