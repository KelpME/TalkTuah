"""Settings-related widgets"""

from .settings_modal import SettingsModal
from .temperature_slider import TemperatureSlider, TemperatureChanged
from .gpu_memory_slider import GPUMemorySlider, GPUMemoryChanged
from .endpoint_widget import EndpointLine
from .download_manager import DownloadManager
from .model_manager import ModelManager, ModelDownloadRequested

__all__ = [
    "SettingsModal",
    "TemperatureSlider",
    "TemperatureChanged",
    "GPUMemorySlider",
    "GPUMemoryChanged",
    "EndpointLine",
    "DownloadManager",
    "ModelManager",
    "ModelDownloadRequested",
]
