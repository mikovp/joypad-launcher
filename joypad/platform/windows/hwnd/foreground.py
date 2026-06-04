"""Bring process windows to foreground."""

import sys

from joypad.platform.windows.hwnd.timed_pump import timed_pump
from joypad.platform.windows.process import get_process_and_descendant_pids


def bring_process_window_to_foreground(pid):
    """Finds process main window by PID and switches focus to it (Windows)."""
    if not pid or sys.platform != "win32":
        return
    try:
        from ctypes import WINFUNCTYPE, byref, c_bool, c_ulong, c_void_p, windll
        found_hwnd = [None]

        def enum_callback(hwnd, _lparam):
            if not windll.user32.IsWindowVisible(hwnd):
                return True
            proc_id = c_ulong()
            windll.user32.GetWindowThreadProcessId(hwnd, byref(proc_id))
            if proc_id.value == pid:
                found_hwnd[0] = hwnd
                return False
            return True

        EnumWindowsProc = WINFUNCTYPE(c_bool, c_void_p, c_void_p)
        windll.user32.EnumWindows(EnumWindowsProc(enum_callback), 0)
        game_hwnd = found_hwnd[0]
        if not game_hwnd:
            return
        SW_RESTORE = 9
        windll.user32.ShowWindow(game_hwnd, SW_RESTORE)
        windll.user32.SetForegroundWindow(game_hwnd)
    except Exception:
        pass


def bring_any_other_window_to_foreground(skip_hwnd):
    """Switches focus to first other visible window with title (for Steam — game window)."""
    if not skip_hwnd or sys.platform != "win32":
        return
    try:
        from ctypes import WINFUNCTYPE, c_bool, c_void_p, create_unicode_buffer, windll
        found_hwnd = [None]

        def enum_callback(hwnd, _lparam):
            if hwnd == skip_hwnd or not windll.user32.IsWindowVisible(hwnd):
                return True
            length = windll.user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True
            buf = create_unicode_buffer(length + 1)
            windll.user32.GetWindowTextW(hwnd, buf, length + 1)
            if buf.value and buf.value.strip():
                found_hwnd[0] = hwnd
                return False
            return True

        EnumWindowsProc = WINFUNCTYPE(c_bool, c_void_p, c_void_p)
        windll.user32.EnumWindows(EnumWindowsProc(enum_callback), 0)
        other_hwnd = found_hwnd[0]
        if other_hwnd:
            SW_RESTORE = 9
            windll.user32.ShowWindow(other_hwnd, SW_RESTORE)
            windll.user32.SetForegroundWindow(other_hwnd)
    except Exception:
        pass


def bring_launcher_to_front(hwnd):
    """Restores window from minimized and brings to foreground (Windows)."""
    if not hwnd or sys.platform != "win32":
        return
    try:
        from ctypes import windll
        SW_RESTORE = 9
        windll.user32.ShowWindow(hwnd, SW_RESTORE)
        windll.user32.SetForegroundWindow(hwnd)
    except Exception:
        pass


def bring_game_to_foreground(process, attempts=12, tick=None):
    """Switches focus to process window or its child processes."""
    if not process or sys.platform != "win32":
        return
    for _ in range(attempts):
        pids = get_process_and_descendant_pids(process.pid)
        for pid in pids:
            bring_process_window_to_foreground(pid)
        timed_pump(0.5, tick=tick)
