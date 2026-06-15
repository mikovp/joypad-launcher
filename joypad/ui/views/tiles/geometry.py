"""Tile grid geometry and layout."""

from joypad.config.settings import _TILE_SCALE_DEFAULT
from joypad.config.theme import parse_tile_scale


def compute_tile_grid(screen_w, screen_h, hint_line_h, tile_scale=1.0, title_line_h=None, footer_lines=2):
    """
    Square tile grid: N tiles per row, rows stacked below (scroll vertically).
    tile_scale enlarges tiles (fewer per row); set in theme.tile_scale or Settings.
    """
    scale = parse_tile_scale(tile_scale, 1.0)
    side_margin = max(24, screen_w // 40)
    gap = max(8, min(18, int(14 * scale)))
    top_banner = 36 + hint_line_h * 2
    bottom_hint = max(44, hint_line_h * max(2, footer_lines) + 24)
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
    max_cols_fit = max(2, (usable_w + gap) // (min_tile + gap))
    if cols > max_cols_fit:
        cols = max_cols_fit
        tile_size = (usable_w - gap * (cols - 1)) // cols
    max_tile = min(usable_w // 2, int(grid_h * 0.48), int(220 * scale))
    tile_size = max(min_tile, min(max_tile, tile_size))
    max_fit = (usable_w - gap * (cols - 1)) // cols
    if tile_size > max_fit:
        tile_size = max_fit
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
    _ts = parse_tile_scale((state.config.get("theme") or {}).get("tile_scale"), _TILE_SCALE_DEFAULT)
    state.tile_scale = _ts
    footer_lines = getattr(state, "footer_lines", None) or 2
    state.tile_geom = compute_tile_grid(
        state.w,
        state.h,
        state.hint_line_h,
        tile_scale=state.tile_scale,
        title_line_h=state.font_title.get_linesize(),
        footer_lines=footer_lines,
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


def tile_max_scroll_y(state):
    return max(0, state.tile_content_h - state.tile_geom["grid_h"])
