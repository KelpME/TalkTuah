"""TuivLLM Widget Components - Organized by category"""

# Chat widgets
from .chat import ChatMessage

# Layout widgets (borders, footer, status bar)
from .layout import (
    ContainerBorder, SideBorder,
    CustomFooter, KeybindingButton, FooterBorder, FooterEnd, FooterSpacer,
    StatusBar
)

# Settings (modal and all settings widgets)
from .settings import (
    SettingsModal,
    TemperatureSlider, TemperatureChanged,
    ModelManager, ModelDownloadRequested
)

__all__ = [
    # Chat
    "ChatMessage",
    # Layout
    "ContainerBorder",
    "SideBorder",
    "StatusBar",
    "CustomFooter",
    "KeybindingButton",
    "FooterBorder",
    "FooterEnd",
    "FooterSpacer",
    # Settings
    "SettingsModal",
    "ModelManager",
    "ModelDownloadRequested",
    "TemperatureSlider",
    "TemperatureChanged",
]
