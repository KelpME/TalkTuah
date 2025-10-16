"""Text markup utilities"""

import re


def strip_markup(text: str) -> str:
    """Remove Rich markup tags from text for length calculation.
    
    Args:
        text: Text with Rich markup tags
        
    Returns:
        Plain text without markup tags
        
    Example:
        >>> strip_markup("[cyan]Hello[/cyan]")
        'Hello'
    """
    return re.sub(r'\[.*?\]', '', text)
