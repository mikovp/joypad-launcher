"""Shared subprocess defaults for game launches."""

import subprocess

SUBPROCESS_KW = {
    "stdout": subprocess.DEVNULL,
    "stderr": subprocess.DEVNULL,
    "stdin": subprocess.DEVNULL,
}
