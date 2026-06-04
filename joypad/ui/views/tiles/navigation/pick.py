"""Tile pick index and layout lookups."""


def tile_selected_game(state):
    if not state.tile_all_games:
        return None
    return state.tile_all_games[min(state.tile_pick, len(state.tile_all_games) - 1)]


def tile_pick_location(state, pick):
    off = 0
    for si, sec in enumerate(state.tile_sections):
        n = len(sec["games"])
        if pick < off + n:
            return si, pick - off
        off += n
    return 0, 0


def global_pick(state, section_i, local_i):
    off = 0
    for j in range(section_i):
        off += len(state.tile_sections[j]["games"])
    return off + local_i


def tile_entry_for_pick(state, pick):
    for ent in state.tile_layout:
        if ent.get("kind") == "tile" and ent.get("game_index") == pick:
            return ent
    return None


def section_header_y_for_pick(state, pick):
    header_y = 0
    for ent in state.tile_layout:
        if ent.get("kind") == "header":
            header_y = ent["y"]
        if ent.get("kind") == "tile" and ent.get("game_index") == pick:
            return header_y
    return 0
