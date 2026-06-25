"""Launcher window z-order and sizing."""

from __future__ import annotations

import sys


def primary_monitor_rect() -> tuple[int, int, int, int]:
    """Return (x, y, width, height) for the primary monitor (full screen, not work area)."""
    if sys.platform != "win32":
        return 0, 0, 1920, 1080
    try:
        import ctypes
        from ctypes import Structure, byref, wintypes

        class RECT(Structure):
            _fields_ = [
                ("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long),
            ]

        class MONITORINFO(Structure):
            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("rcMonitor", RECT),
                ("rcWork", RECT),
                ("dwFlags", wintypes.DWORD),
            ]

        user32 = ctypes.windll.user32
        monitor = user32.MonitorFromWindow(None, 1)
        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(MONITORINFO)
        if user32.GetMonitorInfoW(monitor, byref(info)):
            rect = info.rcMonitor
            return rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top
        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)
        return 0, 0, width, height
    except Exception:
        return 0, 0, 1920, 1080


def place_launcher_on_monitor(hwnd) -> None:
    """Show the launcher borderless over the full primary monitor."""
    if not hwnd or sys.platform != "win32":
        return
    try:
        from ctypes import windll

        x, y, width, height = primary_monitor_rect()
        SW_SHOW = 5
        HWND_TOP = 0
        SWP_SHOWWINDOW = 0x0040
        user32 = windll.user32
        user32.ShowWindow(hwnd, SW_SHOW)
        user32.SetWindowPos(hwnd, HWND_TOP, x, y, width, height, SWP_SHOWWINDOW)
    except Exception:
        pass


def send_launcher_to_back(hwnd):
    """Send launcher behind other windows while a game runs."""
    if not hwnd or sys.platform != "win32":
        return
    try:
        from ctypes import windll

        HWND_BOTTOM = 1
        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001
        SWP_NOACTIVATE = 0x0010
        windll.user32.SetWindowPos(
            hwnd, HWND_BOTTOM, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
        )
    except Exception:
        pass


def resize_launcher_window(hwnd, width=None, height=None):
    """Resize and position the borderless launcher on the primary monitor."""
    if not hwnd or sys.platform != "win32":
        return
    try:
        from ctypes import windll

        x, y, monitor_w, monitor_h = primary_monitor_rect()
        w = monitor_w if width is None else width
        h = monitor_h if height is None else height
        SWP_NOZORDER = 0x0004
        SWP_SHOWWINDOW = 0x0040
        windll.user32.SetWindowPos(hwnd, None, x, y, w, h, SWP_NOZORDER | SWP_SHOWWINDOW)
    except Exception:
        pass
