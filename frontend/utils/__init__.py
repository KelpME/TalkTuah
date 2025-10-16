"""Utility functions for TalkTuah frontend"""

from .theme_helpers import (
    interpolate_color,
    get_color_for_position,
    get_theme
)
from .markup import strip_markup

__all__ = [
    "interpolate_color",
    "get_color_for_position",
    "get_theme",
    "strip_markup",
]
