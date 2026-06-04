import os
import time

from joypad.input.profiles import remap_settings

REMAP_LOG_NAME = "input_remap.log"

_remap_log_path = None


def remap_log_enabled(config):
    return bool(remap_settings(config).get("log", False))


def remap_log_path(base_dir):
    return os.path.join(base_dir or ".", REMAP_LOG_NAME)


def init_remap_log(base_dir, enabled=True):
    """Append-only log next to launcher for remap worker diagnostics."""
    global _remap_log_path
    if not enabled:
        _remap_log_path = None
        return
    path = remap_log_path(base_dir)
    _remap_log_path = path
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n=== %s ===\n" % time.strftime("%Y-%m-%d %H:%M:%S"))
    except Exception:
        _remap_log_path = None


def remap_log(message):
    if not _remap_log_path:
        return
    line = "[%s] %s\n" % (time.strftime("%H:%M:%S"), message)
    try:
        with open(_remap_log_path, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass
