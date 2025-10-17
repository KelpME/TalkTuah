from textual.widgets import Static
from textual.containers import Horizontal
from utils.theme import get_theme_loader
from utils.theme_helpers import get_color_for_position


class KeybindingButton(Static):
    def __init__(self, key: str, action: str, action_name: str):
        super().__init__()
        self.key = key
        self.action_text = action
        self.action_name = action_name
        self.hovered = False
    
    def render(self) -> str:
        theme = get_theme_loader()
        ai_color = theme.get_color("ai_color", "cyan")
        user_color = theme.get_color("user_color", "cyan")
        main_bg = theme.get_color("main_bg", "")
        
        bg_style = f" on {main_bg}" if main_bg else ""
        
        if self.hovered:
            return f"[{user_color}{bg_style}]├ [bold]{self.key}[/bold] [dim]│[/dim] [bold]{self.action_text}[/bold] ┤[/]"
        else:
            return f"[dim {ai_color}{bg_style}]├ {self.key} │ {self.action_text} ┤[/]"
    
    def on_enter(self) -> None:
        self.hovered = True
        self.refresh()
    
    def on_leave(self) -> None:
        self.hovered = False
        self.refresh()
    
    def on_click(self) -> None:
        # Call the action method directly
        action_method = getattr(self.app, f"action_{self.action_name}", None)
        if action_method:
            action_method()


class FooterBorder(Static):
    def render(self) -> str:
        theme = get_theme_loader()
        ai_color = theme.get_color("ai_color", "cyan")
        bg_color = theme.get_color("main_bg", "")
        
        width = self.size.width if self.size.width > 0 else 80
        buttons_space = 62
        left_pad = 1
        right_pad = max(0, width - buttons_space - left_pad - 2)
        
        # Only add background if theme specifies one
        if bg_color:
            return f"[{ai_color} on {bg_color}]╰{'─' * left_pad}[/]"
        else:
            return f"[{ai_color}]╰{'─' * left_pad}[/]"


class FooterSpacer(Static):
    """Spacer between footer buttons with themed background"""
    
    def render(self) -> str:
        theme = get_theme_loader()
        main_bg = theme.get_color("main_bg", "")
        
        # Only add background if theme specifies one
        if main_bg:
            return f"[on {main_bg}] [/]"
        else:
            return " "


class CustomFooter(Horizontal):
    """Custom footer with clickable keybindings"""
    
    def compose(self):
        yield FooterBorder()
        yield KeybindingButton("CTRL+C", "Quit", "quit")
        yield FooterSpacer()
        yield KeybindingButton("CTRL+L", "Clear", "clear_chat")
        yield FooterSpacer()
        yield KeybindingButton("CTRL+S", "Settings", "settings")
        yield FooterSpacer()
        yield KeybindingButton("CTRL+R", "Reconnect", "reconnect")
        yield FooterEnd()


class FooterEnd(Static):
    def render(self) -> str:
        theme = get_theme_loader()
        ai_color = theme.get_color("ai_color", "cyan")
        bg_color = theme.get_color("main_bg", "")
        
        width = self.size.width if self.size.width > 0 else 10
        
        # Only add background if theme specifies one
        if bg_color:
            return f"[{ai_color} on {bg_color}]{'─' * (width - 1)}╯[/]"
        else:
            return f"[{ai_color}]{'─' * (width - 1)}╯[/]"
