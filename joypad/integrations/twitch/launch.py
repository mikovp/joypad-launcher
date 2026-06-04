"""Twitch (.nsp ROM) launch."""

import os
import subprocess
import sys

from joypad.integrations._subprocess import SUBPROCESS_KW
from joypad.integrations.twitch.shell import shell_execute_open_file


def launch_twitch_game(emulator_exe, nsp_path, launch_args, use_association=True):
    """
    Launch .nsp via Twitch integration: Windows file association or emulator + ROM.
    """
    nsp_path = os.path.normpath(nsp_path)
    if not os.path.isfile(nsp_path):
        return None
    if sys.platform == "win32" and use_association:
        proc = shell_execute_open_file(nsp_path)
        if proc is not None:
            return proc
    emulator_exe = (emulator_exe or "").strip()
    if not emulator_exe:
        return None
    emulator_exe = os.path.normpath(emulator_exe)
    if not os.path.isfile(emulator_exe):
        return None
    work_dir = os.path.dirname(emulator_exe)
    args = [emulator_exe, nsp_path]
    if launch_args:
        args.extend(str(launch_args).split())
    return subprocess.Popen(args, cwd=work_dir, shell=False, **SUBPROCESS_KW)


launch_nsp_game = launch_twitch_game
