"""Diagnostics: check Steam and Epic detection.

Run from repo root: python -m joypad.games.scan_debug
"""

from joypad.config.loader import load_config
from joypad.config.twitch import get_twitch_roms_folder
from joypad.games.scan import scan_twitch_games
from joypad.platform.windows import get_steam_path


def main():
    config = load_config()
    steam_path = get_steam_path(config)
    if steam_path:
        print(f"Steam: {steam_path}")
    else:
        print("Steam not found. Specify steam_path in config.json (full path to steam.exe).")

    if steam_path:
        import glob
        import os

        steam_dir = os.path.dirname(steam_path)
        steamapps = os.path.join(steam_dir, "steamapps")
        print(f"  Steam folder: {steam_dir}")
        print(f"  steamapps exists: {os.path.isdir(steamapps)}")
        if os.path.isdir(steamapps):
            manifests = glob.glob(os.path.join(steamapps, "appmanifest_*.acf"))
            print(f"  appmanifest_*.acf files: {len(manifests)}")
            lf = os.path.join(steamapps, "libraryfolders.vdf")
            print(f"  libraryfolders.vdf exists: {os.path.isfile(lf)}")

    steam_games, epic_games = [], []
    if steam_path:
        from joypad.integrations.steam import scan_steam_games

        steam_games = scan_steam_games(steam_path)
    from joypad.integrations.epic import scan_epic_games

    epic_games = scan_epic_games()
    print(f"\nSteam games found: {len(steam_games)}")
    print(f"Epic games found: {len(epic_games)}")
    if steam_games:
        print("  Steam examples:", [g["name"] for g in steam_games[:5]])
    if epic_games:
        print("  Epic examples:", [g["name"] for g in epic_games[:5]])

    roms_folder = get_twitch_roms_folder(config)
    if roms_folder:
        twitch_games = scan_twitch_games(roms_folder)
        print(f"\nTwitch (.nsp) games in twitch_roms_folder: {len(twitch_games)}")
        if twitch_games:
            print("  Examples:", [g["name"] for g in twitch_games[:5]])
    else:
        print("\nTwitch: set twitch_roms_folder in config.json to scan .nsp files.")


if __name__ == "__main__":
    main()
