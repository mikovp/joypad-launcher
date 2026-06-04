"""Windows system actions (shutdown / reboot)."""

import subprocess
import sys

_SUBPROCESS_KW = {
    "stdout": subprocess.DEVNULL,
    "stderr": subprocess.DEVNULL,
    "stdin": subprocess.DEVNULL,
}


def perform_system_action(action):
    """Performs Windows system action (shutdown / reboot)."""
    if sys.platform != "win32":
        return
    cmd = None
    if action == "shutdown":
        cmd = ["shutdown", "/s", "/t", "0"]
    elif action == "reboot":
        cmd = ["shutdown", "/r", "/t", "0"]
    if not cmd:
        return
    try:
        subprocess.Popen(cmd, shell=False, **_SUBPROCESS_KW)
    except Exception:
        pass
