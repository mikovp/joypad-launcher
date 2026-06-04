"""Filesystem paths for the launcher (base dir next to launcher.py / the exe)."""

import os
import sys

if getattr(sys, "frozen", False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    # repo root = parent of the joypad/ package directory
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_PATH = os.path.join(_BASE_DIR, "config.json")
CONFIG_EXAMPLE = os.path.join(_BASE_DIR, "config.example.json")
