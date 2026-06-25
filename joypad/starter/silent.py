"""Keep the gamepad starter invisible and low priority."""

from __future__ import annotations

import sys

_IDLE_PRIORITY_CLASS = 0x40


def apply_low_power_starter() -> None:
    if sys.platform != "win32":
        return
    import ctypes

    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32
    console = kernel32.GetConsoleWindow()
    if console:
        user32.ShowWindow(console, 0)
    kernel32.SetPriorityClass(kernel32.GetCurrentProcess(), _IDLE_PRIORITY_CLASS)
