"""Game watch target resolution for remap worker and launcher exit detection."""


import ntpath


def game_watch_targets(game):
    """Return (watch_exe, watch_dir) for keeping remap alive through Epic restarts."""
    if (game.get("platform") or "").lower() != "epic":
        return None, None
    exe_path = game.get("exe_path")
    if not exe_path:
        return None, None
    return ntpath.basename(exe_path), ntpath.dirname(exe_path)


def game_watch_title(game):
    """Window-title substring for Steam games (steam.exe exits before the game does)."""
    if (game.get("platform") or "").lower() != "steam":
        return None
    name = (game.get("name") or "").strip()
    return name if len(name) >= 4 else None
