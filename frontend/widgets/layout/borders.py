from textual.widgets import Static
from utils.theme import get_theme_loader
from utils.theme_helpers import get_color_for_position


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
