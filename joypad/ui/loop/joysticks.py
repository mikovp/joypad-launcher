"""Joystick discovery and hot-plug rescan."""

import pygame

from joypad.ui.loop.context import RESCAN_INTERVAL, LoopContext


def rescan_joysticks():
    pygame.joystick.quit()
    pygame.joystick.init()
    js = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for j in js:
        j.init()
    pygame.event.clear()
    return js


def maybe_rescan_joysticks(ctx: LoopContext, joysticks: list) -> list:
    ctx.frames_since_rescan += 1
    if ctx.frames_since_rescan >= RESCAN_INTERVAL:
        ctx.frames_since_rescan = 0
        return rescan_joysticks()
    return joysticks
