#!/usr/bin/env python3
"""Test temperature settings"""

import sys
sys.path.insert(0, 'frontend')

from settings import get_settings

settings = get_settings()
temp = settings.get("temperature", 0.7)

print(f"Current temperature setting: {temp}")
print(f"Settings file location: {settings.settings_file}")
print(f"Settings file exists: {settings.settings_file.exists()}")

if settings.settings_file.exists():
    with open(settings.settings_file, 'r') as f:
        print(f"\nSettings file contents:")
        print(f.read())
else:
    print("\nSettings file does not exist yet. Run TUI and change temperature to create it.")
