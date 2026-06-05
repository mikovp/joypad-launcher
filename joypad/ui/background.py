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


def scale_surface_cover(surface, width, height):
    """Scale *surface* to cover *width* x *height*, center-crop excess (CSS object-fit: cover)."""
    width = max(1, int(width))
    height = max(1, int(height))
    iw, ih = surface.get_size()
    if iw <= 0 or ih <= 0:
        return None
    if iw == width and ih == height:
        return surface
    scale = max(width / iw, height / ih)
    sw = max(1, int(round(iw * scale)))
    sh = max(1, int(round(ih * scale)))
    scaled = pygame.transform.smoothscale(surface, (sw, sh))
    if sw == width and sh == height:
        return scaled
    x = max(0, (sw - width) // 2)
    y = max(0, (sh - height) // 2)
    cropped = scaled.subsurface(pygame.Rect(x, y, width, height)).copy()
    return cropped


def load_background_surface(image_path, width, height):
    if not image_path:
        return None
    img_path = image_path if os.path.isabs(image_path) else os.path.join(_BASE_DIR, image_path)
    try:
        if os.path.isfile(img_path):
            img = pygame.image.load(img_path)
            return scale_surface_cover(img, width, height)
    except Exception:
        pass
    return None
