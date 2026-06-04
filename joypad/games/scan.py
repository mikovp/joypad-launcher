"""
Scan installed games from platform integrations.

Re-exports scanners for backward compatibility; orchestration lives here.
"""

import os

from joypad.integrations.epic import scan_epic_games
from joypad.integrations.steam import scan_steam_games
from joypad.integrations.twitch import scan_nsp_games, scan_twitch_games

__all__ = [
    "scan_all",
    "scan_epic_games",
    "scan_nsp_games",
    "scan_steam_games",
    "scan_twitch_games",
]


def scan_all(steam_exe_path=None):
    """
    Scans Steam and Epic. steam_exe_path — path to steam.exe (optional).
    Twitch (.nsp) ROMs are scanned separately via twitch_roms_folder in bootstrap.
    """
    if steam_exe_path:
        steam_exe_path = os.path.normpath(steam_exe_path)
        if not os.path.isfile(steam_exe_path):
            steam_exe_path = None
    steam = scan_steam_games(steam_exe_path) if steam_exe_path else []
    epic = scan_epic_games()
    return steam + epic
