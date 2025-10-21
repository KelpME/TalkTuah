"""Slider widgets for settings - consolidated from base_slider, temperature_slider, max_tokens_slider, gpu_memory_slider"""

from textual.widgets import Static
from textual.message import Message
from utils.theme import get_theme_loader


# ============================================================================
# Messages
# ============================================================================

class SliderValueChanged(Message):
    """Message when slider value changes"""
    
    def __init__(self, value: float):
        super().__init__()
        self.value = value


class TemperatureChanged(Message):
    """Message when temperature value changes"""
    
    def __init__(self, value: float):
        super().__init__()
        self.value = value


class MaxTokensChanged(Message):
    """Message when max tokens value changes"""
    
    def __init__(self, value: int):
        super().__init__()
        self.value = value


class GPUMemoryChanged(Message):
    """Message when GPU memory value changes"""
    
    def __init__(self, value: float):
        super().__init__()
        self.value = value


# ============================================================================
# Base Slider
# ============================================================================

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


# ============================================================================
# Specific Sliders
# ============================================================================

class TemperatureSlider(BaseSlider):
    """Interactive temperature slider widget (0.0 to 2.0)"""
    
    def __init__(self, initial_value: float = 0.7, inner_width: int = 66):
        super().__init__(
            initial_value=initial_value,
            min_value=0.0,
            max_value=2.0,
            label="Temperature",
            format_func=lambda v: f"{v:.1f}",
            step=0.1,
            inner_width=inner_width,
            width_offset=20
        )
    
    def on_key(self, event) -> None:
        """Handle arrow keys and post TemperatureChanged message"""
        if event.key in ("left", "right"):
            super().on_key(event)
            self.post_message(TemperatureChanged(self.value))


class MaxTokensSlider(BaseSlider):
    """Interactive max tokens slider widget"""
    
    def __init__(self, initial_value: int = 2048, max_value: int = 4096, inner_width: int = 66):
        # Store original values as integers
        self._initial_int = initial_value
        self._max_int = max_value
        
        super().__init__(
            initial_value=float(initial_value),
            min_value=128.0,  # Minimum reasonable token count
            max_value=float(max_value),
            label="Max Tokens",
            format_func=lambda v: f"{int(v)}",
            step=128.0,  # Increment by 128 tokens
            inner_width=inner_width,
            width_offset=23
        )
    
    def on_key(self, event) -> None:
        """Handle arrow keys and post MaxTokensChanged message"""
        if event.key in ("left", "right"):
            super().on_key(event)
            self.post_message(MaxTokensChanged(int(self.value)))


class GPUMemorySlider(BaseSlider):
    """Interactive GPU memory allocation slider widget (10% to 95%)"""
    
    def __init__(self, initial_value: float = 0.75, inner_width: int = 66):
        super().__init__(
            initial_value=initial_value,
            min_value=0.1,
            max_value=0.95,
            label="GPU Memory",
            format_func=lambda v: f"{int(v * 100)}%",
            step=0.05,
            inner_width=inner_width,
            width_offset=25
        )
    
    def on_key(self, event) -> None:
        """Handle arrow keys and post GPUMemoryChanged message"""
        if event.key in ("left", "right"):
            super().on_key(event)
            self.post_message(GPUMemoryChanged(self.value))
