"""Input remapping: backward-compatible entry point."""

from joypad.input.remap_engine import RemapEngine
from joypad.input.remap_loop import run_remap_loop

__all__ = ["RemapEngine", "run_remap_loop"]
