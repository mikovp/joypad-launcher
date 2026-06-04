"""Scroll sync and frame rendering."""

import pygame

from joypad.ui import overlay as ovl
from joypad.ui.views import list as lst
from joypad.ui.views import tiles


def update_scroll(state) -> None:
    if state.ui_mode == "tiles" and state.tile_snap_scroll:
        tiles._tile_snap_scroll(state)
    lst.snap_list_scroll(state)


def draw_frame(state) -> None:
    screen = state.screen
    h = state.h
    if state.bg_surface:
        screen.blit(state.bg_surface, (0, 0))
    else:
        screen.fill(state.bg_color)
    screen.blit(state.title_surface, (60, 40))
    hint_bottom = state.tile_geom["bottom_hint"] if state.ui_mode == "tiles" else state.list_bottom_margin
    screen.blit(state.hint_surface, (60, h - hint_bottom))

    if state.ui_mode == "tiles":
        tiles.draw_tiles_view(state)
    else:
        lst.draw_list_view(state)

    ovl.draw_overlay(state)

    pygame.display.flip()
