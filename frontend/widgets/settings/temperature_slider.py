"""Temperature slider widget"""

from textual.widgets import Static
from textual.message import Message
from theme_loader import get_theme_loader
import re


def strip_markup(text: str) -> str:
    """Remove Rich markup tags from text"""
    return re.sub(r'\[.*?\]', '', text)


class TemperatureChanged(Message):
    """Message when temperature value changes"""
    
    def __init__(self, value: float):
        super().__init__()
        self.value = value


class TemperatureSlider(Static):
    """Interactive temperature slider widget"""
    
    def __init__(self, initial_value: float = 0.7, inner_width: int = 66):
        super().__init__()
        self.value = initial_value
        self.inner_width = inner_width
        self.dragging = False
    
    def render(self) -> str:
        theme = get_theme_loader()
        ai_color = theme.get_color("ai_color", "cyan")
        user_color = theme.get_color("user_color", "cyan")
        
        # Temperature slider (0.0 to 2.0)
        slider_width = self.inner_width - 20
        position = int((self.value / 2.0) * slider_width)
        
        slider = "─" * position + "●" + "─" * (slider_width - position)
        temp_display = f"Temperature: [{user_color}]{self.value:.1f}[/]"
        
        return f"[{ai_color}]│ {temp_display} [{slider}] │[/]"
    
    def on_click(self, event) -> None:
        """Handle click to set temperature"""
        # Calculate position relative to slider
        # Approximate: click position maps to temperature value
        self.dragging = True
        self.update_from_position(event.x)
    
    def on_mouse_move(self, event) -> None:
        """Handle drag to adjust temperature"""
        if self.dragging:
            self.update_from_position(event.x)
    
    def on_mouse_up(self, event) -> None:
        """Stop dragging"""
        self.dragging = False
    
    def update_from_position(self, x: int):
        """Update temperature based on mouse position"""
        # Rough calculation - adjust based on actual widget position
        slider_width = self.inner_width - 20
        # Assuming widget starts at position ~20
        relative_x = max(0, min(x - 20, slider_width))
        self.value = (relative_x / slider_width) * 2.0
        self.value = max(0.0, min(2.0, self.value))
        self.refresh()
        self.post_message(TemperatureChanged(self.value))
    
    def on_key(self, event) -> None:
        """Handle arrow keys to adjust temperature"""
        if event.key == "left":
            self.value = max(0.0, self.value - 0.1)
            self.refresh()
            self.post_message(TemperatureChanged(self.value))
        elif event.key == "right":
            self.value = min(2.0, self.value + 0.1)
            self.refresh()
            self.post_message(TemperatureChanged(self.value))
