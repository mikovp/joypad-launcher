"""Windows SendInput keyboard/mouse injection."""

from joypad.input.sendinput.win32.keyboard import key_event
from joypad.input.sendinput.win32.mouse import (
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
