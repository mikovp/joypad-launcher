# -*- coding: utf-8 -*-
"""
Scan installed games from Steam and Epic Games libraries.
"""

import json
import os
import glob
import re

try:
    import vdf
except ImportError:
    vdf = None

# Standard Epic path (single source — expandvars and ProgramData point to same place)
_programdata = os.environ.get("ProgramData", "C:\\ProgramData")
EPIC_MANIFESTS_DIRS = [
    os.path.join(_programdata, "Epic", "EpicGamesLauncher", "Data", "Manifests"),
]

# Cache: regex and skip types (VDF parser called for each manifest)
_VDF_TOKEN_PATTERN = re.compile(r'"([^"]*)"|\{|\}')
_STEAM_SKIP_TYPES = frozenset(("tool", "music", "video", "series", "advertising"))


def _parse_vdf_simple(path):
    """Minimal VDF parser (no vdf dep): keys and values in quotes, nested {}."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
    except Exception:
        return None
    # Remove // comments
    text = re.sub(r'//[^\n]*', '', text)
    result = {}
    stack = [result]
    # Tokens: "string" or { or }
    pos = 0
    key = None
    while True:
        m = _VDF_TOKEN_PATTERN.search(text, pos)
        if not m:
            break
        pos = m.end()
        if m.group(1) is not None:
            tok = m.group(1).strip()
            if key is None:
                key = tok
            else:
                stack[-1][key] = tok
                key = None
        elif m.group(0) == "{":
            new_obj = {}
            if key is not None:
                stack[-1][key] = new_obj
                key = None
            stack.append(new_obj)
        else:
            if len(stack) > 1:
                stack.pop()
    return result if stack else None


def _parse_vdf(path):
    """Reads VDF file and returns dict. Uses vdf first, fallback to built-in parser."""
    if vdf:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return vdf.load(f)
        except Exception:
            pass
    return _parse_vdf_simple(path)


def scan_steam_games(steam_exe_path):
    """
    Scans installed Steam games.
    steam_exe_path — path to steam.exe.
    Returns list of dict: name, platform="steam", steam_app_id, launch_args.
    """
    if not steam_exe_path or not os.path.isfile(steam_exe_path):
        return []
    steam_dir = os.path.normpath(os.path.dirname(steam_exe_path))
    steamapps = os.path.join(steam_dir, "steamapps")
    library_folders = [steam_dir]  # always start with Steam folder
    libraryfolders_path = os.path.join(steamapps, "libraryfolders.vdf")
    if os.path.isfile(libraryfolders_path):
        data = _parse_vdf(libraryfolders_path)
        if data:
            lf = data.get("libraryfolders") or data.get("LibraryFolders")
            if lf:
                seen_paths = {steam_dir.lower()}
                for key, folder in lf.items():
                    if isinstance(folder, dict):
                        path_val = folder.get("path") or folder.get("Path")
                    elif isinstance(folder, str):
                        path_val = folder
                    else:
                        continue
                    if not path_val:
                        continue
                    path_val = os.path.normpath(path_val)
                    if os.path.isdir(path_val) and path_val.lower() not in seen_paths:
                        seen_paths.add(path_val.lower())
                        library_folders.append(path_val)
    games = []
    seen_appids = set()
    for lib_dir in library_folders:
        apps_dir = os.path.join(lib_dir, "steamapps")
        if not os.path.isdir(apps_dir):
            continue
        for manifest_path in glob.glob(os.path.join(apps_dir, "appmanifest_*.acf")):
            data = _parse_vdf(manifest_path)
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
            app_type = (appstate.get("type") or appstate.get("Type") or "").lower()
            if app_type in _STEAM_SKIP_TYPES:
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


def scan_epic_games():
    """
    Scans installed Epic Games by manifests.
    Returns list of dict: name, platform="epic", exe_path, launch_args.
    """
    games = []
    seen_exe = set()  # one exe — one entry (avoid duplicates with two Manifest paths)
    for manifests_dir in EPIC_MANIFESTS_DIRS:
        if not os.path.isdir(manifests_dir):
            continue
        for item_path in glob.glob(os.path.join(manifests_dir, "*")):
            if os.path.isdir(item_path):
                continue
            try:
                with open(item_path, "r", encoding="utf-8", errors="replace") as f:
                    data = json.load(f)
            except Exception:
                continue
            install_location = data.get("InstallLocation") or data.get("InstallationLocation")
            if not install_location or not os.path.isdir(install_location):
                continue
            launch_exe = data.get("LaunchExecutable") or data.get("LaunchExecutablePath") or data.get("Executable")
            if not launch_exe:
                continue
            exe_path = os.path.normpath(os.path.join(install_location, launch_exe.replace("/", os.sep)))
            if not os.path.isfile(exe_path):
                continue
            exe_key = exe_path.lower()
            if exe_key in seen_exe:
                continue
            seen_exe.add(exe_key)
            display_name = data.get("DisplayName") or data.get("AppName") or data.get("CatalogItemId") or os.path.splitext(os.path.basename(exe_path))[0]
            games.append({
                "name": display_name,
                "platform": "epic",
                "exe_path": exe_path,
                "launch_args": "-fullscreen",
            })
    games.sort(key=lambda g: g["name"].lower())
    return games


def scan_all(steam_exe_path=None):
    """
    Scans Steam and Epic. steam_exe_path — path to steam.exe (optional).
    Returns combined game list without duplicates (Steam first, then Epic).
    """
    if steam_exe_path:
        steam_exe_path = os.path.normpath(steam_exe_path)
        if not os.path.isfile(steam_exe_path):
            steam_exe_path = None
    steam = scan_steam_games(steam_exe_path) if steam_exe_path else []
    epic = scan_epic_games()
    return steam + epic
