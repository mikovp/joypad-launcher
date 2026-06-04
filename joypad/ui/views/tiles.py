"""Tile-view rendering and navigation for the launcher.

Module-level extraction of the tile-cluster functions formerly nested in
run_launcher. Each function takes ``state`` (an AppState) as its first argument;
read-only session data (w, h, screen, tile_sections, cover_cache, config) is
carried on ``state`` as well.
"""

import pygame

from joypad.config.theme import _parse_tile_scale
from joypad.config.settings import _TILE_SCALE_DEFAULT
from joypad.games.model import _tile_selection_title


def compute_tile_grid(screen_w, screen_h, hint_line_h, tile_scale=1.0, title_line_h=None):
    """
    Square tile grid: N tiles per row, rows stacked below (scroll vertically).
    tile_scale enlarges tiles (fewer per row); set in theme.tile_scale or Settings.
    """
    scale = _parse_tile_scale(tile_scale, 1.0)
    side_margin = max(24, screen_w // 40)
    gap = max(8, min(18, int(14 * scale)))
    top_banner = 36 + hint_line_h * 2
    bottom_hint = max(44, hint_line_h + 24)
    label_h = max(28, hint_line_h + 8)
    selection_h = (title_line_h or label_h) + 8
    grid_top = top_banner + selection_h + gap
    grid_h = max(120, screen_h - grid_top - bottom_hint)
    usable_w = screen_w - 2 * side_margin

    target_tile = int(88 * scale)
    target_tile = min(target_tile, usable_w // 2, max(96, int(grid_h * 0.42)))
    cols = max(2, (usable_w + gap) // (target_tile + gap))
    tile_size = (usable_w - gap * (cols - 1)) // cols
    min_tile = int(72 * scale)
    while tile_size < int(target_tile * 0.92) and cols > 2:
        cols -= 1
        tile_size = (usable_w - gap * (cols - 1)) // cols
    max_tile = min(usable_w // 2, int(grid_h * 0.48), int(220 * scale))
    tile_size = max(min_tile, min(max_tile, tile_size))
    grid_content_w = cols * tile_size + gap * max(0, cols - 1)
    grid_offset_x = side_margin + max(0, (usable_w - grid_content_w) // 2)

    return {
        "cols": cols,
        "tile_w": tile_size,
        "tile_h": tile_size,
        "gap": gap,
        "selection_h": selection_h,
        "grid_top": grid_top,
        "grid_h": grid_h,
        "side_margin": side_margin,
        "grid_offset_x": grid_offset_x,
        "label_h": label_h,
        "top_banner": top_banner,
        "bottom_hint": bottom_hint,
        "section_header_h": label_h,
        "tile_scale": scale,
    }


def rebuild_tile_geometry(state):
    _ts = _parse_tile_scale((state.config.get("theme") or {}).get("tile_scale"), _TILE_SCALE_DEFAULT)
    state.tile_scale = _ts
    state.tile_geom = compute_tile_grid(
        state.w, state.h, state.hint_line_h, tile_scale=state.tile_scale, title_line_h=state.font_title.get_linesize()
    )
    rebuild_tile_layout(state)


def tile_row_stride(state):
    return state.tile_geom["tile_h"] + state.tile_geom["gap"] + state.font_hint.get_linesize() + 4


def rebuild_tile_layout(state):
    state.tile_all_games = []
    layout = []
    tg = state.tile_geom
    cols = tg["cols"]
    tw, th = tg["tile_w"], tg["tile_h"]
    gap = tg["gap"]
    ox = tg["grid_offset_x"]
    stride = tile_row_stride(state)
    y = 0
    header_h = tg["section_header_h"]
    section_tile_gap = gap + state.font_hint.get_linesize() // 2
    for sec in state.tile_sections:
        layout.append({"kind": "header", "y": y, "title": sec["title"]})
        y += header_h + section_tile_gap
        games = sec["games"]
        if not games:
            layout.append({"kind": "empty", "y": y, "title": sec["title"]})
            y += state.font_hint.get_linesize() + gap
            continue
        rows = (len(games) + cols - 1) // cols
        for i, game in enumerate(games):
            gi = len(state.tile_all_games)
            state.tile_all_games.append(game)
            row, col = divmod(i, cols)
            layout.append({
                "kind": "tile",
                "y": y + row * stride,
                "x": ox + col * (tw + gap),
                "w": tw,
                "h": th,
                "game_index": gi,
                "game": game,
                "first_row": row == 0,
            })
        y += rows * stride + gap * 2
    state.tile_layout = layout
    state.tile_content_h = y


def tile_selected_game(state):
    if not state.tile_all_games:
        return None
    return state.tile_all_games[min(state.tile_pick, len(state.tile_all_games) - 1)]


def _tile_pick_location(state, pick):
    """Returns (section_index, local_index) for global pick."""
    off = 0
    for si, sec in enumerate(state.tile_sections):
        n = len(sec["games"])
        if pick < off + n:
            return si, pick - off
        off += n
    return 0, 0


def _global_pick(state, section_i, local_i):
    off = 0
    for j in range(section_i):
        off += len(state.tile_sections[j]["games"])
    return off + local_i


def _tile_entry_for_pick(state, pick):
    for ent in state.tile_layout:
        if ent.get("kind") == "tile" and ent.get("game_index") == pick:
            return ent
    return None


def _section_header_y_for_pick(state, pick):
    """Content Y of the section header above the selected tile."""
    header_y = 0
    for ent in state.tile_layout:
        if ent.get("kind") == "header":
            header_y = ent["y"]
        if ent.get("kind") == "tile" and ent.get("game_index") == pick:
            return header_y
    return 0


def tile_max_scroll_y(state):
    return max(0, state.tile_content_h - state.tile_geom["grid_h"])


def _tile_snap_scroll(state):
    ent = _tile_entry_for_pick(state, state.tile_pick)
    if not ent:
        return
    header_y = _section_header_y_for_pick(state, state.tile_pick)
    top = ent["y"]
    bot = top + ent["h"] + state.font_hint.get_linesize() + 8
    view = state.tile_geom["grid_h"]
    stride = max(1, tile_row_stride(state))
    rows_from_header = (top - header_y) // stride if top > header_y else 0
    if top < state.tile_scroll_y:
        # First row(s) of a section: keep section title visible (scroll = header_y, usually 0).
        if rows_from_header <= 1:
            state.tile_scroll_y = header_y
        else:
            state.tile_scroll_y = top
    elif bot > state.tile_scroll_y + view:
        state.tile_scroll_y = bot - view
    state.tile_scroll_y = max(0, min(state.tile_scroll_y, tile_max_scroll_y(state)))


def _tile_step_section(state, sec_i, delta, col):
    """Next/prev non-empty library; land on same column when possible."""
    nsec = len(state.tile_sections)
    for _ in range(nsec):
        sec_i = (sec_i + delta) % nsec
        games = state.tile_sections[sec_i]["games"]
        if games:
            return sec_i, min(col, len(games) - 1)
    return sec_i, 0


def _tile_below(state, local, row, col, cols, n, max_row):
    if local >= n - 1:
        return None
    if row >= max_row:
        return None
    nxt = (row + 1) * cols + col
    if nxt < n:
        return nxt
    # Short last row: no tile in this column — take rightmost tile on row below.
    fallback = min(n - 1, (row + 1) * cols + (cols - 1))
    return fallback if fallback > local else None


def _tile_above(state, local, row, col, cols, n):
    if row <= 0:
        return None
    nxt = (row - 1) * cols + col
    if nxt < n:
        return nxt
    fallback = (row - 1) * cols + min(cols - 1, n - 1 - (row - 1) * cols)
    return fallback if fallback < local else None


def tile_move(state, dx, dy):
    if not state.tile_all_games:
        return
    cols = state.tile_geom["cols"]
    sec_i, local = _tile_pick_location(state, state.tile_pick)
    games = state.tile_sections[sec_i]["games"]
    n = len(games)
    if n == 0:
        return
    col = local % cols
    row = local // cols
    max_row = (n - 1) // cols

    if dy < 0:
        above = _tile_above(state, local, row, col, cols, n)
        if above is not None:
            local = above
        elif sec_i > 0:
            sec_i, local = _tile_step_section(state, sec_i, -1, col)
        else:
            return
    elif dy > 0:
        below = _tile_below(state, local, row, col, cols, n, max_row)
        if below is not None:
            local = below
        else:
            new_sec, new_local = _tile_step_section(state, sec_i, 1, col)
            if new_sec == sec_i and state.tile_sections[sec_i]["games"]:
                return
            sec_i, local = new_sec, new_local
    if dx < 0:
        if col > 0:
            local = row * cols + (col - 1)
        elif row > 0:
            local = (row - 1) * cols + min(cols - 1, n - 1 - (row - 1) * cols)
        elif sec_i > 0:
            sec_i, local = _tile_step_section(state, sec_i, -1, col)
        else:
            return
    elif dx > 0:
        if col < cols - 1 and row * cols + col + 1 < n:
            local = row * cols + col + 1
        elif row < max_row:
            nxt = (row + 1) * cols
            local = min(n - 1, nxt)
        else:
            new_sec, new_local = _tile_step_section(state, sec_i, 1, col)
            if new_sec == sec_i:
                return
            sec_i, local = new_sec, new_local

    if local >= n:
        local = n - 1
    state.tile_pick = _global_pick(state, sec_i, local)
    state.tile_snap_scroll = True
    _tile_snap_scroll(state)


def tile_page_scroll(state, delta_pages):
    if delta_pages == 0:
        return
    step = max(state.tile_geom["grid_h"] // 2, tile_row_stride(state) * 2)
    state.tile_scroll_y = max(
        0,
        min(tile_max_scroll_y(state), state.tile_scroll_y + delta_pages * step),
    )
    state.tile_snap_scroll = False


def tile_section_jump(state, delta):
    """LB/RB on first tile of a section: jump to first tile of prev/next library."""
    if not state.tile_sections or delta == 0:
        return
    sec_i, _local = _tile_pick_location(state, state.tile_pick)
    nsec = len(state.tile_sections)
    for _ in range(nsec):
        sec_i = (sec_i + delta) % nsec
        if state.tile_sections[sec_i]["games"]:
            break
    state.tile_pick = _global_pick(state, sec_i, 0)
    state.tile_scroll_y = _section_header_y_for_pick(state, state.tile_pick)
    state.tile_snap_scroll = True
    _tile_snap_scroll(state)


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
    gname = _tile_selection_title(g)
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

        # Section titles above tiles (covers are drawn first).
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

        # Selection frame on top (no upward bleed into category title).
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
