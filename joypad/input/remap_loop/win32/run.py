"""Remap worker main loop (Windows)."""

import time

from joypad.input.log import remap_log
from joypad.input.remap_loop.win32.startup import startup_remap_loop
from joypad.input.remap_loop.win32.status import log_status_if_due, new_status_state
from joypad.input.remap_loop.win32.watch import new_watch_state, watch_should_exit
from joypad.input.watch import _any_pid_alive
from joypad.input.xinput import gamepad_active, read_xinput


def run_remap_loop(
    profile_path,
    root_pid,
    user_index=0,
    poll_ms=8,
    log_dir=None,
    log_enabled=False,
    watch_exe=None,
    watch_dir=None,
    parent_pid=None,
):
    engine, user_index = startup_remap_loop(
        profile_path, root_pid, user_index, log_dir, log_enabled, watch_exe, watch_dir, parent_pid
    )
    if engine is None:
        return

    ticks = 0
    state = new_watch_state(watch_exe, watch_dir)
    state.update(new_status_state())
    use_watch = bool(watch_exe or watch_dir)
    last_parent_check = 0.0

    try:
        while True:
            now = time.time()
            pad = read_xinput(user_index)
            state["pad_ok"] = pad is not None
            if gamepad_active(pad):
                state["last_activity"] = now
            if parent_pid and now - last_parent_check >= 0.5:
                if not _any_pid_alive({int(parent_pid)}):
                    remap_log("worker exit: launcher pid %s gone" % parent_pid)
                    break
                last_parent_check = now
            if watch_should_exit(now, use_watch, root_pid, watch_exe, watch_dir, state["watch_label"], state):
                break

            engine.tick(pad)
            ticks += 1
            if ticks == 1:
                remap_log("loop running pad=%s" % ("ok" if pad else "none"))
            log_status_if_due(engine, ticks, use_watch, root_pid, watch_exe, watch_dir, state)
            time.sleep(poll_ms / 1000.0)
    except Exception as exc:
        remap_log("ERROR loop: %s" % exc)
        raise
    finally:
        remap_log("worker stop ticks=%s" % ticks)
        engine.release_all()
