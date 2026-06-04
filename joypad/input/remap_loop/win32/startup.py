"""Remap worker startup: logging, XInput scan, profile load."""

import os

from joypad.input.log import init_remap_log, remap_log
from joypad.input.profiles import load_profile
from joypad.input.remap_engine import RemapEngine
from joypad.input.xinput import (
    _xinput,
    pick_xinput_index,
    scan_xinput_indices,
)


def startup_remap_loop(profile_path, root_pid, user_index, log_dir, log_enabled, watch_exe, watch_dir, parent_pid):
    if log_enabled and log_dir:
        init_remap_log(log_dir)
    remap_log(
        "worker start profile=%s watch_pid=%s xinput_index=%s"
        % (os.path.abspath(profile_path), root_pid, user_index)
    )
    if not _xinput:
        remap_log("ERROR: XInput DLL not found (xinput1_4 / xinput1_3 / xinput9_1_0)")
        return None, None
    connected = scan_xinput_indices()
    if connected:
        for idx, btns, lx, ly in connected:
            remap_log("XInput[%s] ok buttons=0x%04x stick=(%s,%s)" % (idx, btns, lx, ly))
    else:
        remap_log("WARN: no XInput controllers on indices 0-3")
    if user_index not in [c[0] for c in connected] and connected:
        remap_log(
            "WARN: configured index %s has no pad; active indices: %s"
            % (user_index, [c[0] for c in connected])
        )
    user_index = pick_xinput_index(user_index)
    if watch_exe:
        remap_log("watch exe: %s" % watch_exe)
    if watch_dir:
        remap_log("watch dir: %s" % watch_dir)
    if parent_pid:
        remap_log("watch launcher pid: %s" % parent_pid)

    profile = load_profile(profile_path, base_dir=log_dir)
    engine = RemapEngine(profile)
    remap_log(
        "mouse method=%s sens=%s scale=%s keyboard=%s"
        % (
            engine.mouse_method,
            engine.mouse_sens,
            engine.mouse_scale,
            engine.keyboard_method,
        )
    )
    return engine, user_index
