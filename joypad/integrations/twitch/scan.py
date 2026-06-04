"""Twitch (.nsp ROM) library scan."""

import os

from joypad.integrations.twitch.platform import PLATFORM


def scan_twitch_games(root_folder):
    """
    Recursively find *.nsp under root_folder (including UNC \\\\server\\share paths).
    Returns entries with platform \"twitch\" and nsp_path / nsp_filename fields.
    """
    root_folder = os.path.normpath((root_folder or "").strip())
    if not root_folder or not os.path.isdir(root_folder):
        return []
    games = []
    for dirpath, _dirnames, filenames in os.walk(root_folder):
        for fn in filenames:
            if not fn.lower().endswith(".nsp"):
                continue
            full = os.path.join(dirpath, fn)
            stem = os.path.splitext(fn)[0]
            try:
                rel_dir = os.path.relpath(dirpath, root_folder)
            except ValueError:
                rel_dir = ""
            if rel_dir and rel_dir != ".":
                display = "%s / %s" % (rel_dir.replace(os.sep, " / "), stem)
            else:
                display = stem
            games.append({
                "name": display,
                "platform": PLATFORM,
                "nsp_path": full,
                "nsp_filename": stem,
            })
    games.sort(key=lambda g: g["name"].lower())
    return games


scan_nsp_games = scan_twitch_games
