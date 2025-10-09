from textual.widgets import Static
from textual.reactive import reactive
from theme_loader import get_theme_loader
import re


def interpolate_color(color1: str, color2: str, factor: float) -> str:
    c1 = color1.lstrip('#')
    c2 = color2.lstrip('#')
    
    if len(c1) != 6 or len(c2) != 6:
        return color1
    
    r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
    r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)
    
    r = int(r1 + (r2 - r1) * factor)
    g = int(g1 + (g2 - g1) * factor)
    b = int(b1 + (b2 - b1) * factor)
    
    return f"#{r:02x}{g:02x}{b:02x}"


def get_gradient_color_at_y(y_position: int, viewport_height: int) -> str:
    theme = get_theme_loader()
    
    gradient_top = theme.get_color("gradient_top", "#f85552")
    gradient_mid = theme.get_color("gradient_mid", "#7fbbb3")
    gradient_bottom = theme.get_color("gradient_bottom", "#a7c080")
    
    if viewport_height <= 1:
        gradient_factor = 0.5
    else:
        clamped_y = max(0, min(y_position, viewport_height - 1))
        gradient_factor = clamped_y / (viewport_height - 1)
    
    if gradient_factor < 0.5:
        return interpolate_color(gradient_top, gradient_mid, gradient_factor * 2)
    else:
        return interpolate_color(gradient_mid, gradient_bottom, (gradient_factor - 0.5) * 2)


class StatusBar(Static):
    status_text: reactive[str] = reactive("Initializing...")
    model_text: reactive[str] = reactive("")
    
    def render(self) -> str:
        theme = get_theme_loader()
        user_color = theme.get_color("user_color", "cyan")
        bg_color = theme.get_color("main_bg", "")
        
        # Split status_text by newline if present (for connection + endpoint)
        status_lines = self.status_text.split('\n')
        status_line1 = status_lines[0] if len(status_lines) > 0 else ""
        status_line2 = status_lines[1] if len(status_lines) > 1 else ""
        
        visible_status1 = re.sub(r'\[.*?\]', '', status_line1)
        visible_status2 = re.sub(r'\[.*?\]', '', status_line2)
        visible_model = re.sub(r'\[.*?\]', '', self.model_text)
        
        width = self.size.width if self.size.width > 0 else 80
        
        # Split model_text into components if it exists
        if self.model_text:
            # Split by the pattern " [dim]│[/dim] " to properly separate sections
            # This preserves the markup in each section
            separator_pattern = r'\s*\[dim\]│\[/dim\]\s*'
            model_parts_markup = re.split(separator_pattern, self.model_text)
            
            # Also split visible text for length calculations
            parts = [p.strip() for p in visible_model.split('│')]
            model_name = parts[0] if len(parts) > 0 else ""
            ram_info = parts[1] if len(parts) > 1 else ""
            vram_info = parts[2] if len(parts) > 2 else ""
            
            # Get markup versions
            model_name_markup = model_parts_markup[0].strip() if len(model_parts_markup) > 0 else ""
            ram_info_markup = model_parts_markup[1].strip() if len(model_parts_markup) > 1 else ""
            vram_info_markup = model_parts_markup[2].strip() if len(model_parts_markup) > 2 else ""
            
            # Build three lines: status line 1 + model, status line 2, RAM/VRAM on right
            status1_len = len(visible_status1) + 2  # +2 for "│ "
            status2_len = len(visible_status2) + 2 if visible_status2 else 2
            padding1 = max(1, width - status1_len - len(model_name) - 2)
            padding2 = max(1, width - status2_len - len(ram_info) - 2)
            
            if bg_color:
                line1 = f"[{user_color} on {bg_color}]│ {status_line1}{' ' * padding1}{model_name_markup} │[/]"
                line2 = f"[{user_color} on {bg_color}]│ {status_line2}{' ' * padding2}{ram_info_markup} │[/]"
                if vram_info:
                    padding3 = max(1, width - 2 - len(vram_info) - 2)
                    line3 = f"[{user_color} on {bg_color}]│ {' ' * padding3}{vram_info_markup} │[/]"
                    return f"{line1}\n{line2}\n{line3}"
                else:
                    # No VRAM, add empty line
                    line3 = f"[{user_color} on {bg_color}]│ {' ' * (width - 4)} │[/]"
                    return f"{line1}\n{line2}\n{line3}"
            else:
                line1 = f"[{user_color}]│ {status_line1}{' ' * padding1}{model_name_markup} │[/]"
                line2 = f"[{user_color}]│ {status_line2}{' ' * padding2}{ram_info_markup} │[/]"
                if vram_info:
                    padding3 = max(1, width - 2 - len(vram_info) - 2)
                    line3 = f"[{user_color}]│ {' ' * padding3}{vram_info_markup} │[/]"
                    return f"{line1}\n{line2}\n{line3}"
                else:
                    # No VRAM, add empty line
                    line3 = f"[{user_color}]│ {' ' * (width - 4)} │[/]"
                    return f"{line1}\n{line2}\n{line3}"
        else:
            # Fallback for when model_text is empty - still need 3 lines
            status1_len = len(visible_status1) + 2
            status2_len = len(visible_status2) + 2 if visible_status2 else 2
            padding1 = max(1, width - status1_len - 2)
            padding2 = max(1, width - status2_len - 2)
            empty_padding = max(1, width - 4)
            
            if bg_color:
                line1 = f"[{user_color} on {bg_color}]│ {status_line1}{' ' * padding1} │[/]"
                line2 = f"[{user_color} on {bg_color}]│ {status_line2}{' ' * padding2} │[/]" if status_line2 else f"[{user_color} on {bg_color}]│ {' ' * empty_padding} │[/]"
                line3 = f"[{user_color} on {bg_color}]│ {' ' * empty_padding} │[/]"
                return f"{line1}\n{line2}\n{line3}"
            else:
                line1 = f"[{user_color}]│ {status_line1}{' ' * padding1} │[/]"
                line2 = f"[{user_color}]│ {status_line2}{' ' * padding2} │[/]" if status_line2 else f"[{user_color}]│ {' ' * empty_padding} │[/]"
                line3 = f"[{user_color}]│ {' ' * empty_padding} │[/]"
                return f"{line1}\n{line2}\n{line3}"
