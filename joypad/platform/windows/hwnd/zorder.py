"""Launcher window z-order and sizing."""

import sys


def send_launcher_to_back(hwnd):
    """Sends launcher window to background (Windows)."""
    if not hwnd or sys.platform != "win32":
        return
    try:
        from ctypes import windll
        HWND_BOTTOM = 1
        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001
        windll.user32.SetWindowPos(hwnd, HWND_BOTTOM, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
    except Exception:
        pass


def resize_launcher_window(hwnd, width, height):
    """Resize borderless launcher window to cover the full screen/work area."""
    if not hwnd or sys.platform != "win32":
        return
    try:
        from ctypes import windll

        SWP_NOZORDER = 0x0004
        windll.user32.SetWindowPos(hwnd, None, 0, 0, width, height, SWP_NOZORDER)
    except Exception:
        pass
