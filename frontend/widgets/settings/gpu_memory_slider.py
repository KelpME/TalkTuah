"""GPU memory allocation slider widget"""

from textual.message import Message
from .base_slider import BaseSlider


class GPUMemoryChanged(Message):
    """Message when GPU memory value changes"""
    
    def __init__(self, value: float):
        super().__init__()
        self.value = value


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
