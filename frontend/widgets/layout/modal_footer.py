"""Reusable modal footer with ESC button and optional info"""

from textual.widgets import Static
from textual.containers import Horizontal
from theme_loader import get_theme_loader


class ModalEscButton(Static):
    """Clickable ESC button for modal footers"""
    
    def __init__(self, callback=None):
        super().__init__()
        self.hovered = False
        self.callback = callback
    
    def render(self) -> str:
        theme = get_theme_loader()
        user_color = theme.get_color("user_color", "cyan")
        ai_color = theme.get_color("ai_color", "cyan")
        
        if self.hovered:
            return f"[{ai_color}]╰──┤ [[{user_color} bold]ESC[/]] ├"
        else:
            return f"[{ai_color}]╰──┤ [[{user_color}]ESC[/]] ├"
    
    def on_enter(self) -> None:
        self.hovered = True
        self.refresh()
    
    def on_leave(self) -> None:
        self.hovered = False
        self.refresh()
    
    def on_click(self) -> None:
        # Call custom callback if provided, otherwise close modal
        if self.callback:
            self.callback()
        else:
            # Default: save and dismiss
            if hasattr(self.screen, 'save_settings'):
                self.screen.save_settings()
            self.screen.dismiss(None)


class ModalFooter(Horizontal):
    """Reusable footer for modals with ESC button and optional right text"""
    
    def __init__(self, right_text: str = "", width: int = 70, callback=None):
        super().__init__()
        self.right_text = right_text
        self.width = width
        self.callback = callback
    
    def compose(self):
        yield ModalEscButton(callback=self.callback)
        
        # Calculate remaining dashes
        # "╰──┤ [ESC] ├" = 13 chars
        # "┤ {text} ├──╯" = len(text) + 7
        middle_dashes = self.width - 13 - len(self.right_text) - 7
        
        theme = get_theme_loader()
        ai_color = theme.get_color("ai_color", "cyan")
        
        if self.right_text:
            yield Static(f"[{ai_color}]{'─' * middle_dashes}┤ {self.right_text} ├──╯[/]")
        else:
            yield Static(f"[{ai_color}]{'─' * (middle_dashes + len(self.right_text) + 7 - 4)}╯[/]")
