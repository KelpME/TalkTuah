"""Utility functions for settings widgets"""

import re


def strip_markup(text: str) -> str:
    """Remove Rich markup tags from text for length calculation"""
    return re.sub(r'\[.*?\]', '', text)
