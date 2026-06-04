"""Input remap profile I/O, notation, and game assignments."""

from joypad.input.profiles.io import (
    assign_game_profile,
    default_profile,
    list_remapped_games,
    load_default_profile,
    load_profile,
    merge_profiles,
    prepare_profile,
    save_profile,
    unassign_game,
)
from joypad.input.profiles.notation import (
    default_chords,
    ensure_chords,
    format_profile_notation,
    normalize_profile_notation,
    parse_chord_slot_key,
    parse_profile_btn_key,
    parse_profile_face_key,
)
from joypad.input.profiles.paths import (
    default_profile_path,
    game_remap_key,
    get_assigned_profile_id,
    profile_file_path,
    profiles_dir,
    remap_settings,
    resolve_profile_path,
    suggest_profile_id,
)
from joypad.input.profiles.slots import format_slot_binding, parse_slot_binding

__all__ = [
    "assign_game_profile",
    "default_chords",
    "default_profile",
    "default_profile_path",
    "ensure_chords",
    "format_profile_notation",
    "format_slot_binding",
    "game_remap_key",
    "get_assigned_profile_id",
    "list_remapped_games",
    "load_default_profile",
    "load_profile",
    "merge_profiles",
    "normalize_profile_notation",
    "parse_chord_slot_key",
    "parse_profile_btn_key",
    "parse_profile_face_key",
    "parse_slot_binding",
    "prepare_profile",
    "profile_file_path",
    "profiles_dir",
    "remap_settings",
    "resolve_profile_path",
    "save_profile",
    "suggest_profile_id",
    "unassign_game",
]
