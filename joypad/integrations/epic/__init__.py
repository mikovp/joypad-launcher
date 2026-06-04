"""Epic Games Store scan and launch."""

from joypad.integrations._exe import launch_exe_game
from joypad.integrations.epic.paths import EPIC_MANIFESTS_DIRS
from joypad.integrations.epic.scan import scan_epic_games


def launch_epic_game(exe_path, launch_args):
    """Launch Epic game by exe path. Returns Popen process or None."""
    return launch_exe_game(exe_path, launch_args)


__all__ = ["EPIC_MANIFESTS_DIRS", "launch_epic_game", "scan_epic_games"]
