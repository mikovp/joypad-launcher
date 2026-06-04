"""Platform integrations: scan and launch per store/service."""

from joypad.integrations.epic import launch_epic_game, scan_epic_games
from joypad.integrations.steam import launch_steam_game, scan_steam_games
from joypad.integrations.twitch import (
    launch_nsp_game,
    launch_twitch_game,
    normalize_game_entry,
    normalize_platform,
    scan_nsp_games,
    scan_twitch_games,
)

LAUNCHABLE_PLATFORMS = frozenset({"steam", "epic", "twitch"})
REMAP_ELIGIBLE_PLATFORMS = LAUNCHABLE_PLATFORMS

__all__ = [
    "LAUNCHABLE_PLATFORMS",
    "REMAP_ELIGIBLE_PLATFORMS",
    "launch_epic_game",
    "launch_nsp_game",
    "launch_steam_game",
    "launch_twitch_game",
    "normalize_game_entry",
    "normalize_platform",
    "scan_epic_games",
    "scan_nsp_games",
    "scan_steam_games",
    "scan_twitch_games",
]
