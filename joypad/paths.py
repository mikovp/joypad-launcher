"""Filesystem paths for the launcher (base dir next to launcher.py / the exe)."""

import os
import sys


def _frozen_base_dir() -> str:
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    parent = os.path.dirname(exe_dir)
    if os.path.isfile(os.path.join(parent, "JoypadLauncher.exe")):
        return parent
    if os.path.isfile(os.path.join(exe_dir, "JoypadLauncher.exe")):
        return exe_dir
    return exe_dir


if getattr(sys, "frozen", False):
    _BASE_DIR = _frozen_base_dir()
else:
    # repo root = parent of the joypad/ package directory
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_PATH = os.path.join(_BASE_DIR, "config.json")
CONFIG_EXAMPLE = os.path.join(_BASE_DIR, "config.example.json")
