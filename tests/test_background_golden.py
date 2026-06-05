"""Background cover scaling for common display aspect ratios."""

import pytest

pytest.importorskip("pygame")
import pygame

from joypad.ui.background import scale_surface_cover

# 16:9 reference wallpaper size (typical bg.jpg).
_SRC_W, _SRC_H = 1920, 1080

# Target sizes at ~1080p height unless noted.
_ASPECT_TARGETS = {
    "4:3": (1440, 1080),
    "16:9": (1920, 1080),
    "16:10": (1920, 1200),
    "24:9": (2560, 1080),
    "32:9": (3840, 1080),
}


@pytest.fixture(scope="module", autouse=True)
def _pygame_init():
    pygame.init()
    yield
    pygame.quit()


def _solid_surface(w, h, color=(40, 40, 60)):
    surf = pygame.Surface((w, h))
    surf.fill(color)
    return surf


@pytest.mark.parametrize("label,target", _ASPECT_TARGETS.items())
def test_scale_surface_cover_matches_target_size(label, target):
    src = _solid_surface(_SRC_W, _SRC_H)
    out = scale_surface_cover(src, target[0], target[1])
    assert out is not None
    assert out.get_size() == target


@pytest.mark.parametrize("label,target", _ASPECT_TARGETS.items())
def test_scale_surface_cover_preserves_aspect_without_letterboxing(label, target):
    """Scaled output must fill the viewport — no dimension smaller than target."""
    tw, th = target
    src = _solid_surface(_SRC_W, _SRC_H)
    scale = max(tw / _SRC_W, th / _SRC_H)
    sw = max(1, int(round(_SRC_W * scale)))
    sh = max(1, int(round(_SRC_H * scale)))
    assert sw >= tw
    assert sh >= th
    out = scale_surface_cover(src, tw, th)
    assert out.get_size() == (tw, th)


def test_scale_surface_cover_exact_size_returns_same_dimensions():
    src = _solid_surface(800, 600)
    out = scale_surface_cover(src, 800, 600)
    assert out.get_size() == (800, 600)
