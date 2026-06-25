"""Home view pygame rendering: rail, hero, horizontal shelves."""

import pygame

from joypad.ui.views.home.geometry import compute_home_geometry
from joypad.ui.views.home.model import build_home_shelves
from joypad.ui.views.home.navigation import (
    RAIL_ITEMS,
    home_init_focus,
    home_selected_game,
)

_RAIL_GLYPH = {"home": "⌂", "settings": "⚙", "power": "⏻"}


def rebuild_home(state):
    sections = getattr(state, "tile_sections", None)
    state.home_shelves = build_home_shelves(sections)
    state.home_geom = compute_home_geometry(
        state.w, state.h, state.font_hint.get_linesize(), state.font_title.get_linesize()
    )
    if not state.home_focus:
        home_init_focus(state)


def _truncate(font, text, max_w):
    t = (text or "").strip() or "Untitled"
    if font.size(t)[0] <= max_w:
        return t
    for n in range(len(t), 0, -1):
        if font.size(t[:n] + "…")[0] <= max_w:
            return t[:n] + "…"
    return "…"


def _draw_rail(state, g):
    f = state.home_focus
    rail_w = g["rail_w"]
    pygame.draw.rect(state.screen, (0, 0, 0), (0, 0, rail_w, state.h))
    n = len(RAIL_ITEMS)
    step = state.h // (n + 1)
    for i, item in enumerate(RAIL_ITEMS):
        cy = step * (i + 1)
        active = f and f["zone"] == "rail" and f["rail"] == i
        color = state.highlight_color if active else state.title_color
        glyph = state.font_title.render(_RAIL_GLYPH.get(item, "?"), True, color)
        rect = glyph.get_rect(center=(rail_w // 2, cy))
        if active:
            pygame.draw.rect(state.screen, state.highlight_color,
                             (4, cy - step // 2 + 6, rail_w - 8, step - 12), 2)
        state.screen.blit(glyph, rect)


def _draw_hero(state, g):
    hero = g["hero"]
    game = home_selected_game(state)
    pygame.draw.rect(state.screen, (30, 30, 42), (hero["x"], hero["y"], hero["w"], hero["h"]))
    if game is None:
        return
    # Blurred backdrop: scale cover up then down (cheap blur), tint dark.
    backdrop = state.cover_cache.get(game, hero["w"], hero["h"])
    if backdrop:
        small = pygame.transform.smoothscale(backdrop, (max(1, hero["w"] // 12), max(1, hero["h"] // 12)))
        blurred = pygame.transform.smoothscale(small, (hero["w"], hero["h"]))
        blurred.set_alpha(110)
        state.screen.blit(blurred, (hero["x"], hero["y"]))
    # Portrait cover, left.
    cover = state.cover_cache.get(game, g["cover_w"], g["cover_h"])
    cx = hero["x"] + g["margin"]
    cy = hero["y"] + (hero["h"] - g["cover_h"]) // 2
    if cover:
        state.screen.blit(cover, (cx, cy))
    # Text block, right of cover.
    tx = cx + g["cover_w"] + g["margin"]
    tw = hero["x"] + hero["w"] - tx - g["margin"]
    name = _truncate(state.font_title, game.get("name", ""), tw)
    state.screen.blit(state.font_title.render(name, True, state.text_color), (tx, cy))
    sub = _truncate(state.font_hint, (game.get("platform") or "").title(), tw)
    state.screen.blit(state.font_hint.render(sub, True, state.title_color),
                      (tx, cy + state.font_title.get_linesize() + 6))
    hint_y = cy + state.font_title.get_linesize() + state.font_hint.get_linesize() + 16
    play = state.font_hint.render("▶ Launch  (A)", True, state.highlight_color)
    state.screen.blit(play, (tx, hint_y))


def _draw_shelves(state, g):
    f = state.home_focus
    area = g["shelf_area"]
    prev_clip = state.screen.get_clip()
    state.screen.set_clip(pygame.Rect(area["x"], area["y"], area["w"], area["h"]))
    try:
        focus_shelf = f["shelf"] if f else 0
        # Scroll so the focused shelf is the first one drawn.
        y = area["y"] - focus_shelf * g["shelf_stride"]
        for si, shelf in enumerate(state.home_shelves or []):
            if y + g["shelf_stride"] >= area["y"] and y <= area["y"] + area["h"]:
                state.screen.blit(
                    state.font_category.render(shelf["title"], True, state.title_color),
                    (area["x"], y),
                )
                ty = y + g["shelf_label_h"]
                focus_col = f["col"] if (f and f["zone"] == "shelf" and f["shelf"] == si) else -1
                start = max(0, focus_col)  # keep focused tile visible by scrolling row
                x = area["x"]
                for ci in range(start, len(shelf["games"])):
                    if x > area["x"] + area["w"]:
                        break
                    cover = state.cover_cache.get(shelf["games"][ci], g["tile_w"], g["tile_h"])
                    if cover:
                        state.screen.blit(cover, (x, ty))
                    if ci == focus_col and f and f["zone"] == "shelf":
                        pygame.draw.rect(state.screen, state.highlight_color,
                                         (x - 3, ty - 3, g["tile_w"] + 6, g["tile_h"] + 6), 4)
                    x += g["tile_w"] + g["tile_gap"]
            y += g["shelf_stride"]
    finally:
        state.screen.set_clip(prev_clip)


def draw_home_view(state):
    g = state.home_geom
    if not g:
        rebuild_home(state)
        g = state.home_geom
    _draw_hero(state, g)
    _draw_shelves(state, g)
    _draw_rail(state, g)
