"""Game process watch checks inside the remap worker loop."""

import os
import time

from joypad.input.constants import GAME_WATCH_ACTIVITY_GRACE, GAME_WATCH_GRACE
from joypad.input.log import remap_log
from joypad.input.watch import (
    _active_game_pids,
    _alive_pids,
    _any_pid_alive,
    _find_pids_in_directory,
    _get_process_tree_pids,
)


def watch_should_exit(
    now,
    use_watch,
    root_pid,
    watch_exe,
    watch_dir,
    watch_label,
    state,
    watch_title=None,
):
    """Update watch state. Returns True when the worker should stop."""
    last_watch_check = state["last_watch_check"]
    if use_watch and now - last_watch_check >= 0.5:
        if watch_dir and now - state["last_dir_scan"] >= 1.0:
            state["cached_dir_pids"] = _find_pids_in_directory(watch_dir, watch_exe)
            state["last_dir_scan"] = now
        alive = _alive_pids(
            _active_game_pids(
                root_pid,
                watch_exe,
                watch_dir,
                state["cached_dir_pids"],
                watch_title,
            )
        )
        if alive:
            state["last_seen"] = now
            state["last_activity"] = now
            if not state["restart_logged"] and root_pid and not _any_pid_alive({int(root_pid)}):
                remap_log(
                    "worker survived game restart (%s pids %s)"
                    % (watch_label, sorted(alive)[:4])
                )
                state["restart_logged"] = True
        elif now - state["last_activity"] <= GAME_WATCH_ACTIVITY_GRACE:
            state["last_seen"] = now
        elif now - state["last_seen"] >= GAME_WATCH_GRACE:
            remap_log("worker exit: %s gone for %.0fs" % (watch_label, GAME_WATCH_GRACE))
            return True
        state["last_watch_check"] = now
    elif not use_watch and not _any_pid_alive(_get_process_tree_pids(root_pid)):
        return True
    return False


def new_watch_state(watch_exe, watch_dir, watch_title=None):
    now = time.time()
    return {
        "last_watch_check": 0.0,
        "last_dir_scan": 0.0,
        "cached_dir_pids": set(),
        "last_seen": now,
        "last_activity": now,
        "restart_logged": False,
        "watch_label": watch_exe or watch_title or os.path.basename(watch_dir or "game"),
    }
