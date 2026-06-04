import copy
import json
import os

from joypad.input.constants import (
    _BTN_PROFILE_ALIASES,
    _FACE_PROFILE_ALIASES,
    BTN_A,
    BTN_B,
    BTN_BACK,
    BTN_FACE,
    BTN_LB,
    BTN_PROFILE_NAMES,
    BTN_RB,
    BTN_START,
    BTN_X,
    BTN_Y,
    DEFAULT_PROFILE_ID,
    FACE_PROFILE_NAMES,
    PROFILES_DIR_DEFAULT,
    SLOT_BINDING_MODES,
)


def parse_profile_btn_key(key):
    """Profile key -> internal index string ('0'–'7'). Accepts a/b/x/y/lb/rb/back/start."""
    if key is None:
        return None
    alias = str(key).strip().lower()
    idx = _BTN_PROFILE_ALIASES.get(alias)
    return str(idx) if idx is not None else alias


def parse_profile_face_key(key):
    """Chord face key -> internal index string ('0'–'3'). Accepts a/b/x/y."""
    if key is None:
        return None
    alias = str(key).strip().lower()
    idx = _FACE_PROFILE_ALIASES.get(alias)
    return str(idx) if idx is not None else alias


def parse_slot_binding(value, default_mode="hold"):
    """Parse a binding slot: string or {binding, mode}. mode: hold | toggle."""
    if isinstance(value, dict):
        binding = value.get("binding") or value.get("bind") or "none"
        mode = str(value.get("mode") or default_mode).lower()
        if mode not in SLOT_BINDING_MODES:
            mode = default_mode
        return binding, mode
    if not value:
        return "none", default_mode
    return str(value), default_mode


def format_slot_binding(binding, mode="hold"):
    """Serialize binding for profile JSON (object when mode is toggle)."""
    if mode == "toggle":
        return {"binding": binding, "mode": "toggle"}
    return binding


def normalize_stick_clicks(section):
    if not section:
        return {}
    out = {}
    for key, value in section.items():
        binding, mode = parse_slot_binding(value)
        if mode == "toggle":
            out[key] = {"binding": binding, "mode": "toggle"}
        else:
            out[key] = binding
    return out


def format_stick_clicks(section):
    if not section:
        return {}
    out = {}
    for key in ("left", "right"):
        if key not in section:
            continue
        binding, mode = parse_slot_binding(section[key])
        out[key] = format_slot_binding(binding, mode)
    for key, value in section.items():
        if key not in out:
            binding, mode = parse_slot_binding(value)
            out[key] = format_slot_binding(binding, mode)
    return out


def normalize_button_map(section):
    if not section:
        return {}
    out = {}
    for key, value in section.items():
        norm = parse_profile_btn_key(key)
        if norm is not None:
            out[norm] = value
    return out


def normalize_button_holds(section):
    if not section:
        return {}
    out = {}
    for key, value in section.items():
        norm = parse_profile_btn_key(key)
        if norm is not None and isinstance(value, dict):
            out[norm] = value
    return out


def normalize_chords_map(chords):
    if not chords:
        return default_chords()
    out = {}
    for mod in ("lb", "rb"):
        layer = chords.get(mod) or {}
        out[mod] = {}
        for key, value in layer.items():
            norm = parse_profile_face_key(key)
            if norm is not None:
                out[mod][norm] = value
    return out


def normalize_profile_notation(profile):
    """Convert readable profile keys to internal numeric indices."""
    if not profile:
        return profile
    out = copy.deepcopy(profile)
    if "buttons" in out:
        out["buttons"] = normalize_button_map(out["buttons"])
    if "button_holds" in out:
        out["button_holds"] = normalize_button_holds(out["button_holds"])
    if "chords" in out:
        out["chords"] = normalize_chords_map(out["chords"])
    if "stick_clicks" in out:
        out["stick_clicks"] = normalize_stick_clicks(out["stick_clicks"])
    return out


def format_button_map(section):
    if not section:
        return {}
    order = (BTN_A, BTN_B, BTN_X, BTN_Y, BTN_LB, BTN_RB, BTN_BACK, BTN_START)
    out = {}
    for idx in order:
        key = str(idx)
        if key in section:
            out[BTN_PROFILE_NAMES[idx]] = section[key]
    for key, value in section.items():
        try:
            idx = int(key)
        except (TypeError, ValueError):
            out[str(key)] = value
            continue
        name = BTN_PROFILE_NAMES.get(idx)
        if name and name not in out:
            out[name] = value
    return out


def format_button_holds(section):
    if not section:
        return {}
    out = {}
    for key, value in section.items():
        try:
            idx = int(key)
            out[BTN_PROFILE_NAMES.get(idx, key)] = value
        except (TypeError, ValueError):
            out[str(key)] = value
    return out


def format_chords_map(chords):
    chords = chords or default_chords()
    out = {}
    for mod in ("lb", "rb"):
        layer = chords.get(mod) or {}
        out[mod] = {}
        for idx in BTN_FACE:
            key = str(idx)
            out[mod][FACE_PROFILE_NAMES[idx]] = layer.get(key, "none")
    return out


def format_profile_notation(profile):
    """Write profiles with readable button names (a, b, x, y, lb, …)."""
    out = copy.deepcopy(profile)
    if "buttons" in out:
        out["buttons"] = format_button_map(out["buttons"])
    if "button_holds" in out:
        out["button_holds"] = format_button_holds(out["button_holds"])
    if "chords" in out:
        out["chords"] = format_chords_map(out["chords"])
    if "stick_clicks" in out:
        out["stick_clicks"] = format_stick_clicks(out["stick_clicks"])
    return out


def game_remap_key(game):
    """Stable key for input_remap_games assignments."""
    platform = (game.get("platform") or "").lower()
    if platform == "steam" and game.get("steam_app_id"):
        return "steam:%s" % game["steam_app_id"]
    if platform == "epic" and game.get("exe_path"):
        return "epic:%s" % os.path.normcase(os.path.normpath(game["exe_path"]))
    if platform == "nsp" and game.get("nsp_path"):
        return "nsp:%s" % os.path.normcase(os.path.normpath(game["nsp_path"]))
    name = (game.get("name") or "").strip()
    return "name:%s" % name if name else ""


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


def get_assigned_profile_id(config, game):
    inline = game.get("input_remap")
    if inline:
        return str(inline).strip()
    key = game_remap_key(game)
    if not key:
        return None
    assignments = config.get("input_remap_games") or {}
    val = assignments.get(key)
    return str(val).strip() if val else None


def resolve_profile_path(config, game, base_dir):
    pid = get_assigned_profile_id(config, game)
    if not pid:
        return None
    path = profile_file_path(config, base_dir, pid)
    return path if os.path.isfile(path) else None


def default_chords():
    return {
        "lb": {str(i): "none" for i in BTN_FACE},
        "rb": {str(i): "none" for i in BTN_FACE},
    }


def ensure_chords(profile):
    chords = profile.setdefault("chords", default_chords())
    for mod in ("lb", "rb"):
        layer = chords.setdefault(mod, {})
        for i in BTN_FACE:
            layer.setdefault(str(i), "none")
    return chords


def parse_chord_slot_key(key):
    """'lb_0' -> ('lb', '0') or None."""
    if not key or "_" not in key:
        return None
    mod, face = key.split("_", 1)
    if mod in ("lb", "rb") and face in {str(i) for i in BTN_FACE}:
        return mod, face
    return None


def default_profile_path(config, base_dir):
    return profile_file_path(config, base_dir, DEFAULT_PROFILE_ID)


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


def suggest_profile_id(game):
    name = (game.get("name") or "game").strip()
    slug = "".join(c.lower() if c.isalnum() else "_" for c in name).strip("_")
    return slug[:32] or "profile"
