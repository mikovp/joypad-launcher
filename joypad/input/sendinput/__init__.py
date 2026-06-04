"""Windows SendInput keyboard/mouse injection."""

import sys

if sys.platform == "win32":
    from joypad.input.sendinput.win32 import (
        key_event,
        mouse_button,
        mouse_center_screen,
        mouse_move,
        mouse_wheel,
    )
else:
    from joypad.input.sendinput.stubs import (
        key_event,
        mouse_button,
        mouse_center_screen,
        mouse_move,
        mouse_wheel,
    )

__all__ = [
    "key_event",
    "mouse_button",
    "mouse_center_screen",
    "mouse_move",
    "mouse_wheel",
]
