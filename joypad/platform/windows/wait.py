"""Wait for game exit and restore launcher window."""

import sys
import time

import pygame

from joypad.platform.windows.hwnd import _sleep_with_spinner
from joypad.platform.windows.hwnd.foreground import bring_launcher_to_front, restore_launcher_focus


def _yield_for_game_window(seconds=2.0, tick=None):
    """Gives game time to create window and get focus (event processing + pause)."""
    steps = max(1, int(seconds * 10))
    step_s = seconds / steps
    for _ in range(steps):
        _sleep_with_spinner(step_s, tick=tick)


def _launch_root_pid(process):
    if process is None:
        return None
    try:
        return process.pid if process.poll() is None else None
    except Exception:
        return getattr(process, "pid", None)


def _pump_with_cancel(tick):
    if tick:
        tick()
    else:
        pygame.event.pump()
    from joypad.platform.windows.hwnd.timed_pump import wait_cancel_pressed

    return wait_cancel_pressed()


def wait_for_game_and_restore(
    process,
    hwnd,
    platform=None,
    watch_exe=None,
    watch_dir=None,
    watch_title=None,
    remap_proc=None,
    tick=None,
    on_restore=None,
):
    """Waits for the game process to finish, then brings launcher to foreground."""
    has_watch = bool(watch_exe or watch_dir or watch_title)
    if process is None and not has_watch:
        return False

    cancelled = False

    if has_watch and sys.platform == "win32":
        from joypad.input.watch import wait_for_game_exe_exit

        cancelled = wait_for_game_exe_exit(
            watch_exe,
            root_pid=_launch_root_pid(process),
            watch_dir=watch_dir,
            watch_title=watch_title,
            pump=lambda: _pump_with_cancel(tick),
        )
    elif remap_proc and sys.platform == "win32":
        while remap_proc.poll() is None:
            if _sleep_with_spinner(0.5, tick=tick):
                cancelled = True
                break
    elif process is not None:
        while process.poll() is None:
            if _sleep_with_spinner(0.5, tick=tick):
                cancelled = True
                break

    def _pump_after_game() -> None:
        if tick:
            tick()
        else:
            pygame.event.pump()

    _pump_after_game()
    if cancelled:
        if on_restore:
            on_restore()
        bring_launcher_to_front(hwnd)
        return cancelled

    time.sleep(0.3)
    if on_restore:
        on_restore()
    restore_launcher_focus(hwnd, pump=_pump_after_game)
    return cancelled
