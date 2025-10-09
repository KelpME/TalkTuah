from textual.widgets import Static
from textual.containers import Horizontal
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
