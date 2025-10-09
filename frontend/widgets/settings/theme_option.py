"""Theme option widget for theme selection"""

from textual.widgets import Static
from textual.message import Message
from theme_loader import get_theme_loader


class ThemeSelected(Message):
    """Message when a theme is selected"""
    
    def __init__(self, theme_name: str):
        super().__init__()
        self.theme_name = theme_name


class ThemeOption(Static):
    """A selectable theme option"""
    
    def __init__(self, theme_name: str, is_selected: bool = False, inner_width: int = 66):
        super().__init__()
        self.theme_name = theme_name
        self.is_selected = is_selected
        self.hovered = False
        self.inner_width = inner_width
    
    def render(self) -> str:
        theme = get_theme_loader()
        user_color = theme.get_color("user_color", "cyan")
        ai_color = theme.get_color("ai_color", "yellow")
        
        # Selection indicator
        indicator = "●" if self.is_selected else "○"
        
        # Calculate padding
        content = f"{indicator} {self.theme_name}"
        padding = max(0, self.inner_width - len(content))
        
        if self.hovered:
            return f"[{ai_color}]│ [{user_color}]{content}[/]{' ' * padding} │[/]"
        else:
            return f"[{ai_color}]│ [dim]{content}[/]{' ' * padding} │[/]"
    
    def on_enter(self) -> None:
        self.hovered = True
        self.refresh()
    
    def on_leave(self) -> None:
        self.hovered = False
        self.refresh()
    
    def on_click(self) -> None:
        # Notify parent screen
        self.post_message(ThemeSelected(self.theme_name))
