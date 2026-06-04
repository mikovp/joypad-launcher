"""Find game processes by exe name, directory, or window title."""

import os
from ctypes import WINFUNCTYPE, byref, c_int, c_void_p, c_wchar, sizeof, windll
from ctypes.wintypes import DWORD

from joypad.input.watch.win32.process import enum_process_ids, process_image_path
from joypad.input.watch.win32.types import PROCESSENTRY32

TH32CS_SNAPPROCESS = 0x00000002
INVALID_HANDLE_VALUE = 0xFFFFFFFF


def find_pids_by_exe_stem(stem, exact_name=None):
    """Find processes by exe name stem (e.g. duckov matches Duckov-Win64-Shipping.exe)."""
    stem = (stem or "").lower()
    exact_name = (exact_name or "").lower()
    if not stem and not exact_name:
        return set()
    try:
        kernel32 = windll.kernel32
        snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if snap in (None, INVALID_HANDLE_VALUE):
            return set()
        found = set()
        try:
            pe = PROCESSENTRY32()
            pe.dwSize = sizeof(PROCESSENTRY32)
            if kernel32.Process32First(snap, byref(pe)):
                while True:
                    name = bytes(pe.szExeFile).split(b"\0", 1)[0].decode("latin-1", "ignore").lower()
                    if exact_name and name == exact_name:
                        found.add(pe.th32ProcessID)
                    elif len(stem) >= 4 and stem in name:
                        found.add(pe.th32ProcessID)
                    if not kernel32.Process32Next(snap, byref(pe)):
                        break
        finally:
            kernel32.CloseHandle(snap)
        return found
    except Exception:
        return set()


def find_pids_by_exe_name(exe_name):
    exe_name = (exe_name or "").lower()
    if not exe_name:
        return set()
    stem = os.path.splitext(exe_name)[0]
    return find_pids_by_exe_stem(stem, exe_name)


def find_pids_in_directory(game_dir, exe_hint=None):
    game_dir = os.path.normcase(os.path.abspath(game_dir or ""))
    found = set()
    if exe_hint:
        found |= find_pids_by_exe_name(exe_hint)
    if not game_dir or not os.path.isdir(game_dir):
        return found
    prefix = game_dir + os.sep
    try:
        for pid in enum_process_ids():
            path = process_image_path(pid)
            if path and path.startswith(prefix):
                found.add(pid)
    except Exception:
        pass
    return found


def find_pids_by_window_substring(text):
    """Fallback: match visible window titles (Unity/Epic games may use different exe names)."""
    needle = (text or "").lower()
    if len(needle) < 4:
        return set()
    found = set()

    def _callback(hwnd, _):
        if not windll.user32.IsWindowVisible(hwnd):
            return True
        length = windll.user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        buf = (c_wchar * (length + 1))()
        windll.user32.GetWindowTextW(hwnd, buf, length + 1)
        title = (buf.value or "").lower()
        if needle in title:
            pid = DWORD()
            windll.user32.GetWindowThreadProcessId(hwnd, byref(pid))
            if pid.value:
                found.add(int(pid.value))
        return True

    WNDENUMPROC = WINFUNCTYPE(c_int, c_void_p, c_void_p)
    try:
        windll.user32.EnumWindows(WNDENUMPROC(_callback), 0)
    except Exception:
        pass
    return found
