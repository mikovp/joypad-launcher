# -*- coding: utf-8 -*-
"""Diagnostics: check Steam and Epic detection. Run: python scan_debug.py"""

import os
import sys

# load config like launcher
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
CONFIG_EXAMPLE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.example.json")

def main():
    config_path = CONFIG_PATH if os.path.exists(CONFIG_PATH) else CONFIG_EXAMPLE
    if not os.path.exists(config_path):
        print("No config.json and config.example.json")
        return
    import json
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Steam path
    steam_path = None
    path_from_config = (config.get("steam_path") or "").strip()
    if path_from_config and os.path.isfile(path_from_config):
        steam_path = os.path.normpath(path_from_config)
        print(f"Steam (from config): {steam_path}")
    if not steam_path:
        for p in [
            os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), "Steam", "steam.exe"),
            os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Steam", "steam.exe"),
        ]:
            if p and os.path.isfile(p):
                steam_path = p
                print(f"Steam (default folder): {steam_path}")
                break
    if not steam_path and sys.platform == "win32":
        try:
            import winreg
            for root, key_path in [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Valve\Steam"),
            ]:
                try:
                    key = winreg.OpenKey(root, key_path, 0, winreg.KEY_READ)
                    install_dir, _ = winreg.QueryValueEx(key, "InstallPath")
                    winreg.CloseKey(key)
                    if install_dir:
                        exe = os.path.join(install_dir, "steam.exe")
                        if os.path.isfile(exe):
                            steam_path = exe
                            print(f"Steam (registry): {steam_path}")
                            break
                except (OSError, FileNotFoundError):
                    pass
        except Exception as e:
            print(f"Registry read error: {e}")
    if not steam_path:
        print("Steam not found. Specify steam_path in config.json (full path to steam.exe).")
    else:
        steam_dir = os.path.dirname(steam_path)
        steamapps = os.path.join(steam_dir, "steamapps")
        print(f"  Steam folder: {steam_dir}")
        print(f"  steamapps exists: {os.path.isdir(steamapps)}")
        if os.path.isdir(steamapps):
            import glob
            manifests = glob.glob(os.path.join(steamapps, "appmanifest_*.acf"))
            print(f"  appmanifest_*.acf files: {len(manifests)}")
            lf = os.path.join(steamapps, "libraryfolders.vdf")
            print(f"  libraryfolders.vdf exists: {os.path.isfile(lf)}")

    # Scanning
    from scan_libraries import scan_steam_games, scan_epic_games, scan_all
    steam_games = scan_steam_games(steam_path) if steam_path else []
    epic_games = scan_epic_games()
    print(f"\nSteam games found: {len(steam_games)}")
    print(f"Epic games found: {len(epic_games)}")
    if steam_games:
        print("  Steam examples:", [g["name"] for g in steam_games[:5]])
    if epic_games:
        print("  Epic examples:", [g["name"] for g in epic_games[:5]])

if __name__ == "__main__":
    main()
