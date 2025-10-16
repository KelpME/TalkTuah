from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, VerticalScroll
from textual.widgets import Input, Label, Header
from textual.reactive import reactive
from textual import work
import asyncio
from datetime import datetime
from typing import List, Dict
from pathlib import Path
import psutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from llm_client import LLMClient
from config import LMSTUDIO_URL, VLLM_MODEL

import sys
if 'theme_loader' in sys.modules:
    del sys.modules['theme_loader']
from theme_loader import get_theme_loader, reload_theme

from widgets import ChatMessage, ContainerBorder, SideBorder, StatusBar, CustomFooter, KeybindingButton, FooterBorder, FooterEnd, FooterSpacer, SettingsModal
from textual.containers import Horizontal as HorizontalContainer


class OmarchyThemeWatcher(FileSystemEventHandler):
    def __init__(self, app):
        super().__init__()
        self.app = app
    
    def on_modified(self, event):
        if self.app.theme_watcher_enabled and ('theme' in event.src_path or 'btop.theme' in event.src_path):
            self.app.call_from_thread(self.app.reload_theme_colors)
    
    def on_created(self, event):
        if self.app.theme_watcher_enabled and Path(event.src_path).name == 'theme':
            self.app.call_from_thread(self.app.reload_theme_colors)
    
    def on_moved(self, event):
        if self.app.theme_watcher_enabled and hasattr(event, 'dest_path') and Path(event.dest_path).name == 'theme':
            self.app.call_from_thread(self.app.reload_theme_colors)


class TuivLLM(App):
    """BTOP++ styled TUI chatbot interface"""
    
    # Modular CSS organization for better maintainability
    CSS_PATH = [
        "styles/main.tcss",
        "styles/chat.tcss",
        "styles/footer.tcss",
    ]
    
    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+l", "clear_chat", "Clear"),
        ("ctrl+s", "settings", "Settings"),
        ("ctrl+r", "reconnect", "Reconnect"),
    ]
    
    messages: reactive[List[Dict]] = reactive([])
    
    def __init__(self):
        super().__init__()
        self.llm_client = LLMClient()
        self.is_processing = False
        self.theme_observer = None
        self.current_theme = "system"  # Default to Omarchy theme
        self.theme_watcher_enabled = True
        self.is_connected = False
        self.status_update_timer = None
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Container(id="main-box"):
            yield ContainerBorder("STATUS", color_key="user_color", position="top", border_type="corner")
            yield StatusBar(id="status-bar")
            yield ContainerBorder("CONVERSATION", color_key="ai_color", position="top", border_type="divider")
            
            with HorizontalContainer(id="conversation-box"):
                yield SideBorder(color_key="ai_color")
                
                with Vertical(id="conversation-content"):
                    yield VerticalScroll(id="messages-scroll")
                    yield ContainerBorder("INPUT", color_key="ai_color", position="top", border_type="divider")
                    yield Input(placeholder="Type your message here...", id="chat-input")
                yield SideBorder(color_key="ai_color")
            
            yield CustomFooter()
    
    async def on_mount(self) -> None:
        self.title = "Talk-Tuah"
        self.apply_theme_to_css()
        
        status_bar = self.query_one("#status-bar", StatusBar)
        model_name = VLLM_MODEL.split('/')[-1] if '/' in VLLM_MODEL else VLLM_MODEL
        status_bar.status_text = "\n[yellow]● Starting[/yellow]"
        
        # Update model and memory info
        # Initial status update (no polling needed - model name is in config)
        self.update_status_bar_right()
        
        self.start_theme_watcher()
        self.set_interval(0.1, self.refresh_gradient)
        
        # No polling timer - status only updates when needed:
        # 1. On startup (above)
        # 2. After sending a message (checks connection)
        # 3. After switching models (in settings callback)
        self.status_update_timer = None
        
        # Focus input field
        self.query_one("#chat-input", Input).focus()
    
    def refresh_gradient(self):
        try:
            messages_scroll = self.query_one("#messages-scroll", VerticalScroll)
            for message in messages_scroll.query(ChatMessage):
                message.refresh()
        except:
            pass
    
    def update_status_bar_right(self, check_connection: bool = True):
        """Update model and memory info on status bar
        
        Args:
            check_connection: If True, ping API to check if vLLM is responding
        """
        try:
            status_bar = self.query_one("#status-bar", StatusBar)
            
            # Get currently loaded model from API (not config)
            model_name = "Unknown"
            connection_status = "[green]● Ready[/green]"
            
            # Check connection and get actual loaded model
            if check_connection:
                try:
                    import httpx
                    from config import LMSTUDIO_URL, VLLM_API_KEY
                    
                    endpoint = LMSTUDIO_URL.rstrip('/')
                    if not endpoint.endswith('/api'):
                        endpoint = f"{endpoint}/api"
                    
                    # Query model-status to get current_model and health
                    status_url = f"{endpoint}/model-status"
                    
                    response = httpx.get(
                        status_url,
                        headers={"Authorization": f"Bearer {VLLM_API_KEY}"},
                        timeout=2.0
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        # Use currently loaded model from vLLM
                        if data.get("current_model"):
                            model_name = data["current_model"]
                            connection_status = "[green]● Connected[/green]"
                        elif data.get("vllm_healthy"):
                            connection_status = "[yellow]● Loading Model[/yellow]"
                            # Fallback to config if model not loaded yet
                            model_name = VLLM_MODEL if VLLM_MODEL else "Unknown"
                        else:
                            connection_status = "[yellow]● Starting[/yellow]"
                            model_name = VLLM_MODEL if VLLM_MODEL else "Unknown"
                    else:
                        connection_status = "[yellow]● Starting[/yellow]"
                        model_name = VLLM_MODEL if VLLM_MODEL else "Unknown"
                except:
                    connection_status = "[red]● Disconnected[/red]"
                    model_name = VLLM_MODEL if VLLM_MODEL else "Unknown"
            else:
                # When not checking connection, use config as fallback
                model_name = VLLM_MODEL if VLLM_MODEL else "Unknown"
            
            # Update connection status
            status_bar.status_text = f"\n{connection_status}"
            
            # Get RAM info
            mem = psutil.virtual_memory()
            ram_total = mem.total / (1024**3)  # GB
            ram_used = mem.used / (1024**3)
            ram_cached = mem.cached / (1024**3) if hasattr(mem, 'cached') else 0
            
            # Try to get GPU memory
            gpu_info = ""
            try:
                import subprocess
                result = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,noheader,nounits'], 
                                      capture_output=True, text=True, timeout=1)
                if result.returncode == 0:
                    gpu_used, gpu_total = result.stdout.strip().split(',')
                    gpu_info = f" [dim]│[/dim] VRAM: {float(gpu_used)/1024:.1f}/{float(gpu_total)/1024:.1f}GB"
            except:
                pass
            
            status_bar.model_text = f"{model_name} [dim]│[/dim] RAM: {ram_used:.1f}/{ram_total:.1f}GB (cached: {ram_cached:.1f}GB){gpu_info}"
        except:
            pass
    
    def apply_theme_to_css(self):
        theme = get_theme_loader()
        from textual.color import Color
        
        main_bg = theme.get_color("main_bg", "")
        
        # If no main_bg, use hardcoded default (very dark gray with transparency)
        if not main_bg:
            main_bg = "#1a1a1a80"  # Very dark gray with 50% transparency
        
        # Apply backgrounds everywhere
        self.styles.background = main_bg
        
        try:
            header = self.query_one(Header)
            header.styles.background = main_bg
        except:
            pass
        
        try:
            messages_scroll = self.query_one("#messages-scroll")
            messages_scroll.styles.background = main_bg
        except:
            pass
        
        try:
            chat_input = self.query_one("#chat-input")
            chat_input.styles.background = Color.parse(main_bg)
        except:
            pass
        
        # Always update input text color
        try:
            chat_input = self.query_one("#chat-input")
            text_color = theme.get_color("gradient_bottom", "#8a8a8d")
            chat_input.styles.color = Color.parse(text_color)
        except:
            pass
    
    def start_theme_watcher(self):
        watch_dir = Path.home() / '.config/omarchy/current'
        if watch_dir.exists():
            self.theme_observer = Observer()
            event_handler = OmarchyThemeWatcher(self)
            self.theme_observer.schedule(event_handler, str(watch_dir), recursive=True)
            self.theme_observer.start()
    
    def reload_theme_colors(self):
        reload_theme()
        self.apply_theme_to_css()
        
        try:
            self.query_one(StatusBar).refresh()
            
            for border in self.query(ContainerBorder):
                border.refresh()
            for border in self.query(SideBorder):
                border.refresh()
            for button in self.query(KeybindingButton):
                button.refresh()
            for border in self.query(FooterBorder):
                border.refresh()
            for border in self.query(FooterEnd):
                border.refresh()
            for spacer in self.query(FooterSpacer):
                spacer.refresh()
            
            messages_scroll = self.query_one("#messages-scroll", VerticalScroll)
            for widget in messages_scroll.query(ChatMessage):
                widget.refresh()
        except:
            pass
        
        self.notify("Theme updated", severity="information", timeout=2)
    
    async def add_system_message(self, message: str):
        """Add a system message to the chat"""
        messages_scroll = self.query_one("#messages-scroll", VerticalScroll)
        timestamp = datetime.now().strftime("%H:%M:%S")
        system_label = Label(f"[dim]╭──╮ SYSTEM │ {timestamp} ╭────────────────────────────────────╮\n│ {message}\n╰───────────────────────────────────────────────────────────╯[/dim]", classes="system-msg")
        await messages_scroll.mount(system_label, before=0)  # Add at top
        messages_scroll.scroll_home(animate=False)  # Scroll to top
    
    async def add_message(self, role: str, content: str):
        """Add a message to the chat - adds at bottom, pushing older messages up"""
        messages_scroll = self.query_one("#messages-scroll", VerticalScroll)
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        msg = ChatMessage(role, content, timestamp)
        await messages_scroll.mount(msg)  # Add at bottom
        messages_scroll.scroll_end(animate=False)  # Keep scrolled to bottom (latest)
        
        # Refresh all messages to update gradient colors
        for message in messages_scroll.query(ChatMessage):
            message.refresh()
    
    def clear_system_messages(self):
        """Clear all system messages from the chat"""
        messages_scroll = self.query_one("#messages-scroll", VerticalScroll)
        for widget in messages_scroll.query(".system-msg"):
            widget.remove()
    
    @work(exclusive=True)
    async def send_message(self, message: str):
        """Send a message to the LLM"""
        if not message.strip():
            return
        
        self.is_processing = True
        
        # Clear system messages on first user message
        self.clear_system_messages()
        
        try:
            # Update status
            status_bar = self.query_one("#status-bar", StatusBar)
            status_bar.status_text = "\n[yellow]● Processing...[/yellow]"
            
            # Log current settings
            from settings import get_settings
            settings = get_settings()
            temp = settings.get("temperature", 0.7)
            self.log(f"[bold cyan]Using temperature: {temp}[/bold cyan]")
            
            # Add user message
            await self.add_message("user", message)
            
            # Get AI response
            response = await self.llm_client.get_response(message)
            
            # Add AI response
            await self.add_message("assistant", response)
            
            # Update status - check connection after successful message
            self.update_status_bar_right(check_connection=True)
            
        except Exception as e:
            await self.add_system_message(f"Error: {str(e)}")
            status_bar = self.query_one("#status-bar", StatusBar)
            status_bar.status_text = f"\n[red]● Error[/red] {str(e)}"
        
        finally:
            self.is_processing = False
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in chat input"""
        if event.input.id == "chat-input":
            message = event.input.value
            event.input.value = ""
            self.send_message(message)
    
    def action_clear_chat(self) -> None:
        """Clear all chat messages"""
        try:
            messages_scroll = self.query_one("#messages-scroll", VerticalScroll)
            messages_scroll.remove_children()
            self.llm_client.clear_history()
            self.call_later(self.add_system_message, "Chat cleared.")
        except Exception as e:
            self.log(f"Error clearing chat: {e}")
    
    def action_reconnect(self) -> None:
        """Reconnect to LLM"""
        try:
            self.llm_client = LLMClient()
            self.call_later(self.add_system_message, "Reconnected to LLM endpoint.")
        except Exception as e:
            self.log(f"Error reconnecting: {e}")
    
    def action_settings(self) -> None:
        """Open settings modal"""
        def handle_theme_change(theme_name):
            if theme_name:
                self.switch_theme(theme_name)
            # Reconnect to apply any endpoint changes
            self.action_reconnect()
            
            # Update status immediately after model switch
            try:
                status_bar = self.query_one("#status-bar", StatusBar)
                status_bar.status_text = "\n[yellow]● Loading Model[/yellow]"
                
                # Refresh status bar to show updated model (check connection)
                self.update_status_bar_right(check_connection=True)
            except Exception:
                # Status bar not mounted yet, skip update
                pass
        
        self.push_screen(SettingsModal(self.current_theme), handle_theme_change)
    
    def switch_theme(self, theme_name: str) -> None:
        """Switch to a different theme"""
        self.current_theme = theme_name
        if theme_name == "system":
            self.theme_watcher_enabled = True
            if not self.theme_observer:
                self.start_theme_watcher()
        else:
            # Disable watcher for custom themes
            self.theme_watcher_enabled = False
            if self.theme_observer:
                self.theme_observer.stop()
                self.theme_observer = None
        
        # Force reload the theme module to clear cache
        import sys
        if 'theme_loader' in sys.modules:
            del sys.modules['theme_loader']
        from theme_loader import get_theme_loader as get_loader_fresh
        
        # Load the new theme directly
        theme_loader = get_loader_fresh()
        theme_loader.load_theme(theme_name)
        
        # Apply and refresh everything (without calling reload_theme again)
        self.apply_theme_to_css()
        
        # Refresh all widgets manually
        try:
            self.query_one(StatusBar).refresh()
            
            for border in self.query(ContainerBorder):
                border.refresh()
            for border in self.query(SideBorder):
                border.refresh()
            for button in self.query(KeybindingButton):
                button.refresh()
            for border in self.query(FooterBorder):
                border.refresh()
            for border in self.query(FooterEnd):
                border.refresh()
            for spacer in self.query(FooterSpacer):
                spacer.refresh()
            
            messages_scroll = self.query_one("#messages-scroll", VerticalScroll)
            for widget in messages_scroll.query(ChatMessage):
                widget.refresh()
        except:
            pass
        
        # Notify user
        theme_display = "Omarchy Theme" if theme_name == "system" else theme_name
        self.notify(f"Theme changed to: {theme_display}", severity="information", timeout=2)
    
    def action_quit(self) -> None:
        """Quit the application"""
        # Stop theme watcher
        if self.theme_observer:
            self.theme_observer.stop()
            self.theme_observer.join()
        self.exit()


if __name__ == "__main__":
    app = TuivLLM()
    app.run()