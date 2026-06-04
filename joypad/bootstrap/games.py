"""Game list loading for bootstrap."""

import sys

from joypad.config.twitch import get_twitch_roms_folder
from joypad.integrations import normalize_game_entry
from joypad.platform.windows import get_steam_path


def collect_games(config: dict) -> list:
    """Load the game list from auto-scan and/or config entries."""
    if config.get("auto_scan"):
        from joypad.games.scan import scan_all

        steam_path = get_steam_path(config)
        if not steam_path:
            print("Steam not found. Specify steam_path in config.json (path to steam.exe).")
        games = scan_all(steam_path)
    else:
        games = [normalize_game_entry(g) for g in config.get("games", [])]

    roms_folder = get_twitch_roms_folder(config)
    if roms_folder:
        from joypad.games.scan import scan_twitch_games

        games = list(games) + scan_twitch_games(roms_folder)

    if not games:
        print(
            "No games to show: Steam/Epic scan empty or disabled, config 'games' empty, "
            "and twitch_roms_folder missing or contains no .nsp files."
        )
        sys.exit(1)
    return games


def _build_game_row_numbers(list_items: list) -> dict[int, int]:
    game_row_numbers = {}
    section_game_index = 0
    for idx, item in enumerate(list_items):
        if item["kind"] == "header":
            section_game_index = 0
        else:
            section_game_index += 1
            game_row_numbers[idx] = section_game_index
    return game_row_numbers
