"""Build the ordered shelf list for the Home view."""


def build_home_shelves(tile_sections):
    """Source shelves (non-empty, original order) then an 'All' (A-Z) shelf."""
    shelves = []
    all_games = []
    for sec in tile_sections or []:
        games = sec.get("games") or []
        if not games:
            continue
        shelves.append({"title": sec["title"], "games": list(games)})
        all_games.extend(games)
    if not all_games:
        return []
    all_sorted = sorted(all_games, key=lambda g: (g.get("name") or "").lower())
    shelves.append({"title": "All", "games": all_sorted})
    return shelves
