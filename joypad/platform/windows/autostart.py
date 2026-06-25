"""Windows Run-key autostart for the gamepad starter."""

from __future__ import annotations

import os
import subprocess
import sys
import time

from joypad.integrations._subprocess import subprocess_no_window_kw
from joypad.starter.command import (
    STARTER_EXE_NAME,
    format_gamepad_starter_command,
    gamepad_starter_command,
    starter_exe_path,
    starter_pid_path,
)
from joypad.starter.registry import (
    _RUN_KEY,
    _VALUE_NAME,
    is_gamepad_starter_autostart_registered,
)

_STARTER_RESTART_DELAY_S = 0.25


def is_gamepad_starter_running() -> bool:
    if sys.platform != "win32":
        return False
    path = starter_pid_path()
    if not os.path.isfile(path):
        return False
    try:
        with open(path, encoding="utf-8") as f:
            pid = int(f.read().strip())
    except (OSError, ValueError):
        return False
    result = subprocess.run(
        ["tasklist", "/FI", "PID eq %d" % pid, "/NH"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        **subprocess_no_window_kw(),
    )
    return str(pid) in (result.stdout or "")


def _stop_all_starters() -> None:
    subprocess.run(
        ["taskkill", "/IM", STARTER_EXE_NAME, "/F"],
        capture_output=True,
        **subprocess_no_window_kw(),
    )
    try:
        os.remove(starter_pid_path())
    except OSError:
        pass


def _start_gamepad_starter_process() -> bool:
    if not os.path.isfile(starter_exe_path()):
        return False
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        subprocess.Popen(
            gamepad_starter_command(),
            creationflags=flags,
            cwd=os.path.dirname(starter_exe_path()),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
        )
    except OSError:
        return False
    return True


def ensure_gamepad_starter_running() -> bool:
    """Start JoypadStarter if autostart is enabled but the listener is not running."""
    if sys.platform != "win32":
        return False
    if not is_gamepad_starter_autostart_registered():
        return False
    if is_gamepad_starter_running():
        return True
    _stop_all_starters()
    time.sleep(_STARTER_RESTART_DELAY_S)
    return _start_gamepad_starter_process()


def _spawn_gamepad_starter() -> bool:
    _stop_all_starters()
    time.sleep(_STARTER_RESTART_DELAY_S)
    return _start_gamepad_starter_process()


def set_gamepad_starter_autostart(enabled: bool) -> bool:
    if sys.platform != "win32":
        return False
    try:
        import winreg

        if enabled:
            if not os.path.isfile(starter_exe_path()):
                return False
            cmd = format_gamepad_starter_command()
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE)
            try:
                winreg.SetValueEx(key, _VALUE_NAME, 0, winreg.REG_SZ, cmd)
            except OSError:
                winreg.CloseKey(key)
                return False
            winreg.CloseKey(key)
            if not _spawn_gamepad_starter():
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE)
                try:
                    winreg.DeleteValue(key, _VALUE_NAME)
                except FileNotFoundError:
                    pass
                winreg.CloseKey(key)
                return False
            return True
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE)
        try:
            winreg.DeleteValue(key, _VALUE_NAME)
        except FileNotFoundError:
            pass
        winreg.CloseKey(key)
        _stop_all_starters()
        return True
    except OSError:
        return False
