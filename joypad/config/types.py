"""Typed shapes for config.json (gradual typing; runtime values remain plain dicts)."""

from __future__ import annotations

from typing import Any, TypedDict


class ThemeConfig(TypedDict, total=False):
    background: str
    cursor: str
    text: str
    title: str
    font_size_title: int
    font_size_list: int
    font_size_hint: int
    font_bold_title: bool
    font_bold_list: bool
    background_image: str
    auto_font_boost_low_res: bool
    auto_font_boost_ref_height: int
    auto_font_boost_max: float
    font_scale: float
    ui_mode: str
    tile_scale: float
    covers_folder: str
    cdn_covers: bool
    cdn_cache_folder: str
    rawg_api_key: str


class FullscreenArgs(TypedDict, total=False):
    steam: str
    epic: str
    twitch: str
    nsp: str  # legacy alias for twitch


class InputRemapConfig(TypedDict, total=False):
    profiles_dir: str
    log: bool


class DdcciConfig(TypedDict, total=False):
    power_off_on_start: bool
    delay_ms: int
    log: bool


class GameEntry(TypedDict, total=False):
    name: str
    platform: str
    steam_app_id: str
    exe_path: str
    nsp_path: str
    nsp_filename: str
    launch_args: str
    system_action: str


class LauncherConfig(TypedDict, total=False):
    steam_path: str
    steam_start_args: str
    auto_scan: bool
    theme: ThemeConfig
    twitch_roms_folder: str
    twitch_use_windows_association: bool
    twitch_emulator_path: str
    twitch_launch_args: str
    nsp_roms_folder: str  # legacy
    nsp_use_windows_association: bool
    nsp_emulator_path: str
    nsp_launch_args: str
    fullscreen_args: FullscreenArgs
    steam_skip_restore_ids: list[int]
    input_remap: InputRemapConfig
    input_remap_games: dict[str, str]
    ddcci: DdcciConfig
    rawg_api_key: str
    games: list[GameEntry | dict[str, Any]]
