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
from .utils import strip_markup
from . import api_client
import asyncio


class EndpointLine(Static, can_focus=True):
    """Editable endpoint line with reset button"""
    
    def __init__(self, value: str, default_value: str, inner_width: int = 66):
        super().__init__()
        self.value = value
        self.default_value = default_value
        self.inner_width = inner_width
        self.can_focus = True
        self.editing = False
        self.cursor_pos = len(value)
    
    def render(self) -> str:
        theme = get_theme_loader()
        ai_color = theme.get_color("ai_color", "cyan")
        user_color = theme.get_color("user_color", "cyan")
        
        label = "Endpoint: "
        reset_btn = "[Reset]"
        display_value = self.value if not self.editing else self.value + "█"
        content = label + display_value
        # Calculate padding to push reset button to the right
        # Account for: label + value + space + [Reset] + space = total content
        content_len = len(label) + len(self.value) + 1 + len(reset_btn)
        padding = max(0, self.inner_width - content_len)
        
        if self.editing:
            return f"[{ai_color}]│ [{user_color}]{content}[/]{' ' * padding} [dim]{reset_btn}[/dim] │[/]"
        else:
            return f"[{ai_color}]│ {content}{' ' * padding} [{user_color}]{reset_btn}[/] │[/]"
    
    def on_click(self) -> None:
        self.editing = True
        self.focus()
        self.refresh()
    
    def on_key(self, event) -> None:
        if not self.editing:
            if event.key == "enter":
                self.editing = True
                self.refresh()
            elif event.key == "r":
                # Reset to default
                self.value = self.default_value
                self.refresh()
            return
        
        if event.key == "enter" or event.key == "escape":
            self.editing = False
            self.refresh()
        elif event.key == "backspace":
            if self.value:
                self.value = self.value[:-1]
            self.value += event.key
            self.refresh()


class TemperatureSlider(Static, can_focus=True):
    """Temperature slider widget"""
    
    def __init__(self, value: float = 0.7, inner_width: int = 66):
        super().__init__()
        self.value = value
        self.can_focus = True
        self.dragging = False
        self.inner_width = inner_width
    
    def render(self) -> str:
        theme = get_theme_loader()
        ai_color = theme.get_color("ai_color", "cyan")
        user_color = theme.get_color("user_color", "cyan")
        
        # Create slider bar (0.0 to 2.0)
        slider_width = 40
        position = int((self.value / 2.0) * slider_width)
        
        bar = "─" * position + "●" + "─" * (slider_width - position - 1)
        label = f"Temperature: {self.value:.2f}"
        content_len = len(label) + 1 + slider_width  # label + space + bar
        padding = max(0, self.inner_width - content_len)
        
        return f"[{ai_color}]│ {label} [{user_color}]{bar}[/]{' ' * padding} │[/]"
    
    def on_key(self, event) -> None:
        """Handle arrow keys to adjust temperature"""
        if event.key == "left":
            self.value = max(0.0, self.value - 0.1)
            self.refresh()
        elif event.key == "right":
            self.value = min(2.0, self.value + 0.1)
            self.refresh()
    
    def on_click(self, event) -> None:
        """Handle click to set value and focus"""
        self.focus()
        self._update_from_mouse(event.x)
    
    def on_mouse_down(self, event) -> None:
        """Start dragging"""
        self.dragging = True
        self._update_from_mouse(event.x)
    
    def on_mouse_up(self, event) -> None:
        """Stop dragging"""
        self.dragging = False
    
    def on_mouse_move(self, event) -> None:
        """Update value while dragging"""
        if self.dragging:
            self._update_from_mouse(event.x)
    
    def _update_from_mouse(self, mouse_x: int):
        """Update temperature value based on mouse position"""
        # Calculate where the slider bar starts (after "│ Temperature: 0.00 ")
        label_offset = 20  # Approximate offset to start of slider bar
        slider_width = 40
        
        # Calculate position relative to slider bar
        relative_x = mouse_x - label_offset
        
        if 0 <= relative_x <= slider_width:
            # Convert position to value (0.0 to 2.0)
            self.value = (relative_x / slider_width) * 2.0
            self.value = max(0.0, min(2.0, self.value))  # Clamp
            self.refresh()


class SettingsModal(ModalScreen):
    """Settings modal for theme selection"""
    
    CSS = """
    SettingsModal {
        align: center middle;
    }
    
    #settings-container {
        width: 70;
        max-width: 70;
        height: auto;
        background: $background;
        padding: 0;
        overflow-x: hidden;
    }
    
    #theme-list {
        width: 100%;
        height: auto;
        margin-top: 1;
        margin-bottom: 1;
        padding: 0 2;
    }
    
    ThemeOption {
        width: 100%;
        height: 1;
    }
    
    ModelOption {
        width: 100%;
        height: 1;
    }
    
    #model-list {
        width: 100%;
        max-width: 100%;
        height: auto;
        max-height: 5;
        overflow-y: auto;
    }
    
    Vertical {
        width: 100%;
        max-width: 100%;
        height: auto;
        padding: 0;
        margin: 0;
    }
    
    Container {
        width: 100%;
        height: auto;
        padding: 0;
        margin: 0;
    }
    
    Horizontal {
        width: 100%;
        height: auto;
        padding: 0;
        margin: 0;
    }
    
    #settings-info {
        width: 100%;
        padding: 0 2;
        margin-bottom: 1;
    }
    
    #settings-footer {
        width: 100%;
        text-align: center;
        padding: 0 2;
        margin-top: 1;
        margin-bottom: 1;
    }
    
    #endpoint-input-box {
        width: 100%;
        height: 1;
        layout: horizontal;
    }
    
    #endpoint-input-box SideBorder {
        width: 1;
        height: 1;
    }
    
    #endpoint-input {
        width: 1fr;
        height: 1;
        border: none;
        padding: 0 1;
    }
    
    ModalFooter {
        width: 100%;
        height: 1;
    }
    """
    
    def __init__(self, current_theme: str):
        super().__init__()
        self.current_theme = current_theme
        self.available_themes = self.get_available_themes()
        self.settings = get_settings()
        self.temp_slider = None
        self.endpoint_input = None
        self.available_models = []
        self.download_active = False
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
            endpoint = self.settings.get("endpoint", LMSTUDIO_URL)
            progress_url = f"{endpoint}/download-progress"
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    progress_url,
                    headers={"Authorization": f"Bearer {VLLM_API_KEY}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status')
                    progress = data.get('progress', 0)
                    model = data.get('model', '')
                    
                    theme = get_theme_loader()
                    user_color = theme.get_color("user_color", "cyan")
                    ai_color = theme.get_color("ai_color", "yellow")
                    inner_width = 66
                    
                    progress_widget = self.query_one("#download-progress", Static)
                    
                    if status == 'complete':
                        # Clear progress bar
                        progress_widget.update(f"[{ai_color}]│{' ' * (inner_width + 2)}│[/]")
                        self.download_active = False
                        
                        self.notify(f"✓ Download complete! {model} is ready.", severity="information", timeout=5)
                        
                        # Refresh model lists
                        await self.refresh_model_lists()
                        
                        return False  # Stop polling
                    elif status == 'error':
                        # Clear progress bar
                        progress_widget.update(f"[{ai_color}]│{' ' * (inner_width + 2)}│[/]")
                        self.download_active = False
                        
                        error = data.get('error', 'Unknown error')
                        self.notify(f"✗ Download failed: {error}", severity="error", timeout=10)
                        return False  # Stop polling
                    elif status != 'idle':
                        # Update progress bar
                        filled = progress // 5
                        empty = 20 - filled
                        bar = f"[{user_color}]{'⣿' * filled}[/][dim]{'⣀' * empty}[/]"
                        
                        status_text = f"[{ai_color}]Downloading {model}...[/] [{bar}] [{user_color}]{progress}%[/] [dim]{status}[/]"
                        padding = max(0, inner_width - len(strip_markup(status_text)))
                        
                        progress_widget.update(f"[{ai_color}]│ {status_text}{' ' * padding} │[/]")
        except Exception as e:
            self.log(f"Progress poll error: {e}")
    
    def on_key(self, event) -> None:
        """Handle key presses"""
        if event.key == "escape":
            self.save_settings()
            # Check if this screen is at the top of the stack before dismissing
            if self.app.screen is self:
                self.dismiss(None)
