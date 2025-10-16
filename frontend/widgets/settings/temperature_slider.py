"""Temperature slider widget"""

from textual.message import Message
from .base_slider import BaseSlider


class TemperatureChanged(Message):
    """Message when temperature value changes"""
    
    def __init__(self, value: float):
        super().__init__()
        self.value = value


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
