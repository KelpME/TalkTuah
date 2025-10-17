"""Endpoint configuration widget"""

from textual.widgets import Static
from utils.theme import get_theme_loader


class EndpointLine(Static, can_focus=True):
    """Editable endpoint line with reset button"""
    
    def __init__(self, value: str, default_value: str, inner_width: int = 66):
        super().__init__()
        self.value = value
        self.default_value = default_value
        self.inner_width = inner_width
        self.can_focus = True
        self.editing = False
        self.cursor_pos = len(value)
    
    def render(self) -> str:
        theme = get_theme_loader()
        ai_color = theme.get_color("ai_color", "cyan")
        user_color = theme.get_color("user_color", "cyan")
        
        label = "Endpoint: "
        reset_btn = "[Reset]"
        display_value = self.value if not self.editing else self.value + "█"
        content = label + display_value
        content_len = len(label) + len(self.value) + 1 + len(reset_btn)
        padding = max(0, self.inner_width - content_len)
        
        if self.editing:
            return f"[{ai_color}]│ [{user_color}]{content}[/]{' ' * padding} [dim]{reset_btn}[/dim] │[/]"
        else:
            return f"[{ai_color}]│ {content}{' ' * padding} [{user_color}]{reset_btn}[/] │[/]"
    
    def on_click(self) -> None:
        self.editing = True
        self.focus()
        self.refresh()
    
    def on_key(self, event) -> None:
        if not self.editing:
            if event.key == "enter":
                self.editing = True
                self.refresh()
            elif event.key == "r":
                self.value = self.default_value
                self.refresh()
            return
        
        if event.key == "enter" or event.key == "escape":
            self.editing = False
            self.refresh()
        elif event.key == "backspace":
            if self.value:
                self.value = self.value[:-1]
            self.refresh()
        elif len(event.key) == 1:
            self.value += event.key
            self.refresh()
