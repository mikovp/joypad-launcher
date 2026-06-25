import os, types, pygame
from joypad.config.loader import load_config
from joypad.ui.overlay.menu.layout import open_settings_overlay

def test_open_settings_lands_on_selectable_row():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init(); pygame.font.init()
    f = pygame.font.Font(None, 28)
    state = types.SimpleNamespace(
        config=load_config(),
        font_category=f, font_list=f,
        settings_menu_items=[], settings_cum_starts=[], settings_row_specs=[],
        settings_content_h=0, overlay_menu=None, overlay_index=None, overlay_scroll_y=None,
    )
    open_settings_overlay(state)
    assert state.overlay_menu == "settings"
    assert state.overlay_scroll_y == 0
    assert state.settings_menu_items, "layout should be rebuilt"
    # the highlighted row must be selectable, never a header
    assert state.settings_menu_items[state.overlay_index].get("kind") in ("setting", "action")
