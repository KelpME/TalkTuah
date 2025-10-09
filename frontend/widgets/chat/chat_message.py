from textual.widgets import Static
from theme_loader import get_theme_loader


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


class ChatMessage(Static):
    """A single chat message widget"""
    
    def __init__(self, role: str, content: str, timestamp: str):
        super().__init__()
        self.role = role
        self.content = content
        self.timestamp = timestamp
    
    def get_line_color_by_position(self, line_index: int, viewport_height: int) -> str:
        theme = get_theme_loader()
        
        gradient_top = theme.get_color("gradient_top", "#f85552")
        gradient_mid = theme.get_color("gradient_mid", "#7fbbb3")
        gradient_bottom = theme.get_color("gradient_bottom", "#a7c080")
        
        if viewport_height <= 1:
            return gradient_mid
        
        # Calculate gradient based on viewport position
        # line_index: position relative to viewport top (can be negative or > viewport_height)
        # We want: 0 = red (top of screen), viewport_height = green (bottom of screen)
        
        if line_index < 0:
            # Above viewport - use top color
            return gradient_top
        elif line_index >= viewport_height:
            # Below viewport - use bottom color
            return gradient_bottom
        else:
            # In viewport - calculate gradient
            gradient_factor = line_index / (viewport_height - 1)
            
            if gradient_factor < 0.5:
                return interpolate_color(gradient_top, gradient_mid, gradient_factor * 2)
            else:
                return interpolate_color(gradient_mid, gradient_bottom, (gradient_factor - 0.5) * 2)
    
    def render(self) -> str:
        theme = get_theme_loader()
        
        if self.role == "user":
            prefix = "YOU"
            border_color = theme.get_color("user_color", "cyan")
        else:
            prefix = "AI"
            border_color = theme.get_color("ai_color", "yellow")
        
        color_name = border_color
        content_lines = self.content.split('\n')
        max_content_len = max(len(line) for line in content_lines) if content_lines else 0
        
        title_part = f" {prefix} │ {self.timestamp} "
        visible_title_len = len(title_part)
        
        content_width_needed = max_content_len + 4
        title_width_needed = visible_title_len + 6
        box_width = max(content_width_needed, title_width_needed)
        
        max_width = self.size.width if self.size.width > 20 else 100
        box_width = min(box_width, max_width)
        
        title_with_brackets = f"┤{title_part}├"
        dash_space = box_width - len(title_with_brackets) - 2
        
        if self.role == "user":
            left_padding = dash_space
            right_padding = 0
        else:
            left_padding = 0
            right_padding = dash_space
        
        try:
            scroll_parent = self.parent
            while scroll_parent and scroll_parent.__class__.__name__ != 'VerticalScroll':
                scroll_parent = scroll_parent.parent
            
            if scroll_parent and hasattr(scroll_parent, 'scroll_offset'):
                viewport_height = scroll_parent.size.height if scroll_parent.size.height > 0 else 30
                widget_y = self.region.y if hasattr(self, 'region') else 0
                scroll_y = scroll_parent.scroll_offset.y if hasattr(scroll_parent.scroll_offset, 'y') else 0
                
                # Calculate position relative to viewport (0 = top of screen, viewport_height = bottom)
                visible_y = widget_y - scroll_y
                
                lines_before = visible_y
                viewport_total = viewport_height
            else:
                lines_before = 0
                viewport_total = 30
        except:
            lines_before = 0
            viewport_total = 30
        
        header_line = f"[{color_name}]╭{'─' * left_padding}{title_with_brackets}{'─' * right_padding}╮[/]"
        
        body_lines = []
        # Start at line 1 (after header)
        line_offset = 1
        
        for line in content_lines:
            inner_width = box_width - 2
            available_space = inner_width - 2
            line_len = len(line)
            
            # Calculate color based on viewport position (screen position)
            # lines_before = message top Y relative to viewport, line_offset = current line within message
            screen_line = lines_before + line_offset
            
            # Debug: clamp screen_line to viewport to see gradient properly
            # screen_line can be: negative (above screen), 0-viewport_height (on screen), >viewport_height (below screen)
            line_color = self.get_line_color_by_position(screen_line, viewport_total)
            
            if line_len <= available_space:
                padding_needed = available_space - line_len
                body_lines.append(f"[{color_name}]│[/] [{line_color}]{line}[/]{' ' * padding_needed} [{color_name}]│[/]")
                line_offset += 1
            else:
                words = line.split(' ')
                current_line = ""
                
                for word in words:
                    test_line = current_line + (" " if current_line else "") + word
                    
                    if len(test_line) <= available_space:
                        current_line = test_line
                    else:
                        if current_line:
                            screen_line = lines_before + line_offset
                            line_color = self.get_line_color_by_position(screen_line, viewport_total)
                            padding_needed = available_space - len(current_line)
                            body_lines.append(f"[{color_name}]│[/] [{line_color}]{current_line}[/]{' ' * padding_needed} [{color_name}]│[/]")
                            line_offset += 1
                        
                        if len(word) <= available_space:
                            current_line = word
                        else:
                            current_line = word[:available_space]
                
                if current_line:
                    screen_line = lines_before + line_offset
                    line_color = self.get_line_color_by_position(screen_line, viewport_total)
                    padding_needed = available_space - len(current_line)
                    body_lines.append(f"[{color_name}]│[/] [{line_color}]{current_line}[/]{' ' * padding_needed} [{color_name}]│[/]")
                    line_offset += 1
        
        body = '\n'.join(body_lines)
        footer_line = f"[{color_name}]╰{'─' * (box_width - 2)}╯[/]"
        
        container_width = self.size.width if self.size.width > 20 else 100
        
        if self.role == "user":
            left_padding = max(0, container_width - box_width)
            pad_str = " " * left_padding
            
            header_padded = pad_str + header_line
            body_padded = "\n".join([pad_str + line for line in body.split('\n')])
            footer_padded = pad_str + footer_line
            
            return f"{header_padded}\n{body_padded}\n{footer_padded}"
        else:
            return f"{header_line}\n{body}\n{footer_line}"
