"""Windows registry helpers for Steam and uninstall paths."""

import os
import sys


def _get_steam_path_from_registry():
    """Steam path from Windows registry (HKLM and HKCU)."""
    if sys.platform != "win32":
        return None
    try:
        import winreg
        roots_and_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Valve\Steam"),
        ]
        for root, key_path in roots_and_paths:
            try:
                key = winreg.OpenKey(root, key_path, 0, winreg.KEY_READ)
                install_dir, _ = winreg.QueryValueEx(key, "InstallPath")
                winreg.CloseKey(key)
                if install_dir and os.path.isdir(install_dir):
                    exe = os.path.join(install_dir, "steam.exe")
                    if os.path.isfile(exe):
                        return exe
            except (OSError, FileNotFoundError):
                continue
    except Exception:
        pass
    return None


def get_steam_path(config):
    """Steam.exe path: config -> default folders -> Windows registry."""
    path = (config.get("steam_path") or "").strip()
    if path:
        path = os.path.normpath(path)
        if os.path.isfile(path):
            return path
    defaults = [
        os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), "Steam", "steam.exe"),
        os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Steam", "steam.exe"),
    ]
    for p in defaults:
        if p and os.path.isfile(p):
            return p
    return _get_steam_path_from_registry()


def find_exe_in_uninstall_registry(
    display_substring,
    *,
    exe_basename,
    value_names=("DisplayIcon", "InstallLocation"),
):
    """Search Windows uninstall registry keys for an installed app's exe path."""
    needle = (display_substring or "").lower()
    if not needle or sys.platform != "win32":
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
                    if needle not in str(display).lower():
                        continue
                    for value_name in value_names:
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
                            exe = os.path.join(val, exe_basename)
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
