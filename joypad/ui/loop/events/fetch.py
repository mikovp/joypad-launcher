"""Safe pygame.event.get wrapper."""

import pygame


def get_events():
    try:
        return pygame.event.get()
    except (KeyError, SystemError):
        return []
