"""Download progress management"""

from textual.widgets import Static
from theme_loader import get_theme_loader
from config import LMSTUDIO_URL, VLLM_API_KEY
from .utils import strip_markup
from . import api_client


class DownloadManager:
    """Manages download progress polling and UI updates"""
    
    def __init__(self, settings, notify_callback, log_callback):
        self.settings = settings
        self.notify = notify_callback
        self.log = log_callback
        self.download_active = False
    
    async def poll_progress(self, progress_widget: Static, refresh_callback) -> bool:
        """
        Poll for download progress and update progress bar
        Returns False to stop polling, True to continue
        """
        try:
            endpoint = self.settings.get("endpoint", LMSTUDIO_URL)
            data = await api_client.get_download_progress(endpoint)
            
            if not data:
                return True
            
            status = data.get('status')
            progress = data.get('progress', 0)
            model = data.get('model', '')
            
            theme = get_theme_loader()
            user_color = theme.get_color("user_color", "cyan")
            ai_color = theme.get_color("ai_color", "yellow")
            inner_width = 66
            
            if status == 'complete':
                progress_widget.update(f"[{ai_color}]│{' ' * (inner_width + 2)}│[/]")
                self.download_active = False
                self.notify(f"✓ Download complete! {model} is ready.", severity="information", timeout=5)
                await refresh_callback()
                return False
            
            elif status == 'error':
                progress_widget.update(f"[{ai_color}]│{' ' * (inner_width + 2)}│[/]")
                self.download_active = False
                error = data.get('error', 'Unknown error')
                self.notify(f"✗ Download failed: {error}", severity="error", timeout=10)
                return False
            
            elif status != 'idle':
                filled = progress // 5
                empty = 20 - filled
                bar = f"[{user_color}]{'⣿' * filled}[/][dim]{'⣀' * empty}[/]"
                status_text = f"[{ai_color}]Downloading {model}...[/] [{bar}] [{user_color}]{progress}%[/] [dim]{status}[/]"
                padding = max(0, inner_width - len(strip_markup(status_text)))
                progress_widget.update(f"[{ai_color}]│ {status_text}{' ' * padding} │[/]")
            
            return True
            
        except Exception as e:
            self.log(f"Progress poll error: {e}")
            return True
