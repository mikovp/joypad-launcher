"""Epic Games manifest directory paths."""

import glob
import os

_programdata = os.environ.get("ProgramData", "C:\\ProgramData")
_localappdata = os.environ.get("LOCALAPPDATA", "")
EPIC_MANIFESTS_DIRS = []
for _epic_base in (
    os.path.join(_programdata, "Epic", "EpicGamesLauncher", "Data", "Manifests"),
    os.path.join(_localappdata, "EpicGamesLauncher", "Data", "Manifests"),
):
    if _epic_base and _epic_base not in EPIC_MANIFESTS_DIRS:
        EPIC_MANIFESTS_DIRS.append(_epic_base)


def epic_manifest_paths(manifests_dir):
    paths = set()
    for pattern in ("*.item", "*"):
        for item_path in glob.glob(os.path.join(manifests_dir, pattern)):
            if os.path.isfile(item_path):
                paths.add(item_path)
    return sorted(paths)
