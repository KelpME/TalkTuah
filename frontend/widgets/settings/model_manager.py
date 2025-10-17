"""Model management widget for downloading HuggingFace models"""

from textual.widgets import Static, Input
from textual.containers import Vertical, Horizontal
from textual.message import Message
from utils.theme import get_theme_loader
from config import LMSTUDIO_URL, VLLM_API_KEY
from settings import get_settings
from utils.markup import strip_markup
from ..layout.borders import SideBorder
from .huggingface_models import get_autocomplete_suggestions, format_model_suggestion, POPULAR_MODELS
from . import api_client
import httpx


class ModelListItem(Static, can_focus=True):
    """Clickable model list item - requires double-click to download"""
    
    def __init__(self, model_id: str, inner_width: int = 66):
        super().__init__()
        self.model_id = model_id
        self.inner_width = inner_width
        self.can_focus = True
        self.click_count = 0
        self.last_click_time = 0
    
    def render(self) -> str:
        theme = get_theme_loader()
        ai_color = theme.get_color("ai_color", "cyan")
        user_color = theme.get_color("user_color", "cyan")
        
        # Format with VRAM info
        display_text = format_model_suggestion(self.model_id)
        
        # Add double-click hint
        if self.click_count == 1:
            hint = " [dim](click again to download)[/dim]"
        else:
            hint = ""
        
        display_with_hint = display_text + hint
        padding = max(0, self.inner_width - len(strip_markup(display_with_hint)))
        
        if self.has_focus or self.click_count == 1:
            return f"[{ai_color}]│ [{user_color}]▶ {display_with_hint}[/]{' ' * padding} │[/]"
        else:
            return f"[{ai_color}]│ [dim]{display_text}[/dim]{' ' * padding} │[/]"
    
    def on_click(self) -> None:
        """Handle click on model item - requires double-click"""
        import time
        current_time = time.time()
        
        # Reset if more than 2 seconds since last click
        if current_time - self.last_click_time > 2.0:
            self.click_count = 0
        
        self.click_count += 1
        self.last_click_time = current_time
        
        if self.click_count >= 2:
            # Double-click confirmed - trigger download
            self.post_message(ModelDownloadRequested(self.model_id))
            self.click_count = 0
        else:
            # First click - show hint
            self.refresh()
            # Reset after 2 seconds
            self.set_timer(2.0, self._reset_click_count)
    
    def _reset_click_count(self):
        """Reset click count and refresh"""
        self.click_count = 0
        self.refresh()
    
    def on_key(self, event) -> None:
        """Handle enter key - immediate download"""
        if event.key == "enter":
            self.post_message(ModelDownloadRequested(self.model_id))


class ModelDownloadRequested(Message):
    """Message when model download is requested"""
    
    def __init__(self, model_id: str):
        super().__init__()
        self.model_id = model_id


class ModelManager(Static):
    """Widget for managing model downloads"""
    
    # Styles defined in settings.tcss (shared with SettingsModal)
    
    def __init__(self, inner_width: int = 66):
        super().__init__()
        self.inner_width = inner_width
        self.filtered_models = []
        self.downloaded_models = []
    
    def compose(self):
        theme = get_theme_loader()
        ai_color = theme.get_color("ai_color", "cyan")
        # Download section
        yield Static(f"[{ai_color}]│ [dim]Download from HuggingFace:[/dim]{' ' * (self.inner_width - 26)} │[/]")
        with Horizontal(id="model-download-box"):
            yield SideBorder(color_key="ai_color")
            yield Input(
                placeholder="Start typing model name (e.g., Qwen/Qwen2.5-1.5B-Instruct)",
                id="model-download-input"
            )
            yield SideBorder(color_key="ai_color")
        
        download_help = "[dim]Type to filter, click or press Enter to download[/dim]"
        padding = max(0, self.inner_width - len(strip_markup(download_help)))
        yield Static(f"[{ai_color}]│ {download_help}{' ' * padding} │[/]", id="download-help-text")
        
        # Model list container
        with Vertical(id="model-list-container"):
            pass
    
    
    async def on_mount(self) -> None:
        """Initialize with all models and fetch downloaded ones"""
        # Fetch list of already downloaded models
        settings = get_settings()
        endpoint = settings.get("endpoint", LMSTUDIO_URL)
        self.downloaded_models = await api_client.fetch_downloaded_models(endpoint)
        
        # Update help text with count
        self.update_help_text()
        
        await self.update_model_list("")
    
    def update_help_text(self):
        """Update help text to show how many models are already downloaded"""
        try:
            theme = get_theme_loader()
            ai_color = theme.get_color("ai_color", "cyan")
            
            downloaded_count = len(self.downloaded_models)
            if downloaded_count > 0:
                help_msg = f"[dim]Type to filter ({downloaded_count} already downloaded, excluded from list)[/dim]"
            else:
                help_msg = "[dim]Type to filter, click or press Enter to download[/dim]"
            
            padding = max(0, self.inner_width - len(strip_markup(help_msg)))
            help_widget = self.query_one("#download-help-text", Static)
            help_widget.update(f"[{ai_color}]│ {help_msg}{' ' * padding} │[/]")
        except:
            pass
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Filter models as user types"""
        if event.input.id == "model-download-input":
            self.call_after_refresh(lambda: self.update_model_list(event.value))
    
    async def update_model_list(self, search_term: str) -> None:
        """Update the model list based on search term, excluding downloaded models"""
        container = self.query_one("#model-list-container", Vertical)
        
        # Clear existing items
        await container.remove_children()
        
        # Filter models based on search
        if search_term:
            candidate_models = get_autocomplete_suggestions(search_term)
        else:
            candidate_models = POPULAR_MODELS[:20]  # Show first 20 by default
        
        # Exclude already downloaded models
        self.filtered_models = [
            model for model in candidate_models 
            if model not in self.downloaded_models
        ]
        
        # Add model items
        if self.filtered_models:
            for model_id in self.filtered_models:
                await container.mount(ModelListItem(model_id, self.inner_width))
        else:
            # Show message if all models are downloaded
            theme = get_theme_loader()
            ai_color = theme.get_color("ai_color", "cyan")
            if search_term:
                msg = "[dim]No new models match your search[/dim]"
            else:
                msg = "[dim]All popular models already downloaded[/dim]"
            padding = max(0, self.inner_width - len(strip_markup(msg)))
            await container.mount(Static(f"[{ai_color}]│ {msg}{' ' * padding} │[/]"))
    
    async def on_model_download_requested(self, message: ModelDownloadRequested) -> None:
        """Handle model download request from list item"""
        model_id = message.model_id
        
        # Clear the search input
        try:
            input_widget = self.query_one("#model-download-input", Input)
            input_widget.value = ""
        except:
            pass
        
        # Add to downloaded list immediately to prevent duplicate downloads
        if model_id not in self.downloaded_models:
            self.downloaded_models.append(model_id)
            self.update_help_text()
        
        # Show confirmation
        self.notify(
            f"Starting download: {model_id}",
            severity="information",
            timeout=3
        )
        
        # Refresh the list to remove the downloading model
        await self.update_model_list("")
        
        # Call API to start download
        try:
            settings = get_settings()
            endpoint = settings.get("endpoint", LMSTUDIO_URL)
            download_url = f"{endpoint}/download-model"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    download_url,
                    params={"model_id": model_id, "auto": "true"},
                    headers={"Authorization": f"Bearer {VLLM_API_KEY}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('status') == 'downloading':
                        self.notify(
                            f"✓ {data.get('message')}",
                            severity="information",
                            timeout=5
                        )
                        # Post message to close settings and start progress tracking
                        from .download_started import DownloadStarted
                        self.post_message(DownloadStarted(model_id))
                    else:
                        command = data.get('command', '')
                        self.notify(
                            f"Run: {command}",
                            severity="information",
                            timeout=10
                        )
                else:
                    self.notify(f"Failed: {response.status_code}", severity="error", timeout=5)
        except Exception as e:
            self.notify(f"Error: {str(e)}", severity="error", timeout=5)
