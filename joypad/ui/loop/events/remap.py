"""Input remap editor session event loop."""

import pygame

from joypad.input.constants import AXIS_LEFT_X, AXIS_LEFT_Y, AXIS_REPEAT_FRAMES, DEADZONE
from joypad.ui.editor import input as editor_input
from joypad.ui.loop.context import LoopContext


def handle_remap_session(state, events, ctx: LoopContext, joysticks: list, clock) -> bool:
    """Process remap editor session. Returns True if the frame is fully handled."""
    if not state.input_remap_session:
        return False
    session = state.input_remap_session
    for event in events:
        if event.type == pygame.QUIT:
            state.running = False
    session.process_events(events)
    if ctx.axis_held <= 0 and joysticks:
        stick = joysticks[0]
        y = stick.get_axis(AXIS_LEFT_Y)
        x = stick.get_axis(AXIS_LEFT_X)
        if y < -DEADZONE:
            editor_input.nav(session, -1)
            ctx.axis_held = AXIS_REPEAT_FRAMES
        elif y > DEADZONE:
            editor_input.nav(session, 1)
            ctx.axis_held = AXIS_REPEAT_FRAMES
        elif session.mode == "editor" and x < -DEADZONE:
            editor_input.nav_h(session, -1)
            ctx.axis_held = AXIS_REPEAT_FRAMES
        elif session.mode == "editor" and x > DEADZONE:
            editor_input.nav_h(session, 1)
            ctx.axis_held = AXIS_REPEAT_FRAMES
    if ctx.axis_held > 0:
        ctx.axis_held -= 1
    session.draw()
    pygame.display.flip()
    clock.tick(60)
    if session.finished:
        state.input_remap_session = None
    return True
