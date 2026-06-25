"""Game launch orchestration (process start, remap worker, foreground)."""

import os
import sys

from joypad.input.log import init_remap_log, remap_log, remap_log_enabled
from joypad.input.profiles import game_remap_key, resolve_profile_path
from joypad.input.watch import game_watch_targets
from joypad.input.worker import start_remap_worker, stop_remap_worker
from joypad.launch.focus import focus_launched_game
from joypad.launch.start import start_game_process
from joypad.launch.system import perform_system_action
from joypad.paths import _BASE_DIR


def try_launch_game(
    g,
    state,
    *,
    steam_path,
    default_args,
    steam_skip_restore_ids,
    hwnd,
    active_remap_proc,
    spinner_tick=None,
):
    """Launches game g. Returns (exit_launcher, axis_held) or None on skip."""
    config = state.config
    profile_path = resolve_profile_path(config, g, _BASE_DIR) if sys.platform == "win32" else None
    if sys.platform == "win32" and remap_log_enabled(config):
        init_remap_log(_BASE_DIR, enabled=True)
        remap_log(
            "launch %s key=%s profile=%s"
            % (g.get("name"), game_remap_key(g), profile_path or "(none)")
        )

    started = start_game_process(
        g,
        state,
        steam_path=steam_path,
        default_args=default_args,
        steam_skip_restore_ids=steam_skip_restore_ids,
    )
    if started == "exit":
        return (True, 0)
    if started is None:
        return None

    process = started.process
    platform = started.platform
    skip_restore = started.skip_restore
    remap_proc = None
    watch_exe, watch_dir = game_watch_targets(g)
    if profile_path:
        remap_proc = start_remap_worker(
            profile_path,
            process.pid,
            _BASE_DIR,
            watch_exe=watch_exe,
            watch_dir=watch_dir,
            parent_pid=os.getpid(),
            log_enabled=remap_log_enabled(config),
        )
        active_remap_proc[0] = remap_proc

    try:
        def _restore_launcher() -> None:
            from joypad.bootstrap.display import resync_launcher_display

            resync_launcher_display(state, hwnd)

        focus_launched_game(
            process,
            platform,
            hwnd=hwnd,
            watch_exe=watch_exe,
            watch_dir=watch_dir,
            remap_proc=remap_proc,
            skip_restore=skip_restore,
            tick=spinner_tick,
            on_restore=_restore_launcher,
        )
    finally:
        stop_remap_worker(remap_proc)
        active_remap_proc[0] = None
    return (False, 15)


__all__ = ["perform_system_action", "try_launch_game"]
