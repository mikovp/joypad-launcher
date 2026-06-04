"""Steam library folder discovery."""

import os

from joypad.integrations.vdf import parse_vdf


def steam_library_folders(steam_exe_path):
    """Return list of Steam library root directories (primary + libraryfolders.vdf)."""
    if not steam_exe_path or not os.path.isfile(steam_exe_path):
        return []
    steam_dir = os.path.normpath(os.path.dirname(steam_exe_path))
    library_folders = [steam_dir]
    libraryfolders_path = os.path.join(steam_dir, "steamapps", "libraryfolders.vdf")
    if not os.path.isfile(libraryfolders_path):
        return library_folders
    data = parse_vdf(libraryfolders_path)
    if not data:
        return library_folders
    lf = data.get("libraryfolders") or data.get("LibraryFolders")
    if not lf:
        return library_folders
    seen_paths = {steam_dir.lower()}
    for _key, folder in lf.items():
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
    return library_folders
