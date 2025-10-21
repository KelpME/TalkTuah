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
from utils import LLMClient
from config import LMSTUDIO_URL, VLLM_MODEL

import sys
if 'utils.theme' in sys.modules:
    del sys.modules['utils.theme']
from utils import get_theme_loader, reload_theme

from widgets import ChatMessage, ContainerBorder, SideBorder, StatusBar, CustomFooter, KeybindingButton, FooterBorder, FooterEnd, FooterSpacer, SettingsModal, DownloadProgressBar
from widgets.settings.model_option import ModelSelected
from widgets.settings.download_started import DownloadStarted
from textual.containers import Horizontal as HorizontalContainer


class OmarchyThemeWatcher(FileSystemEventHandler):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.last_reload = 0
        import time
        self.time = time
    
    def _should_reload(self):
        """Debounce rapid file changes"""
        import time
        now = time.time()
        if now - self.last_reload < 0.5:  # Debounce 500ms
            return False
        self.last_reload = now
        return True
    
    def on_modified(self, event):
        if self.app.theme_watcher_enabled and ('theme' in event.src_path or 'btop.theme' in event.src_path):
            if self._should_reload():
                self.app.log(f"[Theme] Reloading theme from {event.src_path}")
                self.app.call_from_thread(self.app.reload_theme_colors)
    
    def on_created(self, event):
        if self.app.theme_watcher_enabled and ('theme' in event.src_path or Path(event.src_path).name == 'theme'):
            if self._should_reload():
                self.app.log(f"[Theme] Loading new theme from {event.src_path}")
                self.app.call_from_thread(self.app.reload_theme_colors)
    
    def on_moved(self, event):
        if self.app.theme_watcher_enabled and hasattr(event, 'dest_path'):
            if 'theme' in event.dest_path:
                if self._should_reload():
                    self.app.log(f"[Theme] Reloading theme from {event.dest_path}")
                    self.app.call_from_thread(self.app.reload_theme_colors)
    
    def on_deleted(self, event):
        """Handle theme deletion (symlink recreation triggers create after this)"""
        # Silently ignore delete events - theme recreation will trigger create event


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
        ("ctrl+t", "reload_theme", "Reload Theme"),
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
        self.download_poll_timer = None
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Container(id="main-box"):
            yield ContainerBorder("STATUS", color_key="user_color", position="top", border_type="corner")
            yield StatusBar(id="status-bar")
            yield DownloadProgressBar(id="download-progress")
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
    
    def start_status_polling(self):
        """Start polling status bar every second (e.g., during model loading)"""
        # Stop existing timer if any
        if self.status_update_timer:
            self.status_update_timer.stop()
        
        # Start new timer - update every 1 second
        self.status_update_timer = self.set_interval(1.0, self.poll_status_bar)
        self.log("Started status bar polling (1s intervals)")
    
    def poll_status_bar(self):
        """Poll status bar and stop when model is fully loaded"""
        self.update_status_bar_right(check_connection=True)
        
        # Check if model is loaded
        try:
            status_bar = self.query_one("#status-bar", StatusBar)
            # If status shows "Connected", model is loaded - stop polling
            if "[green]● Connected[/green]" in status_bar.status_text:
                self.stop_status_polling()
        except:
            pass
    
    def stop_status_polling(self):
        """Stop status bar polling"""
        if self.status_update_timer:
            self.status_update_timer.stop()
            self.status_update_timer = None
            self.log("Stopped status bar polling")
    
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
        # Watch both the symlink directory and the theme subdirectory
        watch_dirs = [
            Path.home() / '.config/omarchy/current',  # For theme symlink changes
            Path.home() / '.config/omarchy/current/theme',  # For theme file changes
        ]
        
        self.theme_observer = Observer()
        event_handler = OmarchyThemeWatcher(self)
        
        for watch_dir in watch_dirs:
            if watch_dir.exists():
                self.theme_observer.schedule(event_handler, str(watch_dir), recursive=True)
                self.log(f"Watching theme directory: {watch_dir}")
        
        self.theme_observer.start()
    
    def reload_theme_colors(self):
        self.log("Reloading theme colors...")
        reload_theme()
        self.apply_theme_to_css()
        self.log("Theme CSS applied")
        
        try:
            # Refresh status bar and progress bar with layout update
            status = self.query_one(StatusBar)
            status.refresh(repaint=True, layout=True)
            try:
                progress = self.query_one(DownloadProgressBar)
                progress.refresh(repaint=True, layout=True)
            except:
                pass
            
            # Refresh all border components with repaint
            for border in self.query(ContainerBorder):
                border.refresh(repaint=True)
            for border in self.query(SideBorder):
                border.refresh(repaint=True)
            for border in self.query(FooterBorder):
                border.refresh(repaint=True)
            for border in self.query(FooterEnd):
                border.refresh(repaint=True)
            for spacer in self.query(FooterSpacer):
                spacer.refresh(repaint=True)
            
            # Refresh footer buttons
            for button in self.query(KeybindingButton):
                button.refresh(repaint=True)
            try:
                self.query_one(CustomFooter).refresh(repaint=True)
            except:
                pass
            
            # Refresh chat messages
            messages_scroll = self.query_one("#messages-scroll", VerticalScroll)
            for widget in messages_scroll.query(ChatMessage):
                widget.refresh(repaint=True)
            
            # Refresh settings modal if open
            try:
                modal = self.query_one(SettingsModal)
                modal.refresh(repaint=True, layout=True)
                # Refresh all child widgets in modal
                for widget in modal.query("*"):
                    try:
                        widget.refresh()
                    except:
                        pass
            except:
                pass
                
        except Exception as e:
            self.log(f"Error refreshing widgets: {e}")
        
        # Force full screen refresh
        try:
            self.refresh(repaint=True, layout=True)
        except Exception as e:
            self.log(f"Error refreshing app: {e}")
        
        self.log("Theme reload complete")
        self.notify("Theme updated", severity="information", timeout=2)
    
    async def add_system_message(self, message: str):
        """Add a system message to the chat"""
        try:
            messages_scroll = self.query_one("#messages-scroll", VerticalScroll)
            timestamp = datetime.now().strftime("%H:%M:%S")
            system_label = Label(f"[dim]╭──╮ SYSTEM │ {timestamp} ╭────────────────────────────────────╮\n│ {message}\n╰───────────────────────────────────────────────────────────╯[/dim]", classes="system-msg")
            await messages_scroll.mount(system_label, before=0)  # Add at top
            messages_scroll.scroll_home(animate=False)  # Scroll to top
        except Exception as e:
            self.log(f"Error adding system message: {e}")
    
    async def add_message(self, role: str, content: str):
        """Add a message to the chat - adds at bottom, pushing older messages up"""
        try:
            messages_scroll = self.query_one("#messages-scroll", VerticalScroll)
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            msg = ChatMessage(role, content, timestamp)
            await messages_scroll.mount(msg)  # Add at bottom
            messages_scroll.scroll_end(animate=False)  # Keep scrolled to bottom (latest)
            
            # Refresh all messages to update gradient colors
            for message in messages_scroll.query(ChatMessage):
                message.refresh()
        except Exception as e:
            self.log(f"Error adding message: {e}")
    
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
            from user_preferences import get_settings
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
            self.notify("Reconnected to LLM", severity="information")
            self.update_status_bar_right(check_connection=True)
        except Exception as e:
            self.notify(f"Reconnection failed: {str(e)}", severity="error")
    
    def action_reload_theme(self) -> None:
        """Manually reload theme from Omarchy"""
        self.log("Manual theme reload triggered via Ctrl+T")
        self.reload_theme_colors()
    
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
    
    def on_download_started(self, message: DownloadStarted) -> None:
        """Handle download started - begin polling for progress"""
        self.log(f"DownloadStarted message received for: {message.model_id}")
        
        # Initialize progress bar with downloading state immediately
        try:
            progress_bar = self.query_one("#download-progress", DownloadProgressBar)
            progress_bar.status = "downloading"
            progress_bar.model_name = message.model_id
            progress_bar.progress = 0
            progress_bar.refresh()
            self.log("Progress bar initialized and refreshed")
        except Exception as e:
            self.log(f"Failed to initialize progress bar: {e}")
        
        # Start polling download progress every 2 seconds
        if self.download_poll_timer:
            self.download_poll_timer.stop()
        
        self.download_poll_timer = self.set_interval(2.0, self.poll_download_progress)
        self.notify(f"Download tracking started: {message.model_id}", severity="information", timeout=3)
    
    async def poll_download_progress(self) -> None:
        """Poll download progress and update progress bar"""
        try:
            progress_bar = self.query_one("#download-progress", DownloadProgressBar)
            should_continue = await progress_bar.poll_progress()
            
            # Stop polling if download is complete or failed
            if not should_continue and self.download_poll_timer:
                self.download_poll_timer.stop()
                self.download_poll_timer = None
        except Exception as e:
            self.log(f"Download progress poll error: {e}")
    
    async def on_model_selected(self, message: ModelSelected) -> None:
        """Handle model selected from download progress bar (load button)"""
        # Same as switching from settings - trigger model switch
        from user_preferences import get_settings
        from config import LMSTUDIO_URL
        from widgets.settings import api_client
        
        settings = get_settings()
        settings.set("selected_model", message.model_name)
        
        # Reset progress bar immediately
        try:
            progress_bar = self.query_one("#download-progress", DownloadProgressBar)
            progress_bar.reset()
        except:
            pass
        
        # Call API to switch model
        try:
            endpoint = settings.get("endpoint", LMSTUDIO_URL)
            self.notify(f"Switching to {message.model_name}...", severity="information", timeout=2)
            
            data = await api_client.switch_model(message.model_name, endpoint)
            self.notify(
                f"✓ {data.get('message')}\n{data.get('info')}",
                severity="information",
                timeout=10
            )
            
            # Start polling status bar to show loading progress
            self.start_status_polling()
                
        except Exception as e:
            self.notify(f"Error switching model: {str(e)}", severity="error", timeout=5)
    
    def action_quit(self) -> None:
        """Quit the application"""
        # Stop timers
        if self.download_poll_timer:
            self.download_poll_timer.stop()
        if self.status_update_timer:
            self.status_update_timer.stop()
        
        # Stop theme watcher
        if self.theme_observer:
            self.theme_observer.stop()
            self.theme_observer.join()
        self.exit()


if __name__ == "__main__":
    app = TuivLLM()
    app.run()