"""Compact download progress bar for main chat page"""

from textual.widgets import Static
from textual.reactive import reactive
from utils.theme import get_theme_loader
from datetime import datetime
import httpx
from config import LMSTUDIO_URL, VLLM_API_KEY
from user_preferences import get_settings


class DownloadProgressBar(Static):
    """Compact progress bar showing model download status"""
    
    progress = reactive(0)
    status = reactive("idle")
    model_name = reactive(None)
    show_load_button = reactive(False)
    load_button_timer = reactive(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.download_complete_time = None
        # Start hidden
        self.styles.height = 0
    
    def watch_status(self, old_status: str, new_status: str) -> None:
        """Watch status changes to update visibility"""
        self._update_visibility()
    
    def watch_show_load_button(self, old_value: bool, new_value: bool) -> None:
        """Watch load button state to update visibility"""
        self._update_visibility()
    
    def _update_visibility(self) -> None:
        """Update widget visibility based on status"""
        if self.status == "idle" and not self.show_load_button:
            self.styles.height = 0
        else:
            self.styles.height = "auto"
        self.refresh()
    
    def render(self) -> str:
        if self.status == "idle" and not self.show_load_button:
            # Completely hide by returning empty and setting height to 0
            self.styles.height = 0
            return ""
        
        # Show the bar - set height to auto
        self.styles.height = "auto"
        
        theme = get_theme_loader()
        ai_color = theme.get_color("ai_color", "cyan")
        user_color = theme.get_color("user_color", "cyan")
        bg_color = theme.get_color("main_bg", "")
        
        # Get width for borders
        width = self.size.width if self.size.width > 0 else 80
        
        # Build background style
        if bg_color:
            bg_style = f" on {bg_color}"
        else:
            bg_style = ""
        
        # Compact display
        if self.show_load_button:
            # Show "Load Model" button for 8 seconds after completion
            remaining = max(0, 8 - self.load_button_timer)
            content = f"[{user_color}]▶ Click to load: {self.model_name} ({remaining}s)[/]"
            padding = max(1, width - len(f"▶ Click to load: {self.model_name} ({remaining}s)") - 4)
            return f"[{ai_color}{bg_style}]│ {content}{' ' * padding} │[/]"
        
        # Show progress bar
        bar_width = 30
        filled = int((self.progress / 100) * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)
        
        # Short model name
        short_name = self.model_name.split('/')[-1] if self.model_name and '/' in self.model_name else self.model_name
        
        if self.status == "downloading":
            content = f"Downloading {short_name}: [{user_color}]{bar}[/{user_color}] {self.progress}%"
            visible_len = len(f"Downloading {short_name}: {bar} {self.progress}%")
            padding = max(1, width - visible_len - 4)
            return f"[{ai_color}{bg_style}]│ {content}{' ' * padding} │[/]"
        elif self.status == "complete":
            content = f"✓ Downloaded {short_name}: [{user_color}]{bar}[/{user_color}] 100%"
            visible_len = len(f"✓ Downloaded {short_name}: {bar} 100%")
            padding = max(1, width - visible_len - 4)
            return f"[{ai_color}{bg_style}]│ {content}{' ' * padding} │[/]"
        elif self.status == "error":
            content = f"[red]✗ Failed {short_name}[/red]"
            visible_len = len(f"✗ Failed {short_name}")
            padding = max(1, width - visible_len - 4)
            return f"[{ai_color}{bg_style}]│ {content}{' ' * padding} │[/]"
        
        return ""
    
    async def update_progress(self, progress_data: dict):
        """Update progress from API poll"""
        self.status = progress_data.get("status", "idle")
        self.progress = progress_data.get("progress", 0)
        self.model_name = progress_data.get("model")
        
        # If completed, start the 8-second load button timer
        if self.status == "complete" and not self.download_complete_time:
            self.download_complete_time = datetime.now()
            self.show_load_button = True
            self.load_button_timer = 0
        
        self.refresh()
    
    async def poll_progress(self):
        """Poll the download progress endpoint"""
        try:
            settings = get_settings()
            endpoint = settings.get("endpoint", LMSTUDIO_URL)
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{endpoint}/download-progress",
                    headers={"Authorization": f"Bearer {VLLM_API_KEY}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    await self.update_progress(data)
                    
                    # If showing load button, increment timer
                    if self.show_load_button:
                        self.load_button_timer += 1
                        if self.load_button_timer >= 8:
                            # Hide after 8 seconds
                            self.reset()
                    
                    # Return True to continue polling if downloading
                    return data.get("status") == "downloading" or self.show_load_button
        except Exception as e:
            self.log(f"Progress poll error: {e}")
        
        return False
    
    def reset(self):
        """Reset progress bar"""
        self.status = "idle"
        self.progress = 0
        self.model_name = None
        self.show_load_button = False
        self.load_button_timer = 0
        self.download_complete_time = None
        self.refresh()
    
    def on_click(self) -> None:
        """Handle click on load button"""
        if self.show_load_button and self.model_name:
            # Post message to load the model
            from .settings.model_option import ModelSelected
            self.post_message(ModelSelected(self.model_name))
            self.reset()
