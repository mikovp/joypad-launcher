"""Wait while pumping pygame events; optional tick callback for UI refresh."""

import time

import pygame


def timed_pump(seconds, tick=None):
    """Pause while pumping events; if tick is set, call it at ~10 fps."""
    pygame.event.pump()
    if not tick:
        time.sleep(seconds)
        return
    end = time.perf_counter() + seconds
    while time.perf_counter() < end:
        tick()
        remaining = end - time.perf_counter()
        if remaining > 0:
            time.sleep(min(0.1, remaining))
