"""Model option widget for selecting active model"""

from textual.widgets import Static
from textual.message import Message
from utils.theme import get_theme_loader


class ModelSelected(Message):
    """Message when a model is selected"""
    
    def __init__(self, model_name: str):
        super().__init__()
        self.model_name = model_name


class ModelDeleteRequested(Message):
    """Message when a model deletion is requested"""
    
    def __init__(self, model_name: str):
        super().__init__()
        self.model_name = model_name


class ModelOption(Static, can_focus=True):
    """A selectable model option"""
    
    def __init__(self, model_name: str, is_selected: bool = False, inner_width: int = 66, is_downloading: bool = False):
        super().__init__()
        self.model_name = model_name
        self.is_selected = is_selected
        self.inner_width = inner_width
        self.is_downloading = is_downloading
        self.can_focus = True  # Enable keyboard focus
        # Double-click tracking
        self.click_count = 0
        self.last_click_time = 0
    
    def render(self) -> str:
        theme = get_theme_loader()
        user_color = theme.get_color("user_color", "cyan")
        ai_color = theme.get_color("ai_color", "yellow")
        
        # If downloading, show special indicator
        if self.is_downloading:
            indicator = "⏳"
            content = f"{indicator} {self.model_name} [dim](downloading...)[/dim]"
            padding = max(0, self.inner_width - len(f"{indicator} {self.model_name} (downloading...)"))
            return f"[{ai_color}]│ [dim]{content}[/]{' ' * padding} │[/]"
        
        # Selection indicator
        indicator = "●" if self.is_selected else "○"
        
        # Show appropriate hint based on state
        if self.click_count == 1:
            # First click - show confirmation hint
            content = f"{indicator} {self.model_name} [dim](click again to select)[/dim]"
            plain_content = f"{indicator} {self.model_name} (click again to select)"
        elif self.has_focus and not self.is_selected:
            # Focused via keyboard - show available actions
            content = f"{indicator} {self.model_name} [dim](Enter=select, Del=delete)[/dim]"
            plain_content = f"{indicator} {self.model_name} (Enter=select, Del=delete)"
        elif self.has_focus and self.is_selected:
            # Active model focused - only show Enter option
            content = f"{indicator} {self.model_name}"
            plain_content = f"{indicator} {self.model_name}"
        else:
            content = f"{indicator} {self.model_name}"
            plain_content = f"{indicator} {self.model_name}"
        
        # Calculate padding
        padding = max(0, self.inner_width - len(plain_content))
        
        # Highlight if focused
        if self.has_focus:
            return f"[{ai_color}]│ [{user_color}]{content}[/]{' ' * padding} │[/]"
        else:
            return f"[{ai_color}]│ [dim]{content}[/]{' ' * padding} │[/]"
    
    def on_enter(self) -> None:
        """Mouse hover - give focus seamlessly"""
        if not self.is_downloading:
            self.focus()
    
    def on_leave(self) -> None:
        """Mouse leave - no action needed, focus handles it"""
        pass
    
    def on_focus(self) -> None:
        """Refresh when focused (via hover or Tab)"""
        self.refresh()
    
    def on_blur(self) -> None:
        """Refresh when focus lost"""
        self.refresh()
    
    def on_click(self) -> None:
        # Don't allow clicking if model is downloading
        if not self.is_downloading:
            self.post_message(ModelSelected(self.model_name))
    
    def on_key(self, event) -> None:
        """Handle keyboard shortcuts"""
        if event.key == "delete" and not self.is_downloading and not self.is_selected:
            # Only allow deleting non-active models
            self.post_message(ModelDeleteRequested(self.model_name))
