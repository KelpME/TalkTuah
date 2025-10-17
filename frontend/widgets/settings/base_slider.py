"""Base slider widget with configurable range and display"""

from textual.widgets import Static
from textual.message import Message
from utils.theme import get_theme_loader


class SliderValueChanged(Message):
    """Message when slider value changes"""
    
    def __init__(self, value: float):
        super().__init__()
        self.value = value


class BaseSlider(Static, can_focus=True):
    """Interactive slider widget with configurable parameters"""
    
    def __init__(
        self,
        initial_value: float,
        min_value: float,
        max_value: float,
        label: str,
        format_func=None,
        step: float = 0.1,
        inner_width: int = 66,
        width_offset: int = 20
    ):
        """Initialize slider.
        
        Args:
            initial_value: Starting value
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            label: Display label (e.g., "Temperature")
            format_func: Function to format value for display (default: str)
            step: Keyboard step size
            inner_width: Total width for layout
            width_offset: Offset for slider bar placement
        """
        super().__init__()
        self.value = initial_value
        self.min_value = min_value
        self.max_value = max_value
        self.label = label
        self.format_func = format_func or str
        self.step = step
        self.inner_width = inner_width
        self.width_offset = width_offset
        self.dragging = False
        self.can_focus = True
    
    def render(self) -> str:
        """Render the slider"""
        theme = get_theme_loader()
        ai_color = theme.get_color("ai_color", "cyan")
        user_color = theme.get_color("user_color", "cyan")
        
        # Calculate slider position
        slider_width = self.inner_width - self.width_offset
        value_range = self.max_value - self.min_value
        normalized_value = (self.value - self.min_value) / value_range
        position = int(normalized_value * slider_width)
        
        # Ensure position is within bounds
        position = max(0, min(slider_width, position))
        
        slider = "─" * position + "●" + "─" * (slider_width - position)
        value_display = f"{self.label}: [{user_color}]{self.format_func(self.value)}[/]"
        
        return f"[{ai_color}]│ {value_display} [{slider}] │[/]"
    
    def on_click(self, event) -> None:
        """Handle click to set value and focus"""
        self.focus()
        self._update_from_mouse(event.x)
    
    def on_mouse_down(self, event) -> None:
        """Start dragging"""
        self.dragging = True
        self._update_from_mouse(event.x)
    
    def on_mouse_up(self, event) -> None:
        """Stop dragging"""
        self.dragging = False
    
    def on_mouse_move(self, event) -> None:
        """Update value while dragging"""
        if self.dragging:
            self._update_from_mouse(event.x)
    
    def _update_from_mouse(self, mouse_x: int):
        """Update value based on mouse position"""
        label_offset = 20
        slider_width = self.inner_width - self.width_offset
        relative_x = mouse_x - label_offset
        
        if 0 <= relative_x <= slider_width:
            value_range = self.max_value - self.min_value
            normalized_value = relative_x / slider_width
            self.value = self.min_value + (normalized_value * value_range)
            self.value = max(self.min_value, min(self.max_value, self.value))
            self.refresh()
    
    def on_key(self, event) -> None:
        """Handle arrow keys to adjust value"""
        if event.key == "left":
            self.value = max(self.min_value, self.value - self.step)
            self.refresh()
            self.post_message(SliderValueChanged(self.value))
        elif event.key == "right":
            self.value = min(self.max_value, self.value + self.step)
            self.refresh()
            self.post_message(SliderValueChanged(self.value))
