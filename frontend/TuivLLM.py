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

from widgets import ChatMessage, ContainerBorder, SideBorder, StatusBar, CustomFooter, KeybindingButton, FooterBorder, FooterEnd, FooterSpacer
from textual.containers import Horizontal as HorizontalContainer


class OmarchyThemeWatcher(FileSystemEventHandler):
    def __init__(self, app):
        super().__init__()
        self.app = app
    
    def on_modified(self, event):
        if 'theme' in event.src_path or 'btop.theme' in event.src_path:
            self.app.call_from_thread(self.app.reload_theme_colors)
    
    def on_created(self, event):
        if Path(event.src_path).name == 'theme':
            self.app.call_from_thread(self.app.reload_theme_colors)
    
    def on_moved(self, event):
        if hasattr(event, 'dest_path') and Path(event.dest_path).name == 'theme':
            self.app.call_from_thread(self.app.reload_theme_colors)


class TuivLLM(App):
    """BTOP++ styled TUI chatbot interface"""
    
    CSS = """
    Screen {
        background: transparent;
    }
    
    Header {
        dock: top;
        height: 1;
    }
    
    #main-box {
        width: 100%;
        height: 1fr;
        padding: 0;
        margin: 0;
    }
    
    #status-bar {
        height: 1;
        width: 100%;
    }
    
    #conversation-box {
        width: 100%;
        height: 1fr;
        layout: horizontal;
    }
    
    SideBorder {
        width: 1;
        height: 100%;
    }
    
    #conversation-content {
        width: 1fr;
        height: 100%;
    }
    
    #messages-scroll {
        width: 100%;
        height: 1fr;
        padding: 0 2;
        scrollbar-size: 0 0;
        align: left bottom;
    }
    
    ContainerBorder {
        width: 100%;
        height: 1;
    }
    
    ChatMessage {
        width: 100%;
        height: auto;
        padding: 0;
        margin-bottom: 1;
    }
    
    #chat-input {
        width: 100%;
        height: 4;
        border: none;
        padding: 0 1;
        color: $success;
    }
    
    CustomFooter {
        height: 1;
        width: 100%;
        layout: horizontal;
    }
    
    FooterBorder {
        width: auto;
        height: 1;
    }
    
    FooterEnd {
        width: 1fr;
        height: 1;
    }
    
    KeybindingButton {
        width: auto;
        height: 1;
    }
    
    FooterSpacer {
        width: auto;
        height: 1;
    }
    
    .system-msg {
        color: $warning;
        text-style: italic;
        padding: 0 1;
        margin-bottom: 1;
    }
    """
    
    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+l", "clear_chat", "Clear"),
        ("ctrl+r", "reconnect", "Reconnect"),
    ]
    
    messages: reactive[List[Dict]] = reactive([])
    
    def __init__(self):
        super().__init__()
        self.llm_client = LLMClient()
        self.is_processing = False
        self.theme_observer = None
    
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
        status_bar.status_text = f"[green]● Connected[/green] [dim]│[/dim] Endpoint: {LMSTUDIO_URL}"
        
        # Update model and memory info
        self.update_status_bar_right()
        
        self.start_theme_watcher()
        self.set_interval(0.1, self.refresh_gradient)
        self.set_interval(2.0, self.update_status_bar_right)
        
        # Focus input field
        self.query_one("#chat-input", Input).focus()
    
    def refresh_gradient(self):
        try:
            messages_scroll = self.query_one("#messages-scroll", VerticalScroll)
            for message in messages_scroll.query(ChatMessage):
                message.refresh()
        except:
            pass
    
    def update_status_bar_right(self):
        """Update model and memory info on status bar"""
        try:
            status_bar = self.query_one("#status-bar", StatusBar)
            model_name = VLLM_MODEL.split('/')[-1] if '/' in VLLM_MODEL else VLLM_MODEL
            
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
        if not message.strip() or self.is_processing:
            return
        
        self.is_processing = True
        
        # Clear system messages on first user message
        self.clear_system_messages()
        
        try:
            # Update status
            status_bar = self.query_one("#status-bar", StatusBar)
            status_bar.status_text = "[yellow]● Processing...[/yellow]"
            
            # Add user message
            await self.add_message("user", message)
            
            # Get AI response
            response = await self.llm_client.get_response(message)
            
            # Add AI response
            await self.add_message("assistant", response)
            
            # Update status
            status_bar.status_text = f"[green]● Connected[/green] [dim]│[/dim] Endpoint: {LMSTUDIO_URL}"
            
        except Exception as e:
            await self.add_system_message(f"Error: {str(e)}")
            status_bar = self.query_one("#status-bar", StatusBar)
            status_bar.status_text = f"[red]● Error[/red] [dim]│[/dim] {str(e)}"
        
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