"""Scroll sync and frame rendering."""

import pygame

from joypad.ui import overlay as ovl
from joypad.ui.views import home as hm
from joypad.ui.views import list as lst
from joypad.ui.views import tiles


def update_scroll(state) -> None:
    if state.ui_mode == "tiles" and state.tile_snap_scroll:
        tiles._tile_snap_scroll(state)
    lst.snap_list_scroll(state)


def draw_frame(state) -> None:
    screen = state.screen
    h = state.h
    screen.fill(state.bg_color)
    if state.bg_surface and state.ui_mode != "home":
        screen.blit(state.bg_surface, (0, 0))
    screen.blit(state.title_surface, (60, 40))

    if state.ui_mode == "home":
        hm.draw_home_view(state)
    elif state.ui_mode == "tiles":
        screen.blit(state.hint_surface, (60, h - state.tile_geom["bottom_hint"]))
        tiles.draw_tiles_view(state)
    else:
        screen.blit(state.hint_surface, (60, h - state.list_bottom_margin))
        lst.draw_list_view(state)

    ovl.draw_overlay(state)
    pygame.display.flip()
