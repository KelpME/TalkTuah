"""Theme and color utilities"""

from theme_loader import get_theme_loader


def interpolate_color(color1: str, color2: str, factor: float) -> str:
    """Interpolate between two hex colors.
    
    Args:
        color1: Start color (hex format)
        color2: End color (hex format)
        factor: Interpolation factor (0.0 to 1.0)
        
    Returns:
        Interpolated color in hex format
    """
    c1 = color1.lstrip('#')
    c2 = color2.lstrip('#')
    
    r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
    r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)
    
    r = int(r1 + (r2 - r1) * factor)
    g = int(g1 + (g2 - g1) * factor)
    b = int(b1 + (b2 - b1) * factor)
    
    return f"#{r:02x}{g:02x}{b:02x}"


def get_color_for_position(viewport_height: int, y_position: int) -> str:
    """Get gradient color for vertical position.
    
    Args:
        viewport_height: Total height of the viewport
        y_position: Current Y position
        
    Returns:
        Color in hex format for the gradient position
    """
    theme = get_theme_loader()
    gradient_top = theme.get_color("gradient_top", "#00ffff")
    gradient_mid = theme.get_color("gradient_mid", "#00ff00")
    gradient_bottom = theme.get_color("gradient_bottom", "#ffff00")
    
    if viewport_height <= 1:
        return gradient_top
    
    clamped_y = max(0, min(viewport_height - 1, y_position))
    gradient_factor = clamped_y / (viewport_height - 1)
    
    if gradient_factor < 0.5:
        return interpolate_color(gradient_top, gradient_mid, gradient_factor * 2)
    else:
        return interpolate_color(gradient_mid, gradient_bottom, (gradient_factor - 0.5) * 2)


def get_theme() -> object:
    """Convenience function to get theme loader.
    
    Returns:
        ThemeLoader instance
    """
    return get_theme_loader()
