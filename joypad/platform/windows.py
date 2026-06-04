"""Windows-only OS integration: registry, window focus, process trees.

The ONLY module permitted to touch ctypes / winreg / win32 APIs. Keep all
ctypes imports lazy (inside functions) so the package imports on non-Windows
dev boxes, matching the original launcher.py behavior.
"""

import os
import subprocess
import sys
import time

import pygame


def _get_steam_path_from_registry():
    """Steam path from Windows registry (HKLM and HKCU)."""
    if sys.platform != "win32":
        return None
    try:
        import winreg
        roots_and_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Valve\Steam"),
        ]
        for root, key_path in roots_and_paths:
            try:
                key = winreg.OpenKey(root, key_path, 0, winreg.KEY_READ)
                install_dir, _ = winreg.QueryValueEx(key, "InstallPath")
                winreg.CloseKey(key)
                if install_dir and os.path.isdir(install_dir):
                    exe = os.path.join(install_dir, "steam.exe")
                    if os.path.isfile(exe):
                        return exe
            except (OSError, FileNotFoundError):
                continue
    except Exception:
        pass
    return None


def get_steam_path(config):
    """Steam.exe path: config -> default folders -> Windows registry."""
    path = (config.get("steam_path") or "").strip()
    if path:
        path = os.path.normpath(path)
        if os.path.isfile(path):
            return path
    defaults = [
        os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), "Steam", "steam.exe"),
        os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Steam", "steam.exe"),
    ]
    for p in defaults:
        if p and os.path.isfile(p):
            return p
    return _get_steam_path_from_registry()


def _send_launcher_to_back(hwnd):
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


def _get_process_and_descendant_pids(pid):
    """Returns [pid] + all child PIDs recursively (Windows, Toolhelp32)."""
    if not pid or sys.platform != "win32":
        return [pid] if pid else []
    try:
        from ctypes import windll, byref, Structure, c_ulong, c_char, sizeof
        from ctypes.wintypes import DWORD
        kernel32 = windll.kernel32
        TH32CS_SNAPPROCESS = 0x00000002
        INVALID_HANDLE_VALUE = 0xFFFFFFFF

        class PROCESSENTRY32(Structure):
            _fields_ = [
                ("dwSize", DWORD),
                ("cntUsage", DWORD),
                ("th32ProcessID", DWORD),
                ("th32DefaultHeapID", c_ulong),
                ("th32ModuleID", DWORD),
                ("cntThreads", DWORD),
                ("th32ParentProcessID", DWORD),
                ("pcPriClassBase", c_ulong),
                ("dwFlags", DWORD),
                ("szExeFile", c_char * 260),
            ]
        snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if snap == INVALID_HANDLE_VALUE or snap is None:
            return [pid]
        parent_to_children = {}
        try:
            pe = PROCESSENTRY32()
            pe.dwSize = sizeof(PROCESSENTRY32)
            if not kernel32.Process32First(snap, byref(pe)):
                return [pid]
            while True:
                parent_to_children.setdefault(pe.th32ParentProcessID, []).append(pe.th32ProcessID)
                if not kernel32.Process32Next(snap, byref(pe)):
                    break
        finally:
            kernel32.CloseHandle(snap)
        result = [pid]
        to_visit = [pid]
        while to_visit:
            p = to_visit.pop()
            for child in parent_to_children.get(p, []):
                if child not in result:
                    result.append(child)
                    to_visit.append(child)
        return result
    except Exception:
        return [pid] if pid else []


def _bring_process_window_to_foreground(pid):
    """Finds process main window by PID and switches focus to it (Windows)."""
    if not pid or sys.platform != "win32":
        return
    try:
        from ctypes import windll, byref, c_ulong, c_bool, c_void_p, WINFUNCTYPE
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


def _bring_game_to_foreground(process, attempts=12):
    """Switches focus to process window or its child processes.
    attempts: number of tries (12 ~ 6s for Epic, 20 ~ 10s for Steam).
    """
    if not process or sys.platform != "win32":
        return
    seen_pids = set()
    for _ in range(attempts):
        pids = _get_process_and_descendant_pids(process.pid)
        for pid in pids:
            seen_pids.add(pid)
            _bring_process_window_to_foreground(pid)
        pygame.event.pump()
        time.sleep(0.5)


def _bring_any_other_window_to_foreground(skip_hwnd):
    """Switches focus to first other visible window with title (for Steam — game window)."""
    if not skip_hwnd or sys.platform != "win32":
        return
    try:
        from ctypes import windll, byref, c_ulong, c_bool, c_void_p, WINFUNCTYPE, create_unicode_buffer
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


def _bring_launcher_to_front(hwnd):
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


def _yield_for_game_window(seconds=2.0):
    """Gives game time to create window and get focus (event processing + pause)."""
    steps = max(1, int(seconds * 10))
    for _ in range(steps):
        pygame.event.pump()
        time.sleep(seconds / steps)


def _wait_for_game_and_restore(process, hwnd, platform=None, watch_exe=None, watch_dir=None, remap_proc=None):
    """Waits for game process to finish, then brings launcher to foreground.

    For Epic we wait until the game exe is fully gone (survives in-game restart).
    When a remap worker is running, the launcher follows the worker lifetime instead
    (the worker tracks the session with gamepad activity + process watch).
    For Steam we wait until Steam process has no child processes (game exited),
    so we do not hang while Steam client is open.
    """
    if not process:
        return

    if platform == "steam" and sys.platform == "win32":
        # Wait until steam.exe has no child processes (games),
        # so we do not hang while Steam client is open.
        while process.poll() is None:
            pygame.event.pump()
            try:
                pids = _get_process_and_descendant_pids(process.pid)
            except Exception:
                pids = [process.pid]
            child_pids = [p for p in pids if p != process.pid]
            if not child_pids:
                break
            time.sleep(0.5)
    elif remap_proc and sys.platform == "win32":
        while remap_proc.poll() is None:
            pygame.event.pump()
            time.sleep(0.5)
    elif platform == "epic" and (watch_exe or watch_dir) and sys.platform == "win32":
        from joypad.input.engine import wait_for_game_exe_exit

        wait_for_game_exe_exit(
            watch_exe,
            root_pid=process.pid,
            watch_dir=watch_dir,
            pump=lambda: pygame.event.pump(),
        )
    else:
        # Normal process wait (Epic without exe hint, NSP, etc.)
        while process.poll() is None:
            pygame.event.pump()
            time.sleep(0.5)

    _bring_launcher_to_front(hwnd)


def _show_error_message(message):
    """Show error dialog (Windows) for visibility when running exe without console."""
    if sys.platform == "win32":
        try:
            from ctypes import windll
            windll.user32.MessageBoxW(0, message, "Joypad Launcher — Error", 0x10)
        except Exception:
            pass
