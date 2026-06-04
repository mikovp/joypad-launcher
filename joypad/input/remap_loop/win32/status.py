"""Periodic remap worker status logging."""

import time

from joypad.input.log import remap_log
from joypad.input.watch import _active_game_pids, _alive_pids, _get_process_tree_pids


def log_status_if_due(engine, ticks, use_watch, root_pid, watch_exe, watch_dir, state):
    now = time.time()
    if now - state["last_status"] < 2.0:
        return
    if use_watch:
        alive = _alive_pids(
            _active_game_pids(root_pid, watch_exe, watch_dir, state["cached_dir_pids"])
        )
        pid_count = len(alive)
    else:
        pid_count = len(_alive_pids(_get_process_tree_pids(root_pid)))
    sent_delta = engine._mouse_sent - state["mouse_sent_prev"]
    state["mouse_sent_prev"] = engine._mouse_sent
    remap_log(
        "alive ticks=%s alive_pids=%s pad=%s keys=%s stick=(%.2f,%.2f) mouse_px=%s"
        % (
            ticks,
            pid_count,
            "ok" if state.get("pad_ok") else "none",
            sum(1 for c in engine._key_refcount.values() if c > 0),
            engine._last_rx,
            engine._last_ry,
            sent_delta,
        )
    )
    state["last_status"] = now


def new_status_state():
    return {
        "last_status": time.time(),
        "mouse_sent_prev": 0,
        "pad_ok": False,
    }
