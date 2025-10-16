#!/usr/bin/env python3
"""Sync TUI settings to .env file"""

import json
import sys
from pathlib import Path


def load_tui_settings():
    """Load settings from TUI config"""
    settings_file = Path.home() / ".config" / "tuivllm" / "settings.json"
    if settings_file.exists():
        with open(settings_file, 'r') as f:
            return json.load(f)
    return {}


def update_env_file(settings):
    """Update .env file with GPU memory setting"""
    env_file = Path(__file__).parent.parent / ".env"
    
    if not env_file.exists():
        print("ERROR: .env file not found. Run: cp .env.example .env")
        sys.exit(1)
    
    # Read existing .env
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Update GPU_MEMORY_UTILIZATION
    gpu_mem = settings.get('gpu_memory_utilization', 0.75)
    updated = False
    
    for i, line in enumerate(lines):
        if line.startswith('GPU_MEMORY_UTILIZATION='):
            lines[i] = f'GPU_MEMORY_UTILIZATION={gpu_mem}\n'
            updated = True
            break
    
    if not updated:
        lines.append(f'GPU_MEMORY_UTILIZATION={gpu_mem}\n')
    
    # Write back
    with open(env_file, 'w') as f:
        f.writelines(lines)
    
    print(f"✓ Updated GPU memory utilization: {int(gpu_mem * 100)}%")


def main():
    settings = load_tui_settings()
    if not settings:
        print("No TUI settings found. Using defaults.")
        return
    
    update_env_file(settings)


if __name__ == "__main__":
    main()
