"""Twitch integration settings in config.json (legacy nsp_* keys supported)."""

from __future__ import annotations

from typing import Any


def _str_setting(config: dict[str, Any], primary: str, legacy: str) -> str:
    return (config.get(primary) or config.get(legacy) or "").strip()


def get_twitch_roms_folder(config: dict[str, Any]) -> str:
    return _str_setting(config, "twitch_roms_folder", "nsp_roms_folder")


def get_twitch_emulator_path(config: dict[str, Any]) -> str:
    return _str_setting(config, "twitch_emulator_path", "nsp_emulator_path")


def get_twitch_launch_args(config: dict[str, Any]) -> str:
    return _str_setting(config, "twitch_launch_args", "nsp_launch_args")


def get_twitch_use_windows_association(config: dict[str, Any]) -> bool | None:
    """None = use platform default (Windows: association on)."""
    if "twitch_use_windows_association" in config:
        return bool(config["twitch_use_windows_association"])
    if "nsp_use_windows_association" in config:
        return bool(config["nsp_use_windows_association"])
    return None


def set_twitch_use_windows_association(config: dict[str, Any], enabled: bool) -> None:
    config["twitch_use_windows_association"] = enabled


def get_twitch_fullscreen_args(default_args: dict[str, Any] | None) -> str:
    args = default_args or {}
    return (args.get("twitch") or args.get("nsp") or "").strip()


def ensure_twitch_config_keys(config: dict[str, Any]) -> None:
    """Mirror legacy nsp_* into twitch_* when only old keys are present."""
    pairs = (
        ("twitch_roms_folder", "nsp_roms_folder"),
        ("twitch_emulator_path", "nsp_emulator_path"),
        ("twitch_launch_args", "nsp_launch_args"),
        ("twitch_use_windows_association", "nsp_use_windows_association"),
    )
    for new_key, old_key in pairs:
        if new_key not in config and old_key in config:
            config[new_key] = config[old_key]

    fullscreen = config.get("fullscreen_args")
    if isinstance(fullscreen, dict) and "twitch" not in fullscreen and "nsp" in fullscreen:
        merged = dict(fullscreen)
        merged["twitch"] = fullscreen["nsp"]
        config["fullscreen_args"] = merged
