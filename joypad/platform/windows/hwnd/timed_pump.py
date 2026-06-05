"""Wait while pumping pygame events; optional tick callback for UI refresh."""

import time

import pygame

from joypad.input.constants import BTN_B


def wait_cancel_pressed():
    """True when B or Escape was pressed to abort waiting for the game."""
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return True
        if event.type == pygame.JOYBUTTONDOWN and event.button == BTN_B:
            return True
    return False


def timed_pump(seconds, tick=None):
    """Pause while pumping events; if tick is set, call it at ~10 fps.

    Returns True if the user cancelled the wait (B or Escape).
    """
    pygame.event.pump()
    if not tick:
        end = time.perf_counter() + seconds
        while time.perf_counter() < end:
            if wait_cancel_pressed():
                return True
            remaining = end - time.perf_counter()
            if remaining > 0:
                time.sleep(min(0.1, remaining))
        return False
    end = time.perf_counter() + seconds
    while time.perf_counter() < end:
        tick()
        if wait_cancel_pressed():
            return True
        remaining = end - time.perf_counter()
        if remaining > 0:
            time.sleep(min(0.1, remaining))
    return False
