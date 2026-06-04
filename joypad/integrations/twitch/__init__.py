"""Twitch (.nsp ROM) scan and launch."""

from joypad.integrations.twitch.launch import launch_nsp_game, launch_twitch_game
from joypad.integrations.twitch.platform import PLATFORM, normalize_game_entry, normalize_platform
from joypad.integrations.twitch.scan import scan_nsp_games, scan_twitch_games

__all__ = [
    "PLATFORM",
    "launch_nsp_game",
    "launch_twitch_game",
    "normalize_game_entry",
    "normalize_platform",
    "scan_nsp_games",
    "scan_twitch_games",
]
