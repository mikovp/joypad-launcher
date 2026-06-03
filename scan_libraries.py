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

# Epic manifest folders (ProgramData + per-user copy)
_programdata = os.environ.get("ProgramData", "C:\\ProgramData")
_localappdata = os.environ.get("LOCALAPPDATA", "")
EPIC_MANIFESTS_DIRS = []
for _epic_base in (
    os.path.join(_programdata, "Epic", "EpicGamesLauncher", "Data", "Manifests"),
    os.path.join(_localappdata, "EpicGamesLauncher", "Data", "Manifests"),
):
    if _epic_base and _epic_base not in EPIC_MANIFESTS_DIRS:
        EPIC_MANIFESTS_DIRS.append(_epic_base)

# Cache: regex and skip types (VDF parser called for each manifest)
_VDF_TOKEN_PATTERN = re.compile(r'"([^"]*)"|\{|\}')
_STEAM_SKIP_TYPES = frozenset(("tool", "music", "video", "series", "advertising"))
_STEAM_SKIP_NAME_PARTS = (
    "steamworks common redistributables",
    "steam linux runtime",
    "proton ",
    "directx",
    "vc_redist",
    "spacewar",
)


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
            name_lower = name.lower()
            if any(part in name_lower for part in _STEAM_SKIP_NAME_PARTS):
                continue
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


def _epic_manifest_paths(manifests_dir):
    """All Epic .item / manifest files in a folder (no subdirs)."""
    paths = set()
    for pattern in ("*.item", "*"):
        for item_path in glob.glob(os.path.join(manifests_dir, pattern)):
            if os.path.isfile(item_path):
                paths.add(item_path)
    return sorted(paths)


def _epic_resolve_exe(install_location, data):
    install_location = os.path.normpath(install_location.replace("/", os.sep))
    launch_exe = (
        data.get("LaunchExecutable")
        or data.get("LaunchExecutablePath")
        or data.get("Executable")
    )
    if launch_exe:
        exe_path = os.path.normpath(os.path.join(install_location, launch_exe.replace("/", os.sep)))
        if os.path.isfile(exe_path):
            return exe_path
    launch_cmd = (data.get("LaunchCommand") or "").strip()
    if launch_cmd:
        for name in (launch_cmd, launch_cmd + ".exe"):
            exe_path = os.path.join(install_location, name.replace("/", os.sep))
            if os.path.isfile(exe_path):
                return os.path.normpath(exe_path)
    return None


def _epic_image_url(data):
    """Remote image URL from Epic manifest, if present."""
    if not isinstance(data, dict):
        return None
    for key in (
        "ImageUrl",
        "ImageURI",
        "TitleImage",
        "Thumbnail",
        "LandscapeImage",
        "MasterImage",
        "IconUrl",
        "Icon",
        "Image",
    ):
        val = data.get(key)
        if isinstance(val, str) and val.startswith("http"):
            return val.strip()
    for nested_key in ("Metadata", "CustomMetadata", "AppInstallationInfo"):
        nested = data.get(nested_key)
        if isinstance(nested, dict):
            url = _epic_image_url(nested)
            if url:
                return url
    return None


def _epic_is_playable(data):
    if data.get("bIsIncompleteInstall"):
        return False
    if data.get("bIsExecutable") is False:
        return False
    categories = data.get("AppCategories") or []
    if categories and "games" not in [str(c).lower() for c in categories]:
        if "applications" in [str(c).lower() for c in categories]:
            return False
    technical = (data.get("TechnicalType") or "").lower()
    if technical and "games" not in technical and "applications" in technical:
        return False
    return True


def scan_epic_games():
    """
    Scans installed Epic Games by manifests (.item JSON in Manifests).
    Returns list of dict: name, platform="epic", exe_path, launch_args.
    """
    games = []
    seen_exe = set()
    for manifests_dir in EPIC_MANIFESTS_DIRS:
        if not os.path.isdir(manifests_dir):
            continue
        for item_path in _epic_manifest_paths(manifests_dir):
            try:
                with open(item_path, "r", encoding="utf-8", errors="replace") as f:
                    data = json.load(f)
            except Exception:
                continue
            if not isinstance(data, dict):
                continue
            if not _epic_is_playable(data):
                continue
            install_location = data.get("InstallLocation") or data.get("InstallationLocation")
            if not install_location:
                continue
            install_location = os.path.normpath(install_location.replace("/", os.sep))
            if not os.path.isdir(install_location):
                continue
            exe_path = _epic_resolve_exe(install_location, data)
            if not exe_path:
                continue
            exe_key = exe_path.lower()
            if exe_key in seen_exe:
                continue
            seen_exe.add(exe_key)
            display_name = (
                data.get("DisplayName")
                or data.get("AppName")
                or data.get("CatalogItemId")
                or os.path.splitext(os.path.basename(exe_path))[0]
            )
            entry = {
                "name": display_name,
                "platform": "epic",
                "exe_path": exe_path,
                "launch_args": "-fullscreen",
            }
            img_url = _epic_image_url(data)
            if img_url:
                entry["epic_image_url"] = img_url
            games.append(entry)
    games.sort(key=lambda g: g["name"].lower())
    return games


def _find_twitch_exe_windows():
    """Twitch desktop app path from common locations and uninstall registry."""
    candidates = []
    local = os.environ.get("LOCALAPPDATA", "")
    prog = os.environ.get("ProgramFiles", r"C:\Program Files")
    prog86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    for folder in (
        os.path.join(local, "Twitch"),
        os.path.join(local, "Twitch", "Bin"),
        os.path.join(prog, "Twitch"),
        os.path.join(prog86, "Twitch"),
    ):
        if folder:
            candidates.append(os.path.join(folder, "Twitch.exe"))
    for path in candidates:
        if path and os.path.isfile(path):
            return os.path.normpath(path)
    if os.name != "nt":
        return None
    try:
        import winreg
    except ImportError:
        return None
    uninstall_roots = (
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    )
    for root, subkey in uninstall_roots:
        try:
            key = winreg.OpenKey(root, subkey)
        except OSError:
            continue
        try:
            n = winreg.QueryInfoKey(key)[0]
            for i in range(n):
                try:
                    sk = winreg.OpenKey(key, winreg.EnumKey(key, i))
                    try:
                        display, _ = winreg.QueryValueEx(sk, "DisplayName")
                    except OSError:
                        continue
                    if "twitch" not in str(display).lower():
                        continue
                    for value_name in ("DisplayIcon", "InstallLocation"):
                        try:
                            val, _ = winreg.QueryValueEx(sk, value_name)
                        except OSError:
                            continue
                        if not val:
                            continue
                        val = str(val).strip().strip('"')
                        if val.lower().endswith(".exe") and os.path.isfile(val):
                            return os.path.normpath(val)
                        if os.path.isdir(val):
                            exe = os.path.join(val, "Twitch.exe")
                            if os.path.isfile(exe):
                                return os.path.normpath(exe)
                except OSError:
                    pass
        finally:
            try:
                winreg.CloseKey(key)
            except Exception:
                pass
    return None


def scan_twitch_app():
    """Twitch desktop client if installed (not from Steam/Epic manifests)."""
    exe = _find_twitch_exe_windows()
    if not exe:
        return []
    return [{
        "name": "Twitch",
        "platform": "twitch",
        "exe_path": exe,
        "launch_args": "",
    }]


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
    twitch = scan_twitch_app()
    return steam + epic + twitch


def scan_nsp_games(root_folder):
    """
    Recursively find *.nsp under root_folder (including UNC \\\\server\\share paths).
    Returns entries with name, platform 'nsp', and full nsp_path.
    Nested paths use display name 'Subfolder / Title' without the .nsp extension.
    """
    root_folder = os.path.normpath((root_folder or "").strip())
    if not root_folder or not os.path.isdir(root_folder):
        return []
    games = []
    for dirpath, _dirnames, filenames in os.walk(root_folder):
        for fn in filenames:
            if not fn.lower().endswith(".nsp"):
                continue
            full = os.path.join(dirpath, fn)
            stem = os.path.splitext(fn)[0]
            try:
                rel_dir = os.path.relpath(dirpath, root_folder)
            except ValueError:
                rel_dir = ""
            if rel_dir and rel_dir != ".":
                display = "%s / %s" % (rel_dir.replace(os.sep, " / "), stem)
            else:
                display = stem
            games.append({
                "name": display,
                "platform": "nsp",
                "nsp_path": full,
                "nsp_filename": stem,
            })
    games.sort(key=lambda g: g["name"].lower())
    return games
