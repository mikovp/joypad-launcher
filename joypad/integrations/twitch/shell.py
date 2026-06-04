"""Windows ShellExecute launch for file associations."""

import os
import sys


class ShellExecuteProcess:
    """Minimal process handle from ShellExecuteEx; supports poll()/pid for wait and focus."""

    STILL_ACTIVE = 259

    def __init__(self, h_process):
        self._hp = h_process
        self.pid = None
        try:
            from ctypes import windll

            pid = windll.kernel32.GetProcessId(h_process)
            self.pid = pid if pid else None
        except Exception:
            pass

    def poll(self):
        from ctypes import byref, windll
        from ctypes.wintypes import DWORD

        if not self._hp:
            return 0
        code = DWORD()
        if not windll.kernel32.GetExitCodeProcess(self._hp, byref(code)):
            windll.kernel32.CloseHandle(self._hp)
            self._hp = None
            return None
        if code.value == self.STILL_ACTIVE:
            return None
        windll.kernel32.CloseHandle(self._hp)
        self._hp = None
        return code.value


def shell_execute_open_file(path):
    """Windows: open file with its registered app (same as double-click)."""
    if sys.platform != "win32":
        return None
    try:
        import ctypes
        from ctypes import byref, wintypes

        SEE_MASK_NOCLOSEPROCESS = 0x00000040

        class SHELLEXECUTEINFOW(ctypes.Structure):
            _fields_ = (
                ("cbSize", ctypes.c_uint32),
                ("fMask", ctypes.c_uint32),
                ("hwnd", wintypes.HWND),
                ("lpVerb", wintypes.LPCWSTR),
                ("lpFile", wintypes.LPCWSTR),
                ("lpParameters", wintypes.LPCWSTR),
                ("lpDirectory", wintypes.LPCWSTR),
                ("nShow", ctypes.c_int),
                ("hInstApp", wintypes.HINSTANCE),
                ("lpIDList", ctypes.c_void_p),
                ("lpClass", wintypes.LPCWSTR),
                ("hKeyClass", wintypes.HANDLE),
                ("dwHotKey", ctypes.c_uint32),
                ("hIcon", wintypes.HANDLE),
                ("hProcess", wintypes.HANDLE),
            )

        sei = SHELLEXECUTEINFOW()
        sei.cbSize = ctypes.sizeof(SHELLEXECUTEINFOW)
        sei.fMask = SEE_MASK_NOCLOSEPROCESS
        sei.lpVerb = "open"
        sei.lpFile = os.path.normpath(path)
        sei.nShow = 1

        if not ctypes.windll.shell32.ShellExecuteExW(byref(sei)):
            return None
        hp = sei.hProcess
        try:
            handle_val = ctypes.cast(hp, ctypes.c_void_p).value if hp else None
        except Exception:
            handle_val = None
        if handle_val:
            return ShellExecuteProcess(hp)
        return None
    except Exception:
        return None
