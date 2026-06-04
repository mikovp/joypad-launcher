"""Steam library scan."""

import glob
import os

from joypad.integrations.steam.filters import should_skip_steam_app
from joypad.integrations.steam.libraries import steam_library_folders
from joypad.integrations.vdf import parse_vdf


def scan_steam_games(steam_exe_path):
    """
    Scans installed Steam games.
    steam_exe_path — path to steam.exe.
    Returns list of dict: name, platform="steam", steam_app_id, launch_args.
    """
    if not steam_exe_path or not os.path.isfile(steam_exe_path):
        return []
    games = []
    seen_appids = set()
    for lib_dir in steam_library_folders(steam_exe_path):
        apps_dir = os.path.join(lib_dir, "steamapps")
        if not os.path.isdir(apps_dir):
            continue
        for manifest_path in glob.glob(os.path.join(apps_dir, "appmanifest_*.acf")):
            data = parse_vdf(manifest_path)
            if not data or not isinstance(data, dict):
                continue
            appstate = data.get("AppState") or data.get("appstate")
            if not appstate and len(data) == 1:
                for v in data.values():
                    if isinstance(v, dict):
                        appstate = v
                        break
            if not appstate or not isinstance(appstate, dict):
                continue
            appid = appstate.get("appid") or appstate.get("AppID")
            if not appid:
                continue
            appid_str = str(appid)
            if appid_str in seen_appids:
                continue
            name = appstate.get("name") or appstate.get("Name") or f"App {appid_str}"
            app_type = appstate.get("type") or appstate.get("Type") or ""
            if should_skip_steam_app(name, app_type):
                continue
            seen_appids.add(appid_str)
            games.append({
                "name": name,
                "platform": "steam",
                "steam_app_id": appid_str,
                "launch_args": "-fullscreen",
            })
    games.sort(key=lambda g: g["name"].lower())
    return games
