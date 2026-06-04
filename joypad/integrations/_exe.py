"""Launch a Windows desktop app by executable path (Epic, Twitch, etc.)."""

import os
import subprocess

from joypad.integrations._subprocess import SUBPROCESS_KW


def launch_exe_game(exe_path, launch_args):
    """Launch by exe path. Returns Popen process or None."""
    exe_path = os.path.abspath(exe_path)
    if not os.path.isfile(exe_path):
        return None
    work_dir = os.path.dirname(exe_path)
    args = [exe_path]
    if launch_args:
        args.extend(str(launch_args).split())
    return subprocess.Popen(args, cwd=work_dir, shell=False, **SUBPROCESS_KW)
