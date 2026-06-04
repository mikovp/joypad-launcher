"""Start game processes by platform."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Any

from joypad.config.twitch import (
    get_twitch_emulator_path,
    get_twitch_fullscreen_args,
    get_twitch_launch_args,
    get_twitch_use_windows_association,
)
from joypad.integrations import launch_epic_game, launch_steam_game, launch_twitch_game, normalize_platform
from joypad.launch.system import perform_system_action


@dataclass
class GameStart:
    process: Any
    platform: str
    skip_restore: bool = False


def start_game_process(g, state, *, steam_path, default_args, steam_skip_restore_ids):
    """
    Launch game ``g`` and return a GameStart, or None if launch was skipped.
    Returns the string ``"exit"`` when the launcher should quit (system action).
    """
    platform = normalize_platform(g.get("platform"))
    if platform == "steam":
        if not steam_path:
            if not state.overlay_menu:
                print("Steam not found. Specify steam_path in config.json")
            return None
        aid = g.get("steam_app_id")
        if not aid:
            return None
        args = g.get("launch_args") or default_args.get("steam", "-fullscreen")
        process = launch_steam_game(steam_path, aid, args, state.steam_start_args)
        if not process:
            return None
        return GameStart(process, platform, skip_restore=str(aid) in steam_skip_restore_ids)

    if platform == "epic":
        exe = g.get("exe_path")
        if not exe:
            return None
        args = g.get("launch_args") or default_args.get("epic", "-fullscreen")
        process = launch_epic_game(exe, args)
        if not process:
            return None
        return GameStart(process, platform)

    if platform == "twitch":
        config = state.config
        nsp_path = g.get("nsp_path")
        if not nsp_path or not os.path.isfile(nsp_path):
            return None
        assoc_cfg = get_twitch_use_windows_association(config)
        if assoc_cfg is None:
            use_association = sys.platform == "win32"
        else:
            use_association = bool(assoc_cfg)
        emu = get_twitch_emulator_path(config)
        args = g.get("launch_args")
        if args is None:
            extra = (
                get_twitch_fullscreen_args(default_args)
                or get_twitch_launch_args(config)
            ).strip()
        else:
            extra = (args or "").strip()
        process = launch_twitch_game(emu, nsp_path, extra, use_association=use_association)
        if process is None:
            if not state.overlay_menu:
                print(
                    "Twitch: launch failed. On Windows set .nsp to open with your emulator (e.g. Ryujinx), "
                    "or set a valid twitch_emulator_path in config.json."
                )
            return None
        return GameStart(process, platform)

    if platform == "system":
        action = g.get("system_action")
        if action:
            perform_system_action(action)
            return "exit"
        return None

    return None
