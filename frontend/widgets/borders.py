from textual.widgets import Static
from theme_loader import get_theme_loader


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


class ContainerBorder(Static):
    def __init__(self, title: str = "", color_key: str = "ai_color", position: str = "top", border_type: str = "corner"):
        super().__init__()
        self.border_title = title
        self.color_key = color_key
        self.position = position
        self.border_type = border_type
    
    def render(self) -> str:
        theme = get_theme_loader()
        color = theme.get_color(self.color_key, "cyan")
        bg_color = theme.get_color("main_bg", "")
        
        width = self.size.width if self.size.width > 0 else 80
        
        # Only add background if theme specifies one
        if bg_color:
            bg_style = f" on {bg_color}"
        else:
            bg_style = ""
        
        if self.border_type == "corner":
            if self.position == "top" and self.border_title:
                title_text = f" {self.border_title} "
                left_pad = 2
                right_pad = max(0, width - len(title_text) - left_pad - 4)
                return f"[{color}{bg_style}]╭{'─' * left_pad}┤{title_text}├{'─' * right_pad}╮[/]"
            elif self.position == "bottom":
                return f"[{color}{bg_style}]╰{'─' * (width - 2)}╯[/]"
        else:
            if self.border_title:
                title_text = f" {self.border_title} "
                left_pad = 2
                right_pad = max(0, width - len(title_text) - left_pad - 4)
                return f"[{color}{bg_style}]├{'─' * left_pad}┤{title_text}├{'─' * right_pad}┤[/]"
            else:
                return f"[{color}{bg_style}]├{'─' * (width - 2)}┤[/]"


class SideBorder(Static):
    def __init__(self, color_key: str = "ai_color"):
        super().__init__()
        self.color_key = color_key
    
    def render(self) -> str:
        theme = get_theme_loader()
        color = theme.get_color(self.color_key, "cyan")
        bg_color = theme.get_color("main_bg", "")
        
        height = self.size.height if self.size.height > 0 else 1
        
        # Only add background if theme specifies one
        if bg_color:
            return "\n".join([f"[{color} on {bg_color}]│[/]"] * height)
        else:
            return "\n".join([f"[{color}]│[/]"] * height)
