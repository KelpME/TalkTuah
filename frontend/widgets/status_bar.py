from textual.widgets import Static
from textual.reactive import reactive
from theme_loader import get_theme_loader
import re


def interpolate_color(color1: str, color2: str, factor: float) -> str:
    c1 = color1.lstrip('#')
    c2 = color2.lstrip('#')
    
    if len(c1) != 6 or len(c2) != 6:
        return color1
    
    r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
    r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)
    
    r = int(r1 + (r2 - r1) * factor)
    g = int(g1 + (g2 - g1) * factor)
    b = int(b1 + (b2 - b1) * factor)
    
    return f"#{r:02x}{g:02x}{b:02x}"


def get_gradient_color_at_y(y_position: int, viewport_height: int) -> str:
    theme = get_theme_loader()
    
    gradient_top = theme.get_color("gradient_top", "#f85552")
    gradient_mid = theme.get_color("gradient_mid", "#7fbbb3")
    gradient_bottom = theme.get_color("gradient_bottom", "#a7c080")
    
    if viewport_height <= 1:
        gradient_factor = 0.5
    else:
        clamped_y = max(0, min(y_position, viewport_height - 1))
        gradient_factor = clamped_y / (viewport_height - 1)
    
    if gradient_factor < 0.5:
        return interpolate_color(gradient_top, gradient_mid, gradient_factor * 2)
    else:
        return interpolate_color(gradient_mid, gradient_bottom, (gradient_factor - 0.5) * 2)


class StatusBar(Static):
    status_text: reactive[str] = reactive("Initializing...")
    model_text: reactive[str] = reactive("")
    
    def render(self) -> str:
        theme = get_theme_loader()
        user_color = theme.get_color("user_color", "cyan")
        bg_color = theme.get_color("main_bg", "")
        
        visible_status = re.sub(r'\[.*?\]', '', self.status_text)
        visible_model = re.sub(r'\[.*?\]', '', self.model_text)
        
        width = self.size.width if self.size.width > 0 else 80
        
        # Calculate padding to push model to the right
        # Format: │ status ... model │
        status_len = len(visible_status) + 2  # +2 for "│ "
        model_len = len(visible_model) + 2    # +2 for " │"
        padding = max(1, width - status_len - model_len)
        
        # Only add background if theme specifies one
        if bg_color:
            return f"[{user_color} on {bg_color}]│ {self.status_text}{' ' * padding}{self.model_text} │[/]"
        else:
            return f"[{user_color}]│ {self.status_text}{' ' * padding}{self.model_text} │[/]"
