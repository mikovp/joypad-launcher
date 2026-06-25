"""Background gamepad starter: Back + Start launches Joypad Launcher."""

from __future__ import annotations

import os
import subprocess
import sys
import time

from joypad.input.xinput import _xinput
from joypad.paths import _BASE_DIR
from joypad.starter.combo import GamepadScan, read_any_back_start
from joypad.starter.command import launcher_command, starter_pid_path
from joypad.starter.silent import apply_low_power_starter

DEFAULT_IDLE_POLL_MS = 200
DEFAULT_ARMED_POLL_MS = 66
DEFAULT_RELEASE_MS = 250
DEFAULT_NO_PAD_POLL_MS = 500
DEFAULT_RESCAN_S = 2.0
_MUTEX_NAME = "Global\\JoypadLauncherGamepadStarter"


def _acquire_starter_mutex():
    import ctypes

    kernel32 = ctypes.windll.kernel32
    handle = kernel32.CreateMutexW(None, True, _MUTEX_NAME)
    if not handle:
        return None
    if kernel32.GetLastError() == 183:
        kernel32.CloseHandle(handle)
        return None
    return handle


def _write_starter_pid() -> None:
    with open(starter_pid_path(), "w", encoding="utf-8") as f:
        f.write(str(os.getpid()))


def _clear_starter_pid() -> None:
    try:
        os.remove(starter_pid_path())
    except OSError:
        pass


def _poll_ms(scan: GamepadScan, active_poll_ms: int, idle_poll_ms: int) -> tuple[list[int], int]:
    indices = scan.connected_indices()
    if not indices:
        return [], idle_poll_ms
    return indices, active_poll_ms


def _wait_for_buttons_idle(
    release_ms: int,
    active_poll_ms: int,
    idle_poll_ms: int,
    scan: GamepadScan,
) -> None:
    """Wait until Back+Start are released for release_ms (ignore stale presses)."""
    clear_since: float | None = None
    while True:
        indices, poll_ms = _poll_ms(scan, active_poll_ms, idle_poll_ms)
        if not read_any_back_start(indices):
            if clear_since is None:
                clear_since = time.monotonic()
            elif (time.monotonic() - clear_since) * 1000.0 >= release_ms:
                return
        else:
            clear_since = None
        time.sleep(poll_ms / 1000.0)


def _wait_for_combo_press(active_poll_ms: int, idle_poll_ms: int, scan: GamepadScan) -> None:
    """Trigger once when Back+Start become pressed together (no hold required)."""
    was_pressed = False
    while True:
        indices, poll_ms = _poll_ms(scan, active_poll_ms, idle_poll_ms)
        pressed = read_any_back_start(indices)
        if pressed and not was_pressed:
            return
        was_pressed = pressed
        time.sleep(poll_ms / 1000.0)


def run_gamepad_starter(
    *,
    idle_poll_ms: int = DEFAULT_IDLE_POLL_MS,
    armed_poll_ms: int = DEFAULT_ARMED_POLL_MS,
    release_ms: int = DEFAULT_RELEASE_MS,
    no_pad_poll_ms: int = DEFAULT_NO_PAD_POLL_MS,
    rescan_s: float = DEFAULT_RESCAN_S,
) -> int:
    """Poll XInput until Back+Start; launch launcher; exit or resume per autostart setting."""
    apply_low_power_starter()
    if sys.platform != "win32":
        return 1
    if not _xinput:
        return 1
    mutex = _acquire_starter_mutex()
    if mutex is None:
        return 0

    scan = GamepadScan(rescan_s=rescan_s)
    _write_starter_pid()
    try:
        _run_gamepad_starter_loop(idle_poll_ms, armed_poll_ms, release_ms, no_pad_poll_ms, scan)
    finally:
        _clear_starter_pid()
        import ctypes

        ctypes.windll.kernel32.CloseHandle(mutex)
    return 0


def _starter_should_exit_after_launch() -> bool:
    from joypad.starter.registry import is_gamepad_starter_autostart_registered

    return is_gamepad_starter_autostart_registered()


def _allow_launcher_foreground() -> None:
    """Let the newly spawned launcher steal focus (Windows foreground lock)."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ASFW_ANY = ctypes.c_uint(-1).value
        ctypes.windll.user32.AllowSetForegroundWindow(ASFW_ANY)
    except Exception:
        pass


def _run_gamepad_starter_loop(
    idle_poll_ms: int,
    armed_poll_ms: int,
    release_ms: int,
    no_pad_poll_ms: int,
    scan: GamepadScan,
) -> None:
    while True:
        _wait_for_buttons_idle(release_ms, idle_poll_ms, no_pad_poll_ms, scan)
        _wait_for_combo_press(armed_poll_ms, no_pad_poll_ms, scan)
        _wait_for_buttons_idle(release_ms, idle_poll_ms, no_pad_poll_ms, scan)

        _allow_launcher_foreground()
        try:
            subprocess.Popen(launcher_command(), cwd=_BASE_DIR)
        except OSError:
            scan.invalidate()
            continue

        if _starter_should_exit_after_launch():
            return
        scan.invalidate()
