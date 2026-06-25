"""Direct XInput polling for launcher UI (works without window focus on Windows)."""

from __future__ import annotations

import sys
from typing import Callable

from joypad.input.constants import (
    AXIS_REPEAT_FRAMES,
    BTN_A,
    BTN_B,
    BTN_BACK,
    BTN_LB,
    BTN_RB,
    BTN_START,
    DEADZONE,
    XINPUT_DPAD,
    XINPUT_FACE,
)
from joypad.input.xinput import _xinput, pick_xinput_index, read_xinput
from joypad.input.xinput.math import apply_deadzone, norm_axis
from joypad.ui import overlay as ovl
from joypad.ui.loop.context import LoopContext
from joypad.ui.views import list as lst

_TRIGGER_PAGE = int(0.72 * 255)
_TRIGGER_RELEASE = int(0.2 * 255)


def launcher_uses_xinput() -> bool:
    return sys.platform == "win32" and _xinput is not None


def poll_xinput_input(state, ctx: LoopContext, on_launch: Callable[[], bool]) -> bool:
    """Poll XInput once. Returns True when the launcher should exit."""
    if ctx.axis_held > 0:
        ctx.axis_held -= 1

    pad = read_xinput(pick_xinput_index(0))
    if pad is None:
        ctx.xinput_prev_buttons = 0
        return False

    buttons = pad.wButtons
    new_press = buttons & ~ctx.xinput_prev_buttons
    ctx.xinput_prev_buttons = buttons

    menu_back = bool(new_press & (XINPUT_FACE[BTN_B] | XINPUT_FACE[BTN_BACK]))
    if menu_back:
        if state.overlay_menu:
            ovl.overlay_back(state)
        else:
            state.overlay_menu = "system"
            state.overlay_index = 0
        return False

    if new_press & (XINPUT_FACE[BTN_A] | XINPUT_FACE[BTN_START]):
        if state.overlay_menu:
            ovl.overlay_confirm(state)
        elif on_launch():
            return True
        return False

    if not state.overlay_menu:
        if new_press & XINPUT_FACE[BTN_LB]:
            lst.nav_lb_rb(state, -1)
            return False
        if new_press & XINPUT_FACE[BTN_RB]:
            lst.nav_lb_rb(state, 1)
            return False

    if ctx.axis_held <= 0:
        if new_press & XINPUT_DPAD["dpad_up"]:
            _nav_vertical(state, -1)
            ctx.axis_held = AXIS_REPEAT_FRAMES
            return False
        if new_press & XINPUT_DPAD["dpad_down"]:
            _nav_vertical(state, 1)
            ctx.axis_held = AXIS_REPEAT_FRAMES
            return False
        if not state.overlay_menu:
            if new_press & XINPUT_DPAD["dpad_left"]:
                lst.nav_horizontal(state, -1)
                ctx.axis_held = AXIS_REPEAT_FRAMES
                return False
            if new_press & XINPUT_DPAD["dpad_right"]:
                lst.nav_horizontal(state, 1)
                ctx.axis_held = AXIS_REPEAT_FRAMES
                return False

        lx = apply_deadzone(norm_axis(pad.sThumbLX), DEADZONE)
        ly = apply_deadzone(norm_axis(pad.sThumbLY), DEADZONE)
        if ly > DEADZONE:
            _nav_vertical(state, -1)
            ctx.axis_held = AXIS_REPEAT_FRAMES
        elif ly < -DEADZONE:
            _nav_vertical(state, 1)
            ctx.axis_held = AXIS_REPEAT_FRAMES
        elif not state.overlay_menu:
            if lx < -DEADZONE:
                lst.nav_horizontal(state, -1)
                ctx.axis_held = AXIS_REPEAT_FRAMES
            elif lx > DEADZONE:
                lst.nav_horizontal(state, 1)
                ctx.axis_held = AXIS_REPEAT_FRAMES
            elif pad.bRightTrigger >= _TRIGGER_PAGE:
                if ctx.trig_page_arm_rt:
                    lst.nav_page(state, 1)
                    ctx.trig_page_arm_rt = False
                    ctx.axis_held = AXIS_REPEAT_FRAMES * 2
            elif pad.bRightTrigger < _TRIGGER_RELEASE:
                ctx.trig_page_arm_rt = True
            if pad.bLeftTrigger >= _TRIGGER_PAGE:
                if ctx.trig_page_arm_lt:
                    lst.nav_page(state, -1)
                    ctx.trig_page_arm_lt = False
                    ctx.axis_held = AXIS_REPEAT_FRAMES * 2
            elif pad.bLeftTrigger < _TRIGGER_RELEASE:
                ctx.trig_page_arm_lt = True

    return False


def _nav_vertical(state, delta: int) -> None:
    if state.overlay_menu:
        ovl.overlay_move(state, delta)
    else:
        lst.nav_vertical(state, delta)
