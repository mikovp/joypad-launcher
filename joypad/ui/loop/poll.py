"""Continuous stick polling between events."""


from joypad.input.constants import AXIS_LEFT_X, AXIS_LEFT_Y, AXIS_REPEAT_FRAMES, DEADZONE
from joypad.ui.loop.context import LoopContext
from joypad.ui.views import list as lst


def poll_continuous_input(state, ctx: LoopContext, joysticks: list) -> None:
    if ctx.axis_held > 0:
        ctx.axis_held -= 1

    if not state.overlay_menu and joysticks and ctx.axis_held <= 0:
        stick = joysticks[0]
        y = stick.get_axis(AXIS_LEFT_Y)
        x = stick.get_axis(AXIS_LEFT_X)
        if y < -DEADZONE:
            lst.nav_vertical(state, -1)
            ctx.axis_held = AXIS_REPEAT_FRAMES
        elif y > DEADZONE:
            lst.nav_vertical(state, 1)
            ctx.axis_held = AXIS_REPEAT_FRAMES
        elif x < -DEADZONE:
            lst.nav_horizontal(state, -1)
            ctx.axis_held = AXIS_REPEAT_FRAMES
        elif x > DEADZONE:
            lst.nav_horizontal(state, 1)
            ctx.axis_held = AXIS_REPEAT_FRAMES
