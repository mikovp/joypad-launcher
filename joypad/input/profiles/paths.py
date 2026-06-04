"""Profile paths and game assignment keys."""

import os

from joypad.input.constants import DEFAULT_PROFILE_ID, PROFILES_DIR_DEFAULT


def remap_settings(config):
    return (config or {}).get("input_remap") or {}


def profiles_dir(config, base_dir):
    folder = remap_settings(config).get("profiles_dir") or PROFILES_DIR_DEFAULT
    if os.path.isabs(folder):
        return folder
    return os.path.join(base_dir, folder)


def profile_file_path(config, base_dir, profile_id):
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(profile_id))
    return os.path.join(profiles_dir(config, base_dir), "%s.json" % safe)


def default_profile_path(config, base_dir):
    return profile_file_path(config, base_dir, DEFAULT_PROFILE_ID)


def game_remap_key(game):
    """Stable key for input_remap_games assignments."""
    from joypad.integrations.twitch import normalize_platform

    platform = normalize_platform(game.get("platform"))
    if platform == "steam" and game.get("steam_app_id"):
        return "steam:%s" % game["steam_app_id"]
    if platform == "epic" and game.get("exe_path"):
        return "epic:%s" % os.path.normcase(os.path.normpath(game["exe_path"]))
    if platform == "twitch" and game.get("nsp_path"):
        return "twitch:%s" % os.path.normcase(os.path.normpath(game["nsp_path"]))
    name = (game.get("name") or "").strip()
    return "name:%s" % name if name else ""


def _lookup_remap_assignment(assignments, key):
    if not key:
        return None
    val = assignments.get(key)
    if val:
        return val
    if key.startswith("twitch:"):
        return assignments.get("nsp:" + key[7:])
    return None


def get_assigned_profile_id(config, game):
    inline = game.get("input_remap")
    if inline:
        return str(inline).strip()
    key = game_remap_key(game)
    if not key:
        return None
    assignments = config.get("input_remap_games") or {}
    val = _lookup_remap_assignment(assignments, key)
    return str(val).strip() if val else None


def resolve_profile_path(config, game, base_dir):
    pid = get_assigned_profile_id(config, game)
    if not pid:
        return None
    path = profile_file_path(config, base_dir, pid)
    return path if os.path.isfile(path) else None


def suggest_profile_id(game):
    name = (game.get("name") or "game").strip()
    slug = "".join(c.lower() if c.isalnum() else "_" for c in name).strip("_")
    return slug[:32] or "profile"
