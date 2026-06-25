"""Launcher executable argv for starter and Windows autostart."""

from __future__ import annotations

import os
import subprocess
import sys

from joypad.cli import GAMEPAD_STARTER_FLAG
from joypad.paths import _BASE_DIR

STARTER_PID_FILE = "gamepad_starter.pid"
LAUNCHER_EXE_NAME = "JoypadLauncher.exe"
STARTER_EXE_NAME = "JoypadStarter.exe"
STARTER_DIR_NAME = "JoypadStarter"


def launcher_exe_path() -> str:
    return os.path.join(_BASE_DIR, LAUNCHER_EXE_NAME)


def starter_exe_path() -> str:
    nested = os.path.join(_BASE_DIR, STARTER_DIR_NAME, STARTER_EXE_NAME)
    if os.path.isfile(nested):
        return nested
    return os.path.join(_BASE_DIR, STARTER_EXE_NAME)


def _python_for_starter() -> str:
    exe = sys.executable
    if exe.lower().endswith("python.exe"):
        pythonw = exe[:-10] + "pythonw.exe"
        if os.path.isfile(pythonw):
            return pythonw
    return exe


def launcher_command() -> list[str]:
    if getattr(sys, "frozen", False):
        return [launcher_exe_path()]
    launcher_py = os.path.join(_BASE_DIR, "launcher.py")
    return [sys.executable, launcher_py]


def gamepad_starter_command() -> list[str]:
    if getattr(sys, "frozen", False):
        return [starter_exe_path()]
    launcher_py = os.path.join(_BASE_DIR, "launcher.py")
    return [_python_for_starter(), launcher_py, GAMEPAD_STARTER_FLAG]


def format_gamepad_starter_command() -> str:
    return subprocess.list2cmdline(gamepad_starter_command())


def starter_pid_path() -> str:
    return os.path.join(_BASE_DIR, STARTER_PID_FILE)
