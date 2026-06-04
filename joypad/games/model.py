"""Game categorization and tile/list data-structure helpers."""

import os


def _game_sections(games):
    """
    Group games by platform. Order: Steam → Epic → Switch → Other.
    Returns [(section_title, [game, ...]), ...]; empty sections omitted.
    """
    buckets = {"steam": [], "epic": [], "nsp": [], "_other": []}
    for g in games:
        p = (g.get("platform") or "").lower()
        if p == "steam":
            buckets["steam"].append(g)
        elif p == "epic":
            buckets["epic"].append(g)
        elif p == "nsp":
            buckets["nsp"].append(g)
        else:
            buckets["_other"].append(g)

    sections = [
        ("steam", "Steam"),
        ("epic", "Epic Games"),
        ("nsp", "Nintendo Switch"),
    ]
    out = []
    for key, title in sections:
        lst = buckets[key]
        if lst:
            out.append((title, lst))
    other = buckets["_other"]
    if other:
        out.append(("Other", other))
    return out


def build_categorized_game_list(games):
    """Flat list with category headers and game rows (list UI)."""
    items = []
    for title, lst in _game_sections(games):
        items.append({"kind": "header", "title": title})
        for game in lst:
            items.append({"kind": "game", "game": game})
    return items


def build_tile_sections(games):
    """Sections for tile grid UI: [{title, games}, ...]."""
    return [{"title": title, "games": lst} for title, lst in _game_sections(games)]


def tile_selection_title(game):
    """One-line label above the grid (game name or .nsp filename)."""
    if not game:
        return "Untitled"
    if (game.get("platform") or "").lower() == "nsp":
        return (
            game.get("nsp_filename")
            or os.path.splitext(os.path.basename(game.get("nsp_path") or ""))[0]
            or game.get("name", "Untitled")
        )
    return game.get("name", "Untitled")
