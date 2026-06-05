"""Wait for game exit and restore launcher window."""

import sys

import pygame

from joypad.platform.windows.hwnd import _bring_launcher_to_front, _sleep_with_spinner
from joypad.platform.windows.process import get_process_and_descendant_pids

_get_process_and_descendant_pids = get_process_and_descendant_pids


def _yield_for_game_window(seconds=2.0, tick=None):
    """Gives game time to create window and get focus (event processing + pause)."""
    steps = max(1, int(seconds * 10))
    step_s = seconds / steps
    for _ in range(steps):
        _sleep_with_spinner(step_s, tick=tick)


def wait_for_game_and_restore(
    process, hwnd, platform=None, watch_exe=None, watch_dir=None, remap_proc=None, tick=None
):
    """Waits for game process to finish, then brings launcher to foreground."""
    if not process:
        return

    cancelled = False

    if platform == "steam" and sys.platform == "win32":
        while process.poll() is None:
            try:
                pids = _get_process_and_descendant_pids(process.pid)
            except Exception:
                pids = [process.pid]
            child_pids = [p for p in pids if p != process.pid]
            if not child_pids:
                break
            if _sleep_with_spinner(0.5, tick=tick):
                cancelled = True
                break
    elif remap_proc and sys.platform == "win32":
        while remap_proc.poll() is None:
            if _sleep_with_spinner(0.5, tick=tick):
                cancelled = True
                break
    elif platform == "epic" and (watch_exe or watch_dir) and sys.platform == "win32":
        from joypad.input.watch import wait_for_game_exe_exit

        def _pump():
            if tick:
                tick()
            else:
                pygame.event.pump()
            from joypad.platform.windows.hwnd.timed_pump import wait_cancel_pressed

            return wait_cancel_pressed()

        cancelled = wait_for_game_exe_exit(
            watch_exe,
            root_pid=process.pid,
            watch_dir=watch_dir,
            pump=_pump,
        )
    else:
        while process.poll() is None:
            if _sleep_with_spinner(0.5, tick=tick):
                cancelled = True
                break

    _bring_launcher_to_front(hwnd)
    return cancelled
