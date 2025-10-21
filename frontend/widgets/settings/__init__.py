"""Settings-related widgets"""

from .settings_modal import SettingsModal
from .sliders import (
    TemperatureSlider, TemperatureChanged,
    MaxTokensSlider, MaxTokensChanged,
    GPUMemorySlider, GPUMemoryChanged
)
from .endpoint_widget import EndpointLine
from .download_manager import DownloadManager
from .model_manager import ModelManager, ModelDownloadRequested
from .model_option import ModelDeleteRequested

__all__ = [
    "SettingsModal",
    "TemperatureSlider",
    "TemperatureChanged",
    "MaxTokensSlider",
    "MaxTokensChanged",
    "GPUMemorySlider",
    "GPUMemoryChanged",
    "EndpointLine",
    "DownloadManager",
    "ModelManager",
    "ModelDownloadRequested",
    "ModelDeleteRequested",
]
