"""Run-key probe for the gamepad starter (pygame-free; safe in JoypadStarter.exe)."""

from __future__ import annotations

import sys

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_VALUE_NAME = "JoypadLauncherGamepadStarter"


def is_gamepad_starter_autostart_registered() -> bool:
    if sys.platform != "win32":
        return False
    try:
        import winreg

        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, _VALUE_NAME)
        winreg.CloseKey(key)
        return True
    except OSError:
        return False
