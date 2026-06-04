"""Game watch target resolution for remap worker."""

import os


def game_watch_targets(game):
    """Return (watch_exe, watch_dir) for keeping remap alive through Epic restarts."""
    if (game.get("platform") or "").lower() != "epic":
        return None, None
    exe_path = game.get("exe_path")
    if not exe_path:
        return None, None
    return os.path.basename(exe_path), os.path.dirname(os.path.abspath(exe_path))
