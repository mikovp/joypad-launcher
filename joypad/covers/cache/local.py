"""Local cover path resolution."""

import glob
import os
import re

from joypad.covers.cdn import nsp_cover_stems
from joypad.integrations.twitch import normalize_platform


def sanitize_filename(name):
    if not name:
        return "game"
    s = re.sub(r'[<>:"/\\|?*]', "_", str(name).strip())
    return s[:120] if s else "game"


def steam_cover_path(steam_dir, app_id):
    if not steam_dir or not app_id:
        return None
    cache = os.path.join(steam_dir, "appcache", "librarycache")
    if not os.path.isdir(cache):
        return None
    app_id = str(app_id)
    for name in (
        "%s_library_600x900.jpg" % app_id,
        "%s_library_hero.jpg" % app_id,
        "%s_header.jpg" % app_id,
        "%s_logo.png" % app_id,
    ):
        path = os.path.join(cache, name)
        if os.path.isfile(path):
            return path
    for pattern in ("%s_*.jpg" % app_id, "%s_*.png" % app_id):
        hits = sorted(glob.glob(os.path.join(cache, pattern)))
        if hits:
            return hits[0]
    sub = os.path.join(cache, app_id)
    if os.path.isdir(sub):
        for name in ("library_600x900.jpg", "library_hero.jpg", "header.jpg"):
            path = os.path.join(sub, name)
            if os.path.isfile(path):
                return path
    return None


def cover_candidates(game, covers_dir, steam_dir):
    """Ordered local paths to try (no network)."""
    platform = normalize_platform(game.get("platform"))
    name = game.get("name") or "Game"
    safe = sanitize_filename(name)
    paths = []

    if covers_dir and os.path.isdir(covers_dir):
        if platform == "steam" and game.get("steam_app_id"):
            aid = str(game["steam_app_id"])
            for stem in (aid, "steam_%s" % aid, safe):
                for ext in (".jpg", ".jpeg", ".png", ".webp"):
                    paths.append(os.path.join(covers_dir, stem + ext))
        elif platform == "epic" and game.get("exe_path"):
            base = os.path.splitext(os.path.basename(game["exe_path"]))[0]
            for stem in (sanitize_filename(base), safe, "epic_%s" % sanitize_filename(base)):
                for ext in (".jpg", ".jpeg", ".png", ".webp"):
                    paths.append(os.path.join(covers_dir, stem + ext))
        elif platform == "twitch" and game.get("nsp_path"):
            for stem in nsp_cover_stems(game):
                safe_stem = sanitize_filename(stem)
                for s in (stem, safe_stem):
                    for ext in (".jpg", ".jpeg", ".png", ".webp"):
                        paths.append(os.path.join(covers_dir, s + ext))
        elif platform != "twitch":
            for ext in (".jpg", ".jpeg", ".png", ".webp"):
                paths.append(os.path.join(covers_dir, safe + ext))

    if platform == "steam" and steam_dir and game.get("steam_app_id"):
        sp = steam_cover_path(steam_dir, game["steam_app_id"])
        if sp:
            paths.append(sp)

    seen = set()
    out = []
    for p in paths:
        key = p.lower()
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


def game_cache_key(game):
    platform = normalize_platform(game.get("platform"))
    if platform == "steam" and game.get("steam_app_id"):
        return ("steam", str(game["steam_app_id"]))
    if platform == "epic" and game.get("exe_path"):
        return ("epic", os.path.normcase(game["exe_path"]))
    if platform == "twitch" and game.get("nsp_path"):
        return ("twitch", os.path.normcase(game["nsp_path"]))
    return (platform, game.get("name") or "")
