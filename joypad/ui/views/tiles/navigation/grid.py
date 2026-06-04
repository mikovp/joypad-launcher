"""Tile grid movement within and across sections."""

from joypad.ui.views.tiles.navigation.pick import global_pick, tile_pick_location
from joypad.ui.views.tiles.navigation.scroll import tile_snap_scroll


def tile_step_section(state, sec_i, delta, col):
    nsec = len(state.tile_sections)
    for _ in range(nsec):
        sec_i = (sec_i + delta) % nsec
        games = state.tile_sections[sec_i]["games"]
        if games:
            return sec_i, min(col, len(games) - 1)
    return sec_i, 0


def tile_below(state, local, row, col, cols, n, max_row):
    if local >= n - 1:
        return None
    if row >= max_row:
        return None
    nxt = (row + 1) * cols + col
    if nxt < n:
        return nxt
    fallback = min(n - 1, (row + 1) * cols + (cols - 1))
    return fallback if fallback > local else None


def tile_above(state, local, row, col, cols, n):
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
    sec_i, local = tile_pick_location(state, state.tile_pick)
    games = state.tile_sections[sec_i]["games"]
    n = len(games)
    if n == 0:
        return
    col = local % cols
    row = local // cols
    max_row = (n - 1) // cols

    if dy < 0:
        above = tile_above(state, local, row, col, cols, n)
        if above is not None:
            local = above
        elif sec_i > 0:
            sec_i, local = tile_step_section(state, sec_i, -1, col)
        else:
            return
    elif dy > 0:
        below = tile_below(state, local, row, col, cols, n, max_row)
        if below is not None:
            local = below
        else:
            new_sec, new_local = tile_step_section(state, sec_i, 1, col)
            if new_sec == sec_i and state.tile_sections[sec_i]["games"]:
                return
            sec_i, local = new_sec, new_local
    if dx < 0:
        if col > 0:
            local = row * cols + (col - 1)
        elif row > 0:
            local = (row - 1) * cols + min(cols - 1, n - 1 - (row - 1) * cols)
        elif sec_i > 0:
            sec_i, local = tile_step_section(state, sec_i, -1, col)
        else:
            return
    elif dx > 0:
        if col < cols - 1 and row * cols + col + 1 < n:
            local = row * cols + col + 1
        elif row < max_row:
            nxt = (row + 1) * cols
            local = min(n - 1, nxt)
        else:
            new_sec, new_local = tile_step_section(state, sec_i, 1, col)
            if new_sec == sec_i:
                return
            sec_i, local = new_sec, new_local

    if local >= n:
        local = n - 1
    state.tile_pick = global_pick(state, sec_i, local)
    state.tile_snap_scroll = True
    tile_snap_scroll(state)
