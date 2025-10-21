"""
Theme Loading and Management

Loads Omarchy theme configurations and provides gradient colors
for the TUI interface.

Moved from theme_loader.py during Phase 4 refactoring.
"""

import os
from pathlib import Path
from typing import Dict, Optional


class ThemeLoader:
    """Loads and manages themes and configuration"""
    
    def __init__(self):
        self.config: Dict[str, str] = {}
        self.theme: Dict[str, str] = {}
        
        # Default config values
        self.defaults = {
            "color_theme": "system",
            "theme_background": "True",
            "truecolor": "True",
            "rounded_corners": "True",
            "show_timestamps": "True",
            "timestamp_format": "%H:%M:%S",
            "max_history": "100",
            "auto_scroll": "True",
            "show_connection_status": "True",
            "vim_keys": "False",
        }
        
        # Default theme (terminal colors)
        self.default_theme = {
            "main_bg": "",
            "main_fg": "",
            "user_color": "cyan",
            "ai_color": "yellow",
            "system_color": "bright_black",
            "border_color": "cyan",
            "status_connected": "green",
            "status_processing": "yellow",
            "status_error": "red",
            "scrollbar_color": "cyan",
            "scrollbar_hover": "cyan",  # Changed from bright_cyan
            "scrollbar_active": "cyan",  # Changed from bright_cyan
            "input_border": "cyan",
            "timestamp_color": "bright_black",
        }
    
    def load_config(self, config_path: Optional[str] = None) -> Dict[str, str]:
        """Load configuration file"""
        if config_path is None:
            # Try multiple locations
            config_paths = [
                Path.home() / ".config" / "tuivllm" / "tuivllm.conf",
                Path(__file__).parent / "tuivllm.conf",
            ]
            
            for path in config_paths:
                if path.exists():
                    config_path = str(path)
                    break
        
        # Start with defaults
        self.config = self.defaults.copy()
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse key = value
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"')
                        self.config[key] = value
        
        return self.config
    
    def load_theme(self, theme_name: Optional[str] = None) -> Dict[str, str]:
        """Load theme file"""
        if theme_name is None:
            theme_name = self.config.get("color_theme", "terminal")
        
        # Start with default theme
        self.theme = self.default_theme.copy()
        
        # Special handling for "system" theme - read from omarchy current theme
        if theme_name == "system":
            self.theme = self._load_system_theme()
            return self.theme
        
        # Try multiple theme locations
        theme_paths = [
            Path.home() / ".config" / "tuivllm" / "themes" / f"{theme_name}.theme",
            Path(__file__).parent / "themes" / f"{theme_name}.theme",
        ]
        
        theme_path = None
        for path in theme_paths:
            if path.exists():
                theme_path = str(path)
                break
        
        if theme_path and os.path.exists(theme_path):
            with open(theme_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse theme[key]="value"
                    if line.startswith('theme[') and ']=' in line:
                        # Extract key and value
                        key_part = line.split(']')[0].replace('theme[', '')
                        value_part = line.split('=', 1)[1].strip().strip('"')
                        self.theme[key_part] = value_part
        
        return self.theme
    
    def _load_system_theme(self) -> Dict[str, str]:
        """Load theme from system's current theme (omarchy/btop style)"""
        # Try to find btop theme file
        btop_theme_paths = [
            Path.home() / ".config" / "omarchy" / "current" / "theme" / "btop.theme",  # Omarchy theme subdirectory
            Path.home() / ".config" / "omarchy" / "current" / "btop.theme",  # Legacy location
            Path.home() / ".config" / "btop" / "themes" / "current.theme",  # Standalone btop
        ]
        
        btop_theme = {}
        for path in btop_theme_paths:
            if path.exists():
                btop_theme = self._parse_btop_theme(str(path))
                break
        
        if not btop_theme:
            # Fallback to default if no system theme found
            return self.default_theme.copy()
        
        # Map btop theme colors to TuivLLM theme
        return self._map_btop_to_tuivllm(btop_theme)
    
    def _parse_btop_theme(self, theme_path: str) -> Dict[str, str]:
        """Parse btop theme file"""
        theme = {}
        with open(theme_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Parse theme[key]="value" or theme[key]=value
                if line.startswith('theme[') and ']=' in line:
                    key_part = line.split(']')[0].replace('theme[', '')
                    value_part = line.split('=', 1)[1].strip().strip('"')
                    theme[key_part] = value_part
        
        return theme
    
    def _map_btop_to_tuivllm(self, btop_theme: Dict[str, str]) -> Dict[str, str]:
        """Map btop theme colors to TuivLLM color scheme"""
        # Start with defaults
        tuivllm_theme = self.default_theme.copy()
        
        # Map btop colors to TuivLLM with better visual distinction
        color_mapping = {
            # Background and foreground
            "main_bg": btop_theme.get("main_bg", ""),
            "main_fg": btop_theme.get("main_fg", ""),
            
            # User messages - use highlight color for distinction (orange/blue typically)
            "user_color": btop_theme.get("hi_fg", btop_theme.get("cpu_mid", "cyan")),
            
            # AI messages - use title color or gradient end (different from user)
            "ai_color": btop_theme.get("title", btop_theme.get("cpu_end", "yellow")),
            
            # System messages - use inactive/comment color
            "system_color": btop_theme.get("inactive_fg", "bright_black"),
            
            # CONVERSATION border - SAME AS AI
            "border_color": btop_theme.get("title", btop_theme.get("cpu_end", "cyan")),
            
            # Status colors - use temperature gradient
            "status_connected": btop_theme.get("temp_start", btop_theme.get("free_start", "green")),
            "status_processing": btop_theme.get("temp_mid", "yellow"),
            "status_error": btop_theme.get("temp_end", "red"),
            
            # Scrollbar - use same as USER color (matches YOU container)
            "scrollbar_color": btop_theme.get("hi_fg", btop_theme.get("cpu_mid", "cyan")),
            "scrollbar_hover": btop_theme.get("hi_fg", btop_theme.get("cpu_mid", "cyan")),
            "scrollbar_active": btop_theme.get("hi_fg", btop_theme.get("cpu_mid", "cyan")),
            
            # INPUT border - SAME AS AI (all three match!)
            "input_border": btop_theme.get("title", btop_theme.get("cpu_end", "cyan")),
            
            # Timestamp - use inactive color (subtle)
            "timestamp_color": btop_theme.get("inactive_fg", "bright_black"),
            
            # Gradient colors for message fade effect (uses CPU/available gradient)
            # Top = Red, Middle = Orange/Yellow, Bottom = Gray/Green
            "gradient_top": btop_theme.get("cpu_end", btop_theme.get("available_end", "#f85552")),
            "gradient_mid": btop_theme.get("cpu_mid", btop_theme.get("available_mid", "#f59e0b")),
            "gradient_bottom": btop_theme.get("cpu_start", btop_theme.get("available_start", "#8a8a8d")),
        }
        
        # Update with mapped colors
        tuivllm_theme.update(color_mapping)
        
        return tuivllm_theme
    
    def get_config(self, key: str, default: Optional[str] = None) -> str:
        """Get configuration value"""
        return self.config.get(key, default or self.defaults.get(key, ""))
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean configuration value"""
        value = self.get_config(key, str(default))
        return value.lower() in ('true', '1', 'yes', 'on')
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get integer configuration value"""
        try:
            return int(self.get_config(key, str(default)))
        except ValueError:
            return default
    
    def get_color(self, key: str, default: str = "white") -> str:
        """Get color from theme"""
        return self.theme.get(key, default)


# Simplified global instance - no need for complex getter/setter
_theme_loader = ThemeLoader()
_theme_loader.load_config()
_theme_loader.load_theme()


def get_theme_loader() -> ThemeLoader:
    """Get the global theme loader instance"""
    return _theme_loader


def reload_theme():
    """Reload theme (called by file watcher)"""
    _theme_loader.load_theme()


# Color utility functions (moved from theme_helpers.py)

def interpolate_color(color1: str, color2: str, factor: float) -> str:
    """Interpolate between two hex colors.
    
    Args:
        color1: Start color (hex format)
        color2: End color (hex format)
        factor: Interpolation factor (0.0 to 1.0)
        
    Returns:
        Interpolated color in hex format
    """
    c1 = color1.lstrip('#')
    c2 = color2.lstrip('#')
    
    r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
    r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)
    
    r = int(r1 + (r2 - r1) * factor)
    g = int(g1 + (g2 - g1) * factor)
    b = int(b1 + (b2 - b1) * factor)
    
    return f"#{r:02x}{g:02x}{b:02x}"


def get_color_for_position(viewport_height: int, y_position: int) -> str:
    """Get gradient color for vertical position.
    
    Args:
        viewport_height: Total height of the viewport
        y_position: Current Y position
        
    Returns:
        Color in hex format for the gradient position
    """
    theme = get_theme_loader()
    gradient_top = theme.get_color("gradient_top", "#00ffff")
    gradient_mid = theme.get_color("gradient_mid", "#00ff00")
    gradient_bottom = theme.get_color("gradient_bottom", "#ffff00")
    
    if viewport_height <= 1:
        return gradient_top
    
    clamped_y = max(0, min(viewport_height - 1, y_position))
    gradient_factor = clamped_y / (viewport_height - 1)
    
    if gradient_factor < 0.5:
        return interpolate_color(gradient_top, gradient_mid, gradient_factor * 2)
    else:
        return interpolate_color(gradient_mid, gradient_bottom, (gradient_factor - 0.5) * 2)
