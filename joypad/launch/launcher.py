import os
import subprocess
import sys

try:
    import pygame
except ImportError:
    print("Install pygame: pip install pygame")
    sys.exit(1)

from joypad.platform.windows import (
    _send_launcher_to_back,
    _bring_process_window_to_foreground,
    _bring_game_to_foreground,
    _yield_for_game_window,
    _wait_for_game_and_restore,
)

_SUBPROCESS_KW = {
    "stdout": subprocess.DEVNULL,
    "stderr": subprocess.DEVNULL,
    "stdin": subprocess.DEVNULL,
}


def launch_steam_game(steam_exe, app_id, launch_args, steam_start_args=None):
    """Launches Steam game. Returns Popen process (for switching focus to Steam/game window).

    steam_start_args — extra args for Steam client (e.g. '-silent'), from config.json -> steam_start_args.
    """
    args = [steam_exe]
    if steam_start_args:
        args.extend(steam_start_args.split())
    args.extend(["-applaunch", str(app_id)])
    if launch_args:
        args.extend(launch_args.split())
    return subprocess.Popen(args, shell=False, **_SUBPROCESS_KW)


def launch_epic_game(exe_path, launch_args):
    """Launch Epic game by exe path. Returns Popen process or None."""
    exe_path = os.path.abspath(exe_path)
    if not os.path.isfile(exe_path):
        return None
    work_dir = os.path.dirname(exe_path)
    args = [exe_path]
    if launch_args:
        args.extend(launch_args.split())
    return subprocess.Popen(args, cwd=work_dir, shell=False, **_SUBPROCESS_KW)


class _ShellExecuteProcess:
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
        from ctypes import windll, byref
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


def _shell_execute_open_file(path):
    """Windows: open file with its registered app (same as double-click)."""
    if sys.platform != "win32":
        return None
    try:
        import ctypes
        from ctypes import wintypes, byref

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
            return _ShellExecuteProcess(hp)
        return None
    except Exception:
        return None


def launch_nsp_game(emulator_exe, nsp_path, launch_args, use_association=True):
    """
    Launch .nsp: on Windows with use_association, via file-type association (e.g. Ryujinx for .nsp);
    otherwise or if the shell returns no process handle, run emulator_exe + ROM directly.
    """
    nsp_path = os.path.normpath(nsp_path)
    if not os.path.isfile(nsp_path):
        return None
    if sys.platform == "win32" and use_association:
        proc = _shell_execute_open_file(nsp_path)
        if proc is not None:
            return proc
    emulator_exe = (emulator_exe or "").strip()
    if not emulator_exe:
        return None
    emulator_exe = os.path.normpath(emulator_exe)
    if not os.path.isfile(emulator_exe):
        return None
    work_dir = os.path.dirname(emulator_exe)
    args = [emulator_exe, nsp_path]
    if launch_args:
        args.extend(str(launch_args).split())
    return subprocess.Popen(args, cwd=work_dir, shell=False, **_SUBPROCESS_KW)


def perform_system_action(action):
    """Performs Windows system action (shutdown / reboot)."""
    if sys.platform != "win32":
        return
    cmd = None
    # Can be extended (sleep, hibernate, etc.)
    if action == "shutdown":
        cmd = ["shutdown", "/s", "/t", "0"]
    elif action == "reboot":
        cmd = ["shutdown", "/r", "/t", "0"]
    if not cmd:
        return
    try:
        subprocess.Popen(cmd, shell=False, **_SUBPROCESS_KW)
    except Exception:
        # Error here is non-critical, just ignore
        pass


def _try_launch_game(g, steam_path, default_args, steam_start_args, steam_skip_restore_ids, hwnd):
    """Launches game from entry g. Returns (should_exit, axis_held) or None on skip."""
    platform = g.get("platform")
    skip_restore = False
    process = None

    if platform == "steam":
        if not steam_path:
            print("Steam not found. Specify steam_path in config.json")
            return None
        aid = g.get("steam_app_id")
        if not aid:
            return None
        args = g.get("launch_args") or default_args.get("steam", "-fullscreen")
        process = launch_steam_game(steam_path, aid, args, steam_start_args)
        if str(aid) in steam_skip_restore_ids:
            skip_restore = True
    elif platform == "epic":
        exe = g.get("exe_path")
        if not exe:
            return None
        args = g.get("launch_args") or default_args.get("epic", "-fullscreen")
        process = launch_epic_game(exe, args)
    elif platform == "system":
        action = g.get("system_action")
        if action:
            perform_system_action(action)
            return (True,)  # should_exit
        return None

    _yield_for_game_window(2.0)
    if process and platform == "epic":
        _bring_game_to_foreground(process, 12)
    elif process and platform == "steam":
        _bring_game_to_foreground(process, 20)
    elif process:
        _bring_process_window_to_foreground(process.pid)
        _yield_for_game_window(0.5)
        _bring_process_window_to_foreground(process.pid)
    _send_launcher_to_back(hwnd)
    pygame.display.iconify()
    if not skip_restore:
        _wait_for_game_and_restore(process, hwnd, platform)
    return (False, 15)  # axis_held
