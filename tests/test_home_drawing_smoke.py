# tests/test_home_drawing_smoke.py
import os
import types
import pygame
import pytest

from joypad.ui.views.home.geometry import compute_home_geometry
from joypad.ui.views.home import navigation as nav


class _Cover:
    def get(self, game, w, h):
        s = pygame.Surface((w, h))
        s.fill((40, 40, 60))
        return s


def _fonts():
    pygame.font.init()
    return pygame.font.Font(None, 28)


@pytest.fixture
def headless_state():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    screen = pygame.Surface((1280, 720))
    f = _fonts()
    shelves = [
        {"title": "Steam", "games": [{"name": "Hades"}, {"name": "Celeste"}]},
        {"title": "All", "games": [{"name": "Celeste"}, {"name": "Hades"}]},
    ]
    st = types.SimpleNamespace(
        screen=screen, w=1280, h=720,
        home_shelves=shelves, home_focus=None, home_geom=None,
        cover_cache=_Cover(),
        font_title=f, font_category=f, font_hint=f,
        text_color=(230, 230, 230), title_color=(170, 170, 190),
        highlight_color=(45, 212, 191), bg_color=(20, 20, 28),
    )
    st.home_geom = compute_home_geometry(1280, 720, 26, 52)
    nav.home_init_focus(st)
    return st


def test_draw_home_view_runs(headless_state):
    from joypad.ui.views.home.drawing import draw_home_view
    draw_home_view(headless_state)   # must not raise


def test_draw_home_view_empty_shelves(headless_state):
    from joypad.ui.views.home.drawing import draw_home_view
    headless_state.home_shelves = []
    nav.home_init_focus(headless_state)
    draw_home_view(headless_state)   # must not raise
