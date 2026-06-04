"""Epic Games Store library scan."""

import json
import os

from joypad.integrations.epic.manifest import epic_image_url, epic_is_playable, epic_resolve_exe
from joypad.integrations.epic.paths import EPIC_MANIFESTS_DIRS, epic_manifest_paths


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
        for item_path in epic_manifest_paths(manifests_dir):
            try:
                with open(item_path, encoding="utf-8", errors="replace") as f:
                    data = json.load(f)
            except Exception:
                continue
            if not isinstance(data, dict):
                continue
            if not epic_is_playable(data):
                continue
            install_location = data.get("InstallLocation") or data.get("InstallationLocation")
            if not install_location:
                continue
            install_location = os.path.normpath(install_location.replace("/", os.sep))
            if not os.path.isdir(install_location):
                continue
            exe_path = epic_resolve_exe(install_location, data)
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
            img_url = epic_image_url(data)
            if img_url:
                entry["epic_image_url"] = img_url
            games.append(entry)
    games.sort(key=lambda g: g["name"].lower())
    return games
