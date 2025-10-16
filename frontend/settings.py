"""Settings management for Talk-Tuah"""

import json
from pathlib import Path
from typing import Any, Dict


class Settings:
    """Manage application settings"""
    
    def __init__(self):
        self.settings_file = Path.home() / ".config" / "tuivllm" / "settings.json"
        self.settings: Dict[str, Any] = self.load()
    
    def load(self) -> Dict[str, Any]:
        """Load settings from file"""
        defaults = {
            "temperature": 0.7,
            "max_tokens": 500,
            "gpu_memory_utilization": 0.75,
            "show_timestamps": True,
            "auto_scroll": True,
            "show_memory_stats": True,
            "endpoint": "http://localhost:8787/api",
            "selected_model": None,  # None means use default from config
        }
        
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults (in case new settings were added)
                    return {**defaults, **loaded}
            except:
                return defaults
        
        return defaults
    
    def save(self):
        """Save settings to file"""
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value"""
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set a setting value"""
        self.settings[key] = value
        self.save()


# Global settings instance
_settings = None

def get_settings() -> Settings:
    """Get the global settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
