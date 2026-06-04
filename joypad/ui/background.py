import os

import pygame

from joypad.paths import _BASE_DIR


def resolve_background_image(config):
    """Background path relative to launcher folder, or None."""
    theme = config.get("theme") or {}
    val = theme.get("background_image")
    if val is False:
        return None
    if isinstance(val, str) and val.strip():
        return val.strip()
    if val is not False and os.path.isfile(os.path.join(_BASE_DIR, "bg.jpg")):
        return "bg.jpg"
    return None


def load_background_surface(image_path, width, height):
    if not image_path:
        return None
    img_path = image_path if os.path.isabs(image_path) else os.path.join(_BASE_DIR, image_path)
    try:
        if os.path.isfile(img_path):
            img = pygame.image.load(img_path)
            return pygame.transform.smoothscale(img, (width, height))
    except Exception:
        pass
    return None
