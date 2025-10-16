"""Max tokens slider widget"""

from textual.message import Message
from .base_slider import BaseSlider


class MaxTokensChanged(Message):
    """Message when max tokens value changes"""
    
    def __init__(self, value: int):
        super().__init__()
        self.value = value


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
