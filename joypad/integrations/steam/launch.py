"""Steam game launch."""

import subprocess

from joypad.integrations._subprocess import SUBPROCESS_KW


def launch_steam_game(steam_exe, app_id, launch_args, steam_start_args=None):
    """Launches Steam game. Returns Popen process.

    steam_start_args — extra args for Steam client (e.g. '-silent'), from config.json -> steam_start_args.
    """
    args = [steam_exe]
    if steam_start_args:
        args.extend(str(steam_start_args).split())
    args.extend(["-applaunch", str(app_id)])
    if launch_args:
        args.extend(str(launch_args).split())
    return subprocess.Popen(args, shell=False, **SUBPROCESS_KW)
