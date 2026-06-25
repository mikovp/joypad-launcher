"""Shared subprocess defaults for game launches."""

import subprocess
import sys


def no_console_creationflags() -> int:
    if sys.platform == "win32":
        return getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return 0


SUBPROCESS_KW = {
    "stdout": subprocess.DEVNULL,
    "stderr": subprocess.DEVNULL,
    "stdin": subprocess.DEVNULL,
}
_flags = no_console_creationflags()
if _flags:
    SUBPROCESS_KW["creationflags"] = _flags


def subprocess_no_window_kw() -> dict:
    flags = no_console_creationflags()
    return {"creationflags": flags} if flags else {}
