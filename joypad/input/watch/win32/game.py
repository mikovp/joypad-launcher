"""Game process watch loop and aggregate PID resolution."""

import os
import time

from joypad.input.constants import GAME_WATCH_ACTIVITY_GRACE, GAME_WATCH_GRACE
from joypad.input.log import remap_log
from joypad.input.watch.win32.find import (
    find_pids_by_exe_name,
    find_pids_by_window_substring,
    find_pids_in_directory,
)
from joypad.input.watch.win32.process import alive_pids, any_pid_alive, get_process_tree_pids


def active_game_pids(root_pid, watch_exe=None, watch_dir=None, cached_dir_pids=None, watch_title=None):
    pids = set()
    if root_pid:
        pids |= get_process_tree_pids(root_pid)
    if watch_exe:
        pids |= find_pids_by_exe_name(watch_exe)
        stem = os.path.splitext(watch_exe)[0]
        if len(stem) >= 4:
            pids |= find_pids_by_window_substring(stem)
    if watch_dir:
        if cached_dir_pids is not None:
            pids |= cached_dir_pids
        else:
            pids |= find_pids_in_directory(watch_dir, watch_exe)
    if watch_title:
        pids |= find_pids_by_window_substring(watch_title)
    return pids


def game_process_alive(root_pid, watch_exe=None, watch_dir=None, cached_dir_pids=None, watch_title=None):
    pids = active_game_pids(root_pid, watch_exe, watch_dir, cached_dir_pids, watch_title)
    return bool(alive_pids(pids))


def wait_for_game_exe_exit(
    watch_exe,
    root_pid=None,
    watch_dir=None,
    grace=GAME_WATCH_GRACE,
    pump=None,
    watch_title=None,
):
    """Wait until no matching game process runs (survives Epic launcher restart).

    Returns True if pump reported user cancel (B / Escape).
    """
    if not watch_exe and not watch_dir and not watch_title:
        return False
    last_seen = time.time()
    last_activity = last_seen
    restart_logged = False
    cached_dir_pids = set()
    last_dir_scan = 0.0
    label = watch_exe or watch_title or os.path.basename(watch_dir or "game")
    while True:
        now = time.time()
        if watch_dir and now - last_dir_scan >= 1.0:
            cached_dir_pids = find_pids_in_directory(watch_dir, watch_exe)
            last_dir_scan = now
        alive = alive_pids(
            active_game_pids(root_pid, watch_exe, watch_dir, cached_dir_pids, watch_title)
        )
        if alive:
            last_seen = now
            last_activity = now
            if (
                not restart_logged
                and root_pid
                and not any_pid_alive({int(root_pid)})
            ):
                remap_log("launcher wait: %s restarted (pids %s)" % (label, sorted(alive)[:4]))
                restart_logged = True
        elif now - last_activity <= GAME_WATCH_ACTIVITY_GRACE:
            last_seen = now
        elif now - last_seen >= grace:
            remap_log("launcher wait: %s gone for %.0fs" % (label, grace))
            break
        if pump:
            if pump():
                remap_log("launcher wait: %s cancelled" % label)
                return True
        time.sleep(0.1 if pump else 0.5)
    return False
