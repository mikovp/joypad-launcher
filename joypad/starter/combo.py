"""Back + Start (View + Menu) combo detection via XInput."""

from __future__ import annotations

import time

from joypad.input.constants import BTN_BACK, BTN_START, XINPUT_FACE
from joypad.input.xinput import read_xinput

BACK_MASK = XINPUT_FACE[BTN_BACK]
START_MASK = XINPUT_FACE[BTN_START]
COMBO_MASK = BACK_MASK | START_MASK


def back_start_pressed(w_buttons: int) -> bool:
    """True when both Back and Start are down at the same time."""
    return bool(w_buttons & COMBO_MASK == COMBO_MASK)


def read_any_back_start(indices: list[int] | None = None) -> bool:
    """Scan given XInput slots (or 0-3) for the Back + Start combo."""
    if indices is not None and not indices:
        return False
    slots = range(4) if indices is None else indices
    for index in slots:
        pad = read_xinput(index)
        if pad is not None and back_start_pressed(pad.wButtons):
            return True
    return False


class GamepadScan:
    """Track connected XInput slots; rescan occasionally when idle."""

    __slots__ = ("_indices", "_next_rescan", "_rescan_s")

    def __init__(self, rescan_s: float = 2.0) -> None:
        self._rescan_s = rescan_s
        self._indices: list[int] = []
        self._next_rescan = 0.0

    def connected_indices(self, now: float | None = None) -> list[int]:
        now = time.monotonic() if now is None else now
        if self._indices and now < self._next_rescan:
            return self._indices
        found: list[int] = []
        for index in range(4):
            if read_xinput(index) is not None:
                found.append(index)
        self._indices = found
        self._next_rescan = now + self._rescan_s
        return self._indices

    def invalidate(self) -> None:
        self._indices = []
        self._next_rescan = 0.0
