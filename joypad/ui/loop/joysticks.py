"""Joystick discovery and hot-plug rescan."""

import pygame

from joypad.ui.loop.context import RESCAN_INTERVAL, LoopContext


def rescan_joysticks(*, clear_events: bool = False) -> list:
    """Refresh the joystick list without tearing down the joystick subsystem."""
    joysticks: list = []
    for index in range(pygame.joystick.get_count()):
        stick = pygame.joystick.Joystick(index)
        if not stick.get_init():
            stick.init()
        joysticks.append(stick)
    if clear_events:
        pygame.event.clear()
    return joysticks


def maybe_rescan_joysticks(ctx: LoopContext, joysticks: list) -> list:
    ctx.frames_since_rescan += 1
    if ctx.frames_since_rescan < RESCAN_INTERVAL:
        return joysticks
    ctx.frames_since_rescan = 0
    if pygame.joystick.get_count() == len(joysticks):
        return joysticks
    return rescan_joysticks()
