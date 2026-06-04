"""Gamepad image loading and scaling."""

import os
import sys

import pygame

from joypad.ui.editor.slots import PAD_IMAGE_FILE


def gamepad_image_path(session):
    rel = os.path.join("assets", PAD_IMAGE_FILE)
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        bundled = os.path.join(sys._MEIPASS, rel)
        if os.path.isfile(bundled):
            return bundled
    return os.path.join(session.base_dir, rel)


def get_gamepad_image(session, target_w, target_h):
    key = (max(1, int(target_w)), max(1, int(target_h)))
    if session._pad_img_key == key and session._pad_img is not None:
        return session._pad_img
    path = gamepad_image_path(session)
    if not os.path.isfile(path):
        session._pad_img = None
        session._pad_img_key = key
        return None
    try:
        img = pygame.image.load(path).convert_alpha()
        session._pad_img = pygame.transform.smoothscale(img, key)
        session._pad_img_key = key
        return session._pad_img
    except Exception:
        session._pad_img = None
        session._pad_img_key = key
        return None
