"""Profile load/save and game assignment."""

import copy
import json
import os

from joypad.input.profiles.notation import ensure_chords, format_profile_notation, normalize_profile_notation
from joypad.input.profiles.paths import (
    default_profile_path,
    game_remap_key,
    get_assigned_profile_id,
    profile_file_path,
)


def _load_profile_raw(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Profile must be a JSON object")
    return data


def merge_profiles(base, override):
    """Merge override onto base (override wins).

    Top-level keys are merged; nested dict values (e.g. ``buttons``, ``triggers``)
    are merged one level deep, per key. Doubly-nested values (e.g. a ``chords``
    layer) are replaced wholesale, not recursed into — callers rely on
    ``ensure_chords`` to backfill any chord slots afterwards.
    """
    out = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            merged = dict(out[key])
            merged.update(value)
            out[key] = merged
        else:
            out[key] = copy.deepcopy(value) if isinstance(value, dict) else value
    return out


def load_default_profile(base_dir, config=None, name=None):
    """Load canonical defaults from input_profiles/default_wasd_mouse.json."""
    path = default_profile_path(config, base_dir)
    if not os.path.isfile(path):
        raise FileNotFoundError("Default profile missing: %s" % path)
    profile = normalize_profile_notation(_load_profile_raw(path))
    if name:
        profile = dict(profile)
        profile["name"] = name
    return profile


def prepare_profile(profile, base_dir, config=None):
    """Apply game profile over default template (defaults live in JSON only)."""
    default_path = default_profile_path(config, base_dir)
    if os.path.isfile(default_path):
        base = merge_profiles(
            normalize_profile_notation(_load_profile_raw(default_path)),
            profile,
        )
    else:
        base = dict(profile)
    ensure_chords(base)
    return base


def default_profile(name="Default", base_dir=None, config=None):
    """Backward-compatible alias; requires base_dir pointing at launcher root."""
    if not base_dir:
        raise ValueError("default_profile requires base_dir; use load_default_profile")
    return load_default_profile(base_dir, config, name=name)


def load_profile(path, base_dir=None, config=None):
    data = normalize_profile_notation(_load_profile_raw(path))
    if base_dir:
        if os.path.normcase(os.path.abspath(path)) == os.path.normcase(
            os.path.abspath(default_profile_path(config, base_dir))
        ):
            ensure_chords(data)
            return data
        return prepare_profile(data, base_dir, config)
    ensure_chords(data)
    return data


def save_profile(path, profile):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = format_profile_notation(profile)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")


def list_remapped_games(config, games):
    """Games that have an input_remap assignment."""
    out = []
    seen = set()
    for g in games:
        pid = get_assigned_profile_id(config, g)
        if not pid:
            continue
        key = game_remap_key(g)
        if key in seen:
            continue
        seen.add(key)
        out.append(g)
    return out


def assign_game_profile(config, game, profile_id, base_dir):
    """Assign profile to game; create default profile file if missing."""
    profile_id = str(profile_id).strip()
    if not profile_id:
        return
    path = profile_file_path(config, base_dir, profile_id)
    if not os.path.isfile(path):
        prof = load_default_profile(base_dir, config, name=game.get("name") or profile_id)
        save_profile(path, prof)
    key = game_remap_key(game)
    if not key:
        return
    assignments = config.setdefault("input_remap_games", {})
    assignments[key] = profile_id


def unassign_game(config, game):
    key = game_remap_key(game)
    if not key:
        return
    assignments = config.get("input_remap_games") or {}
    if key in assignments:
        del assignments[key]
        config["input_remap_games"] = assignments
