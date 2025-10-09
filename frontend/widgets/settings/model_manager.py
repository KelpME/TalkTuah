"""Model management widget for downloading HuggingFace models"""

from textual.widgets import Static, Input
from textual.containers import Vertical, Horizontal
from textual.message import Message
from theme_loader import get_theme_loader
from config import LMSTUDIO_URL, VLLM_API_KEY
from settings import get_settings
from ..layout.borders import SideBorder
from .huggingface_models import get_autocomplete_suggestions, format_model_suggestion, POPULAR_MODELS
import httpx


class ModelListItem(Static, can_focus=True):
    """Clickable model list item"""
    
    def __init__(self, model_id: str, inner_width: int = 66):
        super().__init__()
        self.model_id = model_id
        self.inner_width = inner_width
        self.can_focus = True
    
    def render(self) -> str:
        theme = get_theme_loader()
        ai_color = theme.get_color("ai_color", "cyan")
        user_color = theme.get_color("user_color", "cyan")
        
        # Format with VRAM info
        display_text = format_model_suggestion(self.model_id)
        padding = max(0, self.inner_width - len(display_text))
        
        if self.has_focus:
            return f"[{ai_color}]│ [{user_color}]▶ {display_text}[/]{' ' * padding} │[/]"
        else:
            return f"[{ai_color}]│ [dim]{display_text}[/dim]{' ' * padding} │[/]"
    
    def on_click(self) -> None:
        """Handle click on model item"""
        self.post_message(ModelDownloadRequested(self.model_id))
    
    def on_key(self, event) -> None:
        """Handle enter key"""
        if event.key == "enter":
            self.post_message(ModelDownloadRequested(self.model_id))


class ModelDownloadRequested(Message):
    """Message when model download is requested"""
    
    def __init__(self, model_id: str):
        super().__init__()
        self.model_id = model_id


class ModelManager(Static):
    """Widget for managing model downloads"""
    
    CSS = """
    ModelManager {
        width: 100%;
        height: auto;
    }
    
    #model-download-box {
        width: 100%;
        height: auto;
    }
    
    #model-download-input {
        width: 100%;
        height: 1;
        background: $surface;
        color: $text;
        border: none;
        padding: 0 1;
        margin: 0;
    }
    
    #model-download-input:focus {
        background: $surface;
        border: none;
    }
    
    #model-list-container {
        width: 100%;
        height: auto;
        max-height: 10;
        overflow-y: auto;
    }
    
    ModelListItem {
        width: 100%;
        height: 1;
    }
    """
    
    def __init__(self, inner_width: int = 66):
        super().__init__()
        self.inner_width = inner_width
        self.filtered_models = []
    
    def compose(self):
        theme = get_theme_loader()
        ai_color = theme.get_color("ai_color", "cyan")
        
        # Download section
        yield Static(f"[{ai_color}]│ [dim]Download from HuggingFace:[/dim]{' ' * (self.inner_width - 26)} │[/]")
        with Horizontal(id="model-download-box"):
            yield SideBorder(color_key="ai_color")
            yield Input(
                placeholder="Search models...",
                id="model-download-input"
            )
            yield SideBorder(color_key="ai_color")
        
        download_help = "[dim]Type to filter, click or press Enter on a model to download[/dim]"
        padding = max(0, self.inner_width - len(self.strip_markup(download_help)))
        yield Static(f"[{ai_color}]│ {download_help}{' ' * padding} │[/]")
        
        # Model list container
        with Vertical(id="model-list-container"):
            pass
    
    def strip_markup(self, text: str) -> str:
        """Remove Rich markup tags from text"""
        import re
        return re.sub(r'\[.*?\]', '', text)
    
    async def on_mount(self) -> None:
        """Initialize with all models"""
        await self.update_model_list("")
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Filter models as user types"""
        if event.input.id == "model-download-input":
            self.call_after_refresh(lambda: self.update_model_list(event.value))
    
    async def update_model_list(self, search_term: str) -> None:
        """Update the model list based on search term"""
        container = self.query_one("#model-list-container", Vertical)
        
        # Clear existing items
        await container.remove_children()
        
        # Filter models
        if search_term:
            self.filtered_models = get_autocomplete_suggestions(search_term)
        else:
            self.filtered_models = POPULAR_MODELS[:20]  # Show first 20 by default
        
        # Add model items
        for model_id in self.filtered_models:
            await container.mount(ModelListItem(model_id, self.inner_width))
    
    async def on_model_download_requested(self, message: ModelDownloadRequested) -> None:
        """Handle model download request from list item"""
        model_id = message.model_id
        
        # Clear the search input
        try:
            input_widget = self.query_one("#model-download-input", Input)
            input_widget.value = ""
        except:
            pass
        
        # Show confirmation
        self.notify(
            f"Starting download: {model_id}",
            severity="information",
            timeout=3
        )
        
        # Call API to get download instructions
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
