from textual.widgets import Static, Label, Input, Button, Select
from textual.containers import Container, Vertical, Horizontal as HorizontalContainer
from textual.screen import ModalScreen
from theme_loader import get_theme_loader
from pathlib import Path
from version import __version__
from config import LMSTUDIO_URL, VLLM_API_KEY
from settings import get_settings
from ..layout.borders import SideBorder
from ..layout.modal_footer import ModalFooter
from .model_manager import ModelManager, ModelDownloadRequested
from .model_option import ModelOption, ModelSelected
from .theme_option import ThemeOption, ThemeSelected
from .temperature_slider import TemperatureSlider
from .gpu_memory_slider import GPUMemorySlider, GPUMemoryChanged
from .max_tokens_slider import MaxTokensSlider, MaxTokensChanged
from .huggingface_models import get_model_info
from .endpoint_widget import EndpointLine
from .download_manager import DownloadManager
from .utils import strip_markup
from . import api_client
import asyncio


class SettingsModal(ModalScreen):
    """Settings modal for theme selection"""
    
    # External CSS for better organization (relative to frontend/)
    CSS_PATH = "../../styles/settings.tcss"
    
    def __init__(self, current_theme: str):
        super().__init__()
        self.current_theme = current_theme
        self.available_themes = self.get_available_themes()
        self.settings = get_settings()
        self.temp_slider = None
        self.gpu_memory_slider = None
        self.max_tokens_slider = None
        self.endpoint_input = None
        self.available_models = []
        self.download_manager = DownloadManager(
            self.settings,
            self.notify,
            self.log
        )
        self.progress_timer = None
    
    def compose(self):
        theme = get_theme_loader()
        ai_color = theme.get_color("ai_color", "cyan")
        user_color = theme.get_color("user_color", "cyan")
        
        # Fixed width for consistent borders
        width = 70
        inner_width = width - 4  # Account for "│ " and " │"
        
        with Container(id="settings-container"):
            # Top border with embedded title
            # Total width is 70: ╭ (1) + dashes + ┤ (1) + space + title + space + ├ (1) + dashes + ╮ (1)
            # So: 1 + left_dash + 1 + 1 + len(title) + 1 + 1 + right_dash + 1 = 70
            # Therefore: left_dash + right_dash = 70 - 6 - len(title) = 64 - len(title)
            title = "SETTINGS"
            total_dashes = width - 6 - len(title)  # 70 - 6 - 8 = 56
            left_dash = total_dashes // 2
            right_dash = total_dashes - left_dash
            yield Static(f"[{ai_color}]╭{'─' * left_dash}┤ [bold]{title}[/bold] ├{'─' * right_dash}╮[/]")
            yield Static(f"[{ai_color}]│{' ' * (inner_width + 2)}│[/]")
            
            # Model Settings section
            section_title = "Model Settings"
            total_dashes = width - 6 - len(section_title)
            left_dash = 2
            right_dash = total_dashes - left_dash
            yield Static(f"[{ai_color}]├{'─' * left_dash}┤ [bold]{section_title}[/bold] ├{'─' * right_dash}┤[/]")
            yield Static(f"[{ai_color}]│{' ' * (inner_width + 2)}│[/]")
            
            # API Endpoint input field
            endpoint_label = "API Endpoint:"
            padding = max(0, inner_width - len(endpoint_label))
            yield Static(f"[{ai_color}]│ {endpoint_label}{' ' * padding} │[/]")
            
            with HorizontalContainer(id="endpoint-input-box"):
                yield SideBorder(color_key="ai_color")
                self.endpoint_input = Input(
                    value=self.settings.get("endpoint", LMSTUDIO_URL),
                    placeholder="http://localhost:8787/api",
                    id="endpoint-input"
                )
                yield self.endpoint_input
                yield SideBorder(color_key="ai_color")
            
            yield Static(f"[{ai_color}]│{' ' * (inner_width + 2)}│[/]")
            
            # Model selection (will be populated on mount)
            yield Static(f"[{ai_color}]│ [bold]Active Model:[/bold] [dim](click to switch)[/dim]{' ' * (inner_width - 31)} │[/]")
            with Vertical(id="model-list"):
                yield Static(f"[{ai_color}]│ [dim]Loading...[/dim]{' ' * (inner_width - 11)} │[/]", id="models-loading")
            
            yield Static(f"[{ai_color}]│{' ' * (inner_width + 2)}│[/]")
            
            # Model Management section with clickable list
            yield ModelManager(inner_width=inner_width)
            
            yield Static(f"[{ai_color}]│{' ' * (inner_width + 2)}│[/]")
            
            self.temp_slider = TemperatureSlider(self.settings.get("temperature", 0.7), inner_width)
            yield self.temp_slider
            
            yield Static(f"[{ai_color}]│{' ' * (inner_width + 2)}│[/]")
            
            self.gpu_memory_slider = GPUMemorySlider(self.settings.get("gpu_memory_utilization", 0.75), inner_width)
            yield self.gpu_memory_slider
            
            yield Static(f"[{ai_color}]│{' ' * (inner_width + 2)}│[/]")
            
            # Get max tokens for current model
            from config import VLLM_MODEL
            model_info = get_model_info(VLLM_MODEL)
            model_max_tokens = model_info.get("max_tokens", 4096)
            current_max_tokens = self.settings.get("max_tokens", min(2048, model_max_tokens))
            
            self.max_tokens_slider = MaxTokensSlider(current_max_tokens, model_max_tokens, inner_width)
            yield self.max_tokens_slider
            
            help_line = "[dim]Use ← → or drag to adjust[/dim]"
            padding = inner_width - len(strip_markup(help_line))
            yield Static(f"[{ai_color}]│ {help_line}{' ' * padding} │[/]")
            
            # Theme Selection section
            section_title = "Theme Selection"
            total_dashes = width - 6 - len(section_title)
            left_dash = 2
            right_dash = total_dashes - left_dash
            yield Static(f"[{ai_color}]├{'─' * left_dash}┤ [bold]{section_title}[/bold] ├{'─' * right_dash}┤[/]")
            yield Static(f"[{ai_color}]│{' ' * (inner_width + 2)}│[/]")
            
            # Theme list
            yield ThemeOption("system", self.current_theme == "system", inner_width)
            
            for theme_name in self.available_themes:
                if theme_name != "system":
                    yield ThemeOption(theme_name, self.current_theme == theme_name, inner_width)
            
            yield Static(f"[{ai_color}]│{' ' * (inner_width + 2)}│[/]")
            
            # Bottom border with clickable ESC button and version
            yield ModalFooter(right_text=f"v{__version__}", width=width)
    
    async def fetch_available_models(self):
        """Fetch downloaded models from filesystem via API"""
        endpoint = self.settings.get("endpoint", LMSTUDIO_URL)
        return await api_client.fetch_downloaded_models(endpoint)
    
    async def get_active_model(self):
        """Get the currently active model from vLLM"""
        endpoint = self.settings.get("endpoint", LMSTUDIO_URL)
        return await api_client.fetch_active_model(endpoint)
    
    def get_available_themes(self) -> list:
        """Get list of available themes"""
        themes = ["system"]  # Always include system theme
        
        # Check frontend/themes directory
        themes_dir = Path(__file__).parent.parent / "themes"
        if themes_dir.exists():
            for theme_file in themes_dir.glob("*.theme"):
                theme_name = theme_file.stem
                if theme_name != "terminal":  # Skip terminal theme
                    themes.append(theme_name)
        
        return themes
    
    async def on_mount(self) -> None:
        """Focus the temperature slider and fetch available models"""
        # Fetch downloaded models
        models = await self.fetch_available_models()
        inner_width = 66
        model_list = self.query_one("#model-list", Vertical)
        
        # Remove loading message
        try:
            loading_widget = self.query_one("#models-loading", Static)
            loading_widget.remove()
        except:
            pass
        
        # Clear and rebuild model list
        await model_list.remove_children()
        
        if models:
            # Get currently active model from vLLM (not from settings)
            active_model = await self.get_active_model()
            
            # Add model options - mark the one that's actually loaded in vLLM
            for model in models:
                await model_list.mount(ModelOption(model, model == active_model, inner_width))
        else:
            # Show error
            theme = get_theme_loader()
            ai_color = theme.get_color("ai_color", "cyan")
            error_text = "[red]No models downloaded[/red]"
            padding = max(0, inner_width - len("No models downloaded"))
            await model_list.mount(Static(f"[{ai_color}]│ {error_text}{' ' * padding} │[/]"))
        
        if self.temp_slider:
            self.temp_slider.focus()
    
    async def on_model_selected(self, message: ModelSelected) -> None:
        """Handle model selection - switches model and restarts vLLM"""
        # Update selected model in settings
        self.settings.set("selected_model", message.model_name)
        
        # Update max_tokens to 75% of new model's max to leave room for input
        model_info = get_model_info(message.model_name)
        model_max_tokens = model_info.get("max_tokens", 4096)
        recommended_max_tokens = int(model_max_tokens * 0.75)
        
        # Update the slider if it exists
        if self.max_tokens_slider:
            self.max_tokens_slider.max_value = float(model_max_tokens)
            self.max_tokens_slider.value = float(recommended_max_tokens)
            self.max_tokens_slider.refresh()
            self.settings.set("max_tokens", recommended_max_tokens)
            self.notify(
                f"Max tokens set to {recommended_max_tokens} (75% of {model_max_tokens})",
                severity="information",
                timeout=3
            )
        
        # Update UI to show selection
        for option in self.query(ModelOption):
            option.is_selected = (option.model_name == message.model_name)
            option.refresh()
        
        # Call API to switch model
        try:
            endpoint = self.settings.get("endpoint", LMSTUDIO_URL)
            self.notify(f"Switching to {message.model_name}...", severity="information", timeout=2)
            
            data = await api_client.switch_model(message.model_name, endpoint)
            self.notify(
                f"✓ {data.get('message')}\n{data.get('info')}",
                severity="information",
                timeout=10
            )
                
        except Exception as e:
            self.notify(f"Error switching model: {str(e)}", severity="error", timeout=5)
    
    def on_theme_selected(self, message: ThemeSelected) -> None:
        """Handle theme selection"""
        self.save_settings()
        self.dismiss(message.theme_name)
    
    def save_settings(self):
        """Save all settings"""
        if self.temp_slider:
            self.settings.set("temperature", round(self.temp_slider.value, 2))
        if self.gpu_memory_slider:
            self.settings.set("gpu_memory_utilization", round(self.gpu_memory_slider.value, 2))
        if self.max_tokens_slider:
            self.settings.set("max_tokens", int(self.max_tokens_slider.value))
        if self.endpoint_input:
            self.settings.set("endpoint", self.endpoint_input.value.strip())
    
    
    async def refresh_model_lists(self) -> None:
        """Refresh both the available models dropdown and downloaded models list"""
        try:
            # Refresh available models from API
            models = await self.fetch_available_models()
            inner_width = 66
            model_list = self.query_one("#model-list", Vertical)
            
            # Clear existing models
            await model_list.remove_children()
            
            if models:
                # Get currently selected model
                selected_model = self.settings.get("selected_model")
                
                # Add model options
                for model in models:
                    await model_list.mount(ModelOption(model, model == selected_model, inner_width))
            else:
                # Show error
                theme = get_theme_loader()
                ai_color = theme.get_color("ai_color", "cyan")
                error_text = "[red]Unable to fetch models[/red]"
                padding = max(0, inner_width - len("Unable to fetch models"))
                await model_list.mount(Static(f"[{ai_color}]│ {error_text}{' ' * padding} │[/]"))
            
        except Exception as e:
            self.log(f"Failed to refresh model lists: {e}")
    
    async def poll_download_progress(self) -> None:
        """Poll for download progress and update progress bar"""
        try:
            progress_widget = self.query_one("#download-progress", Static)
            should_continue = await self.download_manager.poll_progress(
                progress_widget,
                self.refresh_model_lists
            )
            if not should_continue:
                return False
        except Exception as e:
            self.log(f"Progress poll error: {e}")
    
    def on_unmount(self) -> None:
        """Save settings when modal is closed by any method"""
        self.save_settings()
    
    def on_key(self, event) -> None:
        """Handle key presses"""
        if event.key == "escape":
            self.save_settings()
            # Check if this screen is at the top of the stack before dismissing
            if self.app.screen is self:
                self.dismiss(None)
