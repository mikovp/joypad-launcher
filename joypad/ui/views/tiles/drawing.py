"""Tile view pygame rendering."""

import pygame

from joypad.games.model import tile_selection_title
from joypad.ui.views.tiles.geometry import tile_max_scroll_y
from joypad.ui.views.tiles.navigation import _tile_entry_for_pick, tile_selected_game


def _truncate_to_width(state, font, text, max_w):
    t = (text or "").strip() or "Untitled"
    if font.size(t)[0] <= max_w:
        return t
    ell = "…"
    for n in range(len(t), 0, -1):
        trial = t[:n] + ell
        if font.size(trial)[0] <= max_w:
            return trial
    return ell


def draw_tiles_view(state):
    if not state.tile_sections:
        return
    g = tile_selected_game(state)
    gname = tile_selection_title(g)
    tg = state.tile_geom
    sm = tg["side_margin"]
    tw, th = tg["tile_w"], tg["tile_h"]

    title_y = tg["top_banner"]
    title_surf = state.font_title.render(
        _truncate_to_width(state, state.font_title, gname, state.w - 2 * sm), True, state.text_color
    )
    state.screen.blit(title_surf, (sm, title_y))

    grid_y0 = tg["grid_top"]
    prev_clip = state.screen.get_clip()
    clip_rect = pygame.Rect(0, grid_y0, state.w, tg["grid_h"])
    state.screen.set_clip(clip_rect)
    try:
        for ent in state.tile_layout:
            if ent["kind"] != "tile":
                continue
            sy = grid_y0 + ent["y"] - state.tile_scroll_y
            eh = ent["h"] + state.font_hint.get_linesize() + 8
            if sy + eh < grid_y0 or sy > grid_y0 + tg["grid_h"]:
                continue
            x, y = ent["x"], sy
            game = ent["game"]
            img = state.cover_cache.get(game, tw, th)
            if img:
                state.screen.blit(img, (x, y))
            else:
                pygame.draw.rect(state.screen, (50, 50, 60), (x, y, tw, th))
            label = _truncate_to_width(state, state.font_hint, game.get("name", ""), tw)
            lbl = state.font_hint.render(label, True, state.text_color)
            state.screen.blit(lbl, (x, y + th + 2))

        for ent in state.tile_layout:
            if ent["kind"] not in ("header", "empty"):
                continue
            sy = grid_y0 + ent["y"] - state.tile_scroll_y
            if ent["kind"] == "header":
                if sy + tg["section_header_h"] < grid_y0 or sy > grid_y0 + tg["grid_h"]:
                    continue
                text = state.font_category.render(ent["title"], True, state.title_color)
                state.screen.blit(text, (sm, sy))
            else:
                if sy + state.font_hint.get_linesize() < grid_y0 or sy > grid_y0 + tg["grid_h"]:
                    continue
                msg = state.font_hint.render("(no games)", True, state.title_color)
                state.screen.blit(msg, (sm + 8, sy))

        sel_ent = _tile_entry_for_pick(state, state.tile_pick)
        if sel_ent:
            sy = grid_y0 + sel_ent["y"] - state.tile_scroll_y
            x = sel_ent["x"]
            th_sel = sel_ent["h"]
            tw_sel = sel_ent["w"]
            eh = th_sel + state.font_hint.get_linesize() + 8
            if not (sy + eh < grid_y0 or sy > grid_y0 + tg["grid_h"]):
                sel_pad = max(5, min(10, tw_sel // 12))
                sel_bw = max(5, min(8, tw_sel // 20))
                pad_top = 2 if sel_ent.get("first_row") else sel_pad
                pygame.draw.rect(
                    state.screen,
                    state.highlight_color,
                    (
                        x - sel_pad,
                        sy - pad_top,
                        tw_sel + 2 * sel_pad,
                        th_sel + pad_top + sel_pad,
                    ),
                    sel_bw,
                )
    finally:
        state.screen.set_clip(prev_clip)

    max_sy = tile_max_scroll_y(state)
    if max_sy > 0:
        if state.tile_scroll_y > 0:
            state.screen.blit(state.font_list.render(" ▲", True, state.title_color), (state.w - 50, grid_y0 + 4))
        if state.tile_scroll_y < max_sy:
            state.screen.blit(
                state.font_list.render(" ▼", True, state.title_color),
                (state.w - 50, grid_y0 + tg["grid_h"] - state.font_list.get_linesize() - 4),
            )
