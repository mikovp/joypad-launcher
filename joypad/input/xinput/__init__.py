"""XInput read helpers and stick normalization."""

import sys

from joypad.input.xinput.math import XINPUT_L3, XINPUT_R3, apply_deadzone, norm_axis

if sys.platform == "win32":
    from joypad.input.xinput.win32 import (
        _xinput,
        gamepad_active,
        pick_xinput_index,
        read_xinput,
        scan_xinput_indices,
    )
else:
    from joypad.input.xinput.stubs import (
        _xinput,
        gamepad_active,
        pick_xinput_index,
        read_xinput,
        scan_xinput_indices,
    )

__all__ = [
    "XINPUT_L3",
    "XINPUT_R3",
    "_xinput",
    "apply_deadzone",
    "gamepad_active",
    "norm_axis",
    "pick_xinput_index",
    "read_xinput",
    "scan_xinput_indices",
]
