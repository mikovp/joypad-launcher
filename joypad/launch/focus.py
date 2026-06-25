"""Bring launched game to foreground and restore launcher when done."""

from joypad.platform.windows import (
    _yield_for_game_window,
    bring_game_to_foreground,
    bring_process_window_to_foreground,
    send_launcher_to_back,
    wait_for_game_and_restore,
)


def focus_launched_game(
    process,
    platform,
    *,
    hwnd,
    watch_exe,
    watch_dir,
    remap_proc,
    skip_restore,
    tick=None,
    on_restore=None,
):
    """Focus game window, hide launcher, wait until game exits."""
    _yield_for_game_window(2.0, tick=tick)
    if process and platform == "epic":
        bring_game_to_foreground(process, 12, tick=tick)
    elif process and platform == "steam":
        bring_game_to_foreground(process, 20, tick=tick)
    elif process and platform == "twitch":
        bring_game_to_foreground(process, 12, tick=tick)
    elif process:
        bring_process_window_to_foreground(process.pid)
        _yield_for_game_window(0.5, tick=tick)
        bring_process_window_to_foreground(process.pid)
    send_launcher_to_back(hwnd)
    if not skip_restore:
        wait_for_game_and_restore(
            process,
            hwnd,
            platform,
            watch_exe=watch_exe,
            watch_dir=watch_dir,
            remap_proc=remap_proc,
            tick=tick,
            on_restore=on_restore,
        )
