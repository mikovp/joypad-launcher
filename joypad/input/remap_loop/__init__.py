"""Remap worker main loop (XInput poll + process watch)."""

import sys

if sys.platform == "win32":
    from joypad.input.remap_loop.win32 import run_remap_loop
else:
    from joypad.input.remap_loop.stubs import run_remap_loop

__all__ = ["run_remap_loop"]
