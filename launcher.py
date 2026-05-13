#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Steam and Epic game launcher with gamepad control.
Launches games in fullscreen mode.
"""

import json
import math
import os
import subprocess
import sys
import time

try:
    import pygame
except ImportError:
    print("Install pygame: pip install pygame")
    sys.exit(1)

# Base folder: when running from exe (PyInstaller) — next to exe, otherwise — script folder
if getattr(sys, "frozen", False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(_BASE_DIR, "config.json")
CONFIG_EXAMPLE = os.path.join(_BASE_DIR, "config.example.json")

# Gamepad buttons (Xbox layout)
BTN_A = 0
BTN_B = 1
BTN_X = 2
BTN_Y = 3
BTN_LB = 4
BTN_RB = 5
BTN_BACK = 6
BTN_START = 7
AXIS_LEFT_Y = 1   # up negative, down positive
AXIS_LEFT_X = 0
DEADZONE = 0.5

# Default colors (overridden from config.json → theme)
BG_COLOR = (20, 20, 28)
TEXT_COLOR = (220, 220, 230)
HIGHLIGHT_COLOR = (70, 130, 200)
TITLE_COLOR = (160, 160, 180)


def _hard_break_word(font, word, max_width):
    """Split a single word into chunks if it is wider than max_width."""
    if not word:
        return [""]
    lines = []
    cur = ""
    for ch in word:
        trial = cur + ch
        if font.size(trial)[0] <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines if lines else [word]


def _wrap_words_to_width(font, text, max_width):
    """Word-wrap text so each line fits within max_width pixels."""
    if max_width < 16:
        return [text] if text else [""]
    raw = (text or "").strip()
    if not raw:
        return [""]
    words = raw.split()
    lines = []
    cur = words[0]
    if font.size(cur)[0] > max_width:
        hb = _hard_break_word(font, cur, max_width)
        lines.extend(hb[:-1])
        cur = hb[-1] if hb else ""
        words = words[1:]
    else:
        words = words[1:]
    for word in words:
        trial = cur + " " + word
        if font.size(trial)[0] <= max_width:
            cur = trial
        else:
            lines.append(cur)
            cur = word
            if font.size(cur)[0] > max_width:
                hb = _hard_break_word(font, cur, max_width)
                lines.extend(hb[:-1])
                cur = hb[-1] if hb else ""
    if cur:
        lines.append(cur)
    return lines


def _parse_color(value, default):
    """Converts config value to (R, G, B) tuple.
    value: string #RRGGBB / #RGB or list [r,g,b] (0-255).
    """
    if value is None:
        return default
    # Hex: "#1a1a1c" or "1a1a1c", short "#fff" -> #ffffff
    if isinstance(value, str):
        s = value.strip().lstrip("#")
        try:
            if len(s) == 6:
                r, g, b = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
                return (r, g, b)
            if len(s) == 3:
                r = int(s[0], 16) * 17
                g = int(s[1], 16) * 17
                b = int(s[2], 16) * 17
                return (r, g, b)
        except (ValueError, IndexError):
            pass
        return default
    if isinstance(value, (list, tuple)) and len(value) >= 3:
        try:
            r, g, b = int(value[0]), int(value[1]), int(value[2])
            if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
                return (r, g, b)
        except (TypeError, ValueError):
            pass
    return default


def _parse_font_size(value, default, min_size=12, max_size=120):
    """Returns font size (int) from config."""
    if value is None:
        return default
    try:
        size = int(value)
        return max(min_size, min(max_size, size))
    except (TypeError, ValueError):
        return default


def _parse_font_bold(value, default=False):
    """Returns True for bold font, False for normal."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        s = value.strip().lower()
        if s in ("bold", "true", "1", "yes"):
            return True
        if s in ("normal", "regular", "false", "0", "no"):
            return False
    return default


def _parse_font_scale(value, default=1.0):
    """Positive font size multiplier from theme.font_scale."""
    if value is None:
        return default
    try:
        x = float(value)
        return x if x > 0 else default
    except (TypeError, ValueError):
        return default


def _parse_positive_float(value, default):
    if value is None:
        return default
    try:
        x = float(value)
        return x if x > 0 else default
    except (TypeError, ValueError):
        return default


def _theme_from_config(config):
    """Returns theme colors and sizes dict from config (theme.*)."""
    theme = config.get("theme") or {}
    return {
        "background": _parse_color(theme.get("background"), BG_COLOR),
        "cursor": _parse_color(theme.get("cursor"), HIGHLIGHT_COLOR),
        "text": _parse_color(theme.get("text"), TEXT_COLOR),
        "title": _parse_color(theme.get("title"), TITLE_COLOR),
        "font_size_title": _parse_font_size(theme.get("font_size_title") or theme.get("font_size_large"), 42, 12, 96),
        "font_size_list": _parse_font_size(theme.get("font_size_list") or theme.get("font_size_small"), 28, 12, 72),
        "font_bold_title": _parse_font_bold(theme.get("font_bold_title"), False),
        "font_bold_list": _parse_font_bold(theme.get("font_bold_list"), False),
        "background_image": (theme.get("background_image") or "").strip() or None,
    }


def _scale_theme_fonts_for_screen(theme, theme_section, screen_height):
    """
    Scale fonts up when display height is below the reference (e.g. 1280×960 / streaming).
    Default: if height < auto_font_boost_ref_height (1080), multiply by ref/height, capped at auto_font_boost_max.
    Then multiply by theme.font_scale for manual tuning.
    """
    if not theme_section:
        theme_section = {}
    t = theme["font_size_title"]
    l = theme["font_size_list"]
    auto = theme_section.get("auto_font_boost_low_res")
    if auto is None:
        auto = True
    if auto and screen_height > 0:
        ref = _parse_positive_float(theme_section.get("auto_font_boost_ref_height"), 1080.0)
        boost_max = _parse_positive_float(theme_section.get("auto_font_boost_max"), 1.65)
        if screen_height < ref:
            factor = min(boost_max, ref / float(screen_height))
            t = int(round(t * factor))
            l = int(round(l * factor))
    mult = _parse_font_scale(theme_section.get("font_scale"), 1.0)
    if mult != 1.0:
        t = int(round(t * mult))
        l = int(round(l * mult))
    theme["font_size_title"] = max(12, min(96, t))
    theme["font_size_list"] = max(12, min(72, l))


def load_config():
    """Loads config.json or uses example and exits if not found."""
    path = CONFIG_PATH
    if not os.path.exists(path):
        path = CONFIG_EXAMPLE
    if not os.path.exists(path) and getattr(sys, "frozen", False):
        path_mei = os.path.join(sys._MEIPASS, "config.example.json")
        if os.path.exists(path_mei):
            path = path_mei
    if not os.path.exists(path):
        msg = f"config.json not found. Copy config.example.json to the launcher folder:\n{_BASE_DIR}"
        print(msg)
        raise FileNotFoundError(msg)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if path == CONFIG_EXAMPLE and not os.path.exists(CONFIG_PATH):
        print("Using config.example.json. Copy to config.json and configure games.")
    return data


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


# Suppress game output to launcher console (game stdout/stderr does not clutter terminal)
_SUBPROCESS_KW = {
    "stdout": subprocess.DEVNULL,
    "stderr": subprocess.DEVNULL,
    "stdin": subprocess.DEVNULL,
}


def launch_steam_game(steam_exe, app_id, launch_args, steam_start_args=None):
    """Launches Steam game. Returns Popen process (for switching focus to Steam/game window).

    steam_start_args — extra args for Steam client (e.g. '-silent'), from config.json -> steam_start_args.
    """
    args = [steam_exe]
    if steam_start_args:
        args.extend(steam_start_args.split())
    args.extend(["-applaunch", str(app_id)])
    if launch_args:
        args.extend(launch_args.split())
    return subprocess.Popen(args, shell=False, **_SUBPROCESS_KW)


def launch_epic_game(exe_path, launch_args):
    """Launch Epic game by exe path. Returns Popen process or None."""
    exe_path = os.path.abspath(exe_path)
    if not os.path.isfile(exe_path):
        return None
    work_dir = os.path.dirname(exe_path)
    args = [exe_path]
    if launch_args:
        args.extend(launch_args.split())
    return subprocess.Popen(args, cwd=work_dir, shell=False, **_SUBPROCESS_KW)


class _ShellExecuteProcess:
    """Minimal process handle from ShellExecuteEx; supports poll()/pid for wait and focus."""

    STILL_ACTIVE = 259

    def __init__(self, h_process):
        self._hp = h_process
        self.pid = None
        try:
            from ctypes import windll

            pid = windll.kernel32.GetProcessId(h_process)
            self.pid = pid if pid else None
        except Exception:
            pass

    def poll(self):
        from ctypes import windll, byref
        from ctypes.wintypes import DWORD

        if not self._hp:
            return 0
        code = DWORD()
        if not windll.kernel32.GetExitCodeProcess(self._hp, byref(code)):
            windll.kernel32.CloseHandle(self._hp)
            self._hp = None
            return None
        if code.value == self.STILL_ACTIVE:
            return None
        windll.kernel32.CloseHandle(self._hp)
        self._hp = None
        return code.value


def _shell_execute_open_file(path):
    """Windows: open file with its registered app (same as double-click)."""
    if sys.platform != "win32":
        return None
    try:
        import ctypes
        from ctypes import wintypes, byref

        SEE_MASK_NOCLOSEPROCESS = 0x00000040

        class SHELLEXECUTEINFOW(ctypes.Structure):
            _fields_ = (
                ("cbSize", ctypes.c_uint32),
                ("fMask", ctypes.c_uint32),
                ("hwnd", wintypes.HWND),
                ("lpVerb", wintypes.LPCWSTR),
                ("lpFile", wintypes.LPCWSTR),
                ("lpParameters", wintypes.LPCWSTR),
                ("lpDirectory", wintypes.LPCWSTR),
                ("nShow", ctypes.c_int),
                ("hInstApp", wintypes.HINSTANCE),
                ("lpIDList", ctypes.c_void_p),
                ("lpClass", wintypes.LPCWSTR),
                ("hKeyClass", wintypes.HANDLE),
                ("dwHotKey", ctypes.c_uint32),
                ("hIcon", wintypes.HANDLE),
                ("hProcess", wintypes.HANDLE),
            )

        sei = SHELLEXECUTEINFOW()
        sei.cbSize = ctypes.sizeof(SHELLEXECUTEINFOW)
        sei.fMask = SEE_MASK_NOCLOSEPROCESS
        sei.lpVerb = "open"
        sei.lpFile = os.path.normpath(path)
        sei.nShow = 1

        if not ctypes.windll.shell32.ShellExecuteExW(byref(sei)):
            return None
        hp = sei.hProcess
        try:
            handle_val = ctypes.cast(hp, ctypes.c_void_p).value if hp else None
        except Exception:
            handle_val = None
        if handle_val:
            return _ShellExecuteProcess(hp)
        return None
    except Exception:
        return None


def launch_nsp_game(emulator_exe, nsp_path, launch_args, use_association=True):
    """
    Launch .nsp: on Windows with use_association, via file-type association (e.g. Ryujinx for .nsp);
    otherwise or if the shell returns no process handle, run emulator_exe + ROM directly.
    """
    nsp_path = os.path.normpath(nsp_path)
    if not os.path.isfile(nsp_path):
        return None
    if sys.platform == "win32" and use_association:
        proc = _shell_execute_open_file(nsp_path)
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
    return subprocess.Popen(args, cwd=work_dir, shell=False, **_SUBPROCESS_KW)


def perform_system_action(action):
    """Performs Windows system action (shutdown / reboot)."""
    if sys.platform != "win32":
        return
    cmd = None
    # Can be extended (sleep, hibernate, etc.)
    if action == "shutdown":
        cmd = ["shutdown", "/s", "/t", "0"]
    elif action == "reboot":
        cmd = ["shutdown", "/r", "/t", "0"]
    if not cmd:
        return
    try:
        subprocess.Popen(cmd, shell=False, **_SUBPROCESS_KW)
    except Exception:
        # Error here is non-critical, just ignore
        pass


def _send_launcher_to_back(hwnd):
    """Sends launcher window to background (Windows)."""
    if not hwnd or sys.platform != "win32":
        return
    try:
        from ctypes import windll
        HWND_BOTTOM = 1
        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001
        windll.user32.SetWindowPos(hwnd, HWND_BOTTOM, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
    except Exception:
        pass


def _get_process_and_descendant_pids(pid):
    """Returns [pid] + all child PIDs recursively (Windows, Toolhelp32)."""
    if not pid or sys.platform != "win32":
        return [pid] if pid else []
    try:
        from ctypes import windll, byref, Structure, c_ulong, c_char, sizeof
        from ctypes.wintypes import DWORD
        kernel32 = windll.kernel32
        TH32CS_SNAPPROCESS = 0x00000002
        INVALID_HANDLE_VALUE = 0xFFFFFFFF

        class PROCESSENTRY32(Structure):
            _fields_ = [
                ("dwSize", DWORD),
                ("cntUsage", DWORD),
                ("th32ProcessID", DWORD),
                ("th32DefaultHeapID", c_ulong),
                ("th32ModuleID", DWORD),
                ("cntThreads", DWORD),
                ("th32ParentProcessID", DWORD),
                ("pcPriClassBase", c_ulong),
                ("dwFlags", DWORD),
                ("szExeFile", c_char * 260),
            ]
        snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if snap == INVALID_HANDLE_VALUE or snap is None:
            return [pid]
        parent_to_children = {}
        try:
            pe = PROCESSENTRY32()
            pe.dwSize = sizeof(PROCESSENTRY32)
            if not kernel32.Process32First(snap, byref(pe)):
                return [pid]
            while True:
                parent_to_children.setdefault(pe.th32ParentProcessID, []).append(pe.th32ProcessID)
                if not kernel32.Process32Next(snap, byref(pe)):
                    break
        finally:
            kernel32.CloseHandle(snap)
        result = [pid]
        to_visit = [pid]
        while to_visit:
            p = to_visit.pop()
            for child in parent_to_children.get(p, []):
                if child not in result:
                    result.append(child)
                    to_visit.append(child)
        return result
    except Exception:
        return [pid] if pid else []


def _bring_process_window_to_foreground(pid):
    """Finds process main window by PID and switches focus to it (Windows)."""
    if not pid or sys.platform != "win32":
        return
    try:
        from ctypes import windll, byref, c_ulong, c_bool, c_void_p, WINFUNCTYPE
        found_hwnd = [None]

        def enum_callback(hwnd, _lparam):
            if not windll.user32.IsWindowVisible(hwnd):
                return True
            proc_id = c_ulong()
            windll.user32.GetWindowThreadProcessId(hwnd, byref(proc_id))
            if proc_id.value == pid:
                found_hwnd[0] = hwnd
                return False
            return True

        EnumWindowsProc = WINFUNCTYPE(c_bool, c_void_p, c_void_p)
        windll.user32.EnumWindows(EnumWindowsProc(enum_callback), 0)
        game_hwnd = found_hwnd[0]
        if not game_hwnd:
            return
        SW_RESTORE = 9
        windll.user32.ShowWindow(game_hwnd, SW_RESTORE)
        windll.user32.SetForegroundWindow(game_hwnd)
    except Exception:
        pass


def _bring_game_to_foreground(process, attempts=12):
    """Switches focus to process window or its child processes.
    attempts: number of tries (12 ~ 6s for Epic, 20 ~ 10s for Steam).
    """
    if not process or sys.platform != "win32":
        return
    seen_pids = set()
    for _ in range(attempts):
        pids = _get_process_and_descendant_pids(process.pid)
        for pid in pids:
            seen_pids.add(pid)
            _bring_process_window_to_foreground(pid)
        pygame.event.pump()
        time.sleep(0.5)


def _bring_any_other_window_to_foreground(skip_hwnd):
    """Switches focus to first other visible window with title (for Steam — game window)."""
    if not skip_hwnd or sys.platform != "win32":
        return
    try:
        from ctypes import windll, byref, c_ulong, c_bool, c_void_p, WINFUNCTYPE, create_unicode_buffer
        found_hwnd = [None]

        def enum_callback(hwnd, _lparam):
            if hwnd == skip_hwnd or not windll.user32.IsWindowVisible(hwnd):
                return True
            length = windll.user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True
            buf = create_unicode_buffer(length + 1)
            windll.user32.GetWindowTextW(hwnd, buf, length + 1)
            if buf.value and buf.value.strip():
                found_hwnd[0] = hwnd
                return False
            return True

        EnumWindowsProc = WINFUNCTYPE(c_bool, c_void_p, c_void_p)
        windll.user32.EnumWindows(EnumWindowsProc(enum_callback), 0)
        other_hwnd = found_hwnd[0]
        if other_hwnd:
            SW_RESTORE = 9
            windll.user32.ShowWindow(other_hwnd, SW_RESTORE)
            windll.user32.SetForegroundWindow(other_hwnd)
    except Exception:
        pass


def _bring_launcher_to_front(hwnd):
    """Restores window from minimized and brings to foreground (Windows)."""
    if not hwnd or sys.platform != "win32":
        return
    try:
        from ctypes import windll
        SW_RESTORE = 9
        windll.user32.ShowWindow(hwnd, SW_RESTORE)
        windll.user32.SetForegroundWindow(hwnd)
    except Exception:
        pass


def _yield_for_game_window(seconds=2.0):
    """Gives game time to create window and get focus (event processing + pause)."""
    steps = max(1, int(seconds * 10))
    for _ in range(steps):
        pygame.event.pump()
        time.sleep(seconds / steps)


def _wait_for_game_and_restore(process, hwnd, platform=None):
    """Waits for game process to finish, then brings launcher to foreground.

    For Epic we wait for the game process to exit.
    For Steam we wait until Steam process has no child processes (game exited),
    so we do not hang while Steam client is open.
    """
    if not process:
        return

    if platform == "steam" and sys.platform == "win32":
        # Wait until steam.exe has no child processes (games),
        # so we do not hang while Steam client is open.
        while process.poll() is None:
            pygame.event.pump()
            try:
                pids = _get_process_and_descendant_pids(process.pid)
            except Exception:
                pids = [process.pid]
            child_pids = [p for p in pids if p != process.pid]
            if not child_pids:
                break
            time.sleep(0.5)
    else:
        # Normal process wait (Epic and others)
        while process.poll() is None:
            pygame.event.pump()
            time.sleep(0.5)

    _bring_launcher_to_front(hwnd)


def _try_launch_game(g, steam_path, default_args, steam_start_args, steam_skip_restore_ids, hwnd):
    """Launches game from entry g. Returns (should_exit, axis_held) or None on skip."""
    platform = g.get("platform")
    skip_restore = False
    process = None

    if platform == "steam":
        if not steam_path:
            print("Steam not found. Specify steam_path in config.json")
            return None
        aid = g.get("steam_app_id")
        if not aid:
            return None
        args = g.get("launch_args") or default_args.get("steam", "-fullscreen")
        process = launch_steam_game(steam_path, aid, args, steam_start_args)
        if str(aid) in steam_skip_restore_ids:
            skip_restore = True
    elif platform == "epic":
        exe = g.get("exe_path")
        if not exe:
            return None
        args = g.get("launch_args") or default_args.get("epic", "-fullscreen")
        process = launch_epic_game(exe, args)
    elif platform == "system":
        action = g.get("system_action")
        if action:
            perform_system_action(action)
            return (True,)  # should_exit
        return None

    _yield_for_game_window(2.0)
    if process and platform == "epic":
        _bring_game_to_foreground(process, 12)
    elif process and platform == "steam":
        _bring_game_to_foreground(process, 20)
    elif process:
        _bring_process_window_to_foreground(process.pid)
        _yield_for_game_window(0.5)
        _bring_process_window_to_foreground(process.pid)
    _send_launcher_to_back(hwnd)
    pygame.display.iconify()
    if not skip_restore:
        _wait_for_game_and_restore(process, hwnd, platform)
    return (False, 15)  # axis_held


def build_categorized_game_list(games):
    """
    Build UI list entries: category headers and game rows.
    Order: Steam → Epic Games → Nintendo Switch → Other (system and unknown platform).
    Empty categories are omitted.
    """
    buckets = {"steam": [], "epic": [], "nsp": [], "_other": []}
    for g in games:
        p = (g.get("platform") or "").lower()
        if p == "steam":
            buckets["steam"].append(g)
        elif p == "epic":
            buckets["epic"].append(g)
        elif p == "nsp":
            buckets["nsp"].append(g)
        else:
            buckets["_other"].append(g)

    sections = [
        ("steam", "Steam"),
        ("epic", "Epic Games"),
        ("nsp", "Nintendo Switch"),
    ]
    items = []
    for key, title in sections:
        lst = buckets[key]
        if not lst:
            continue
        items.append({"kind": "header", "title": title})
        for game in lst:
            items.append({"kind": "game", "game": game})
    other = buckets["_other"]
    if other:
        items.append({"kind": "header", "title": "Other"})
        for game in other:
            items.append({"kind": "game", "game": game})
    return items


def run_launcher():
    config = load_config()
    if config.get("auto_scan"):
        from scan_libraries import scan_all
        steam_path = get_steam_path(config)
        if not steam_path:
            print("Steam not found. Specify steam_path in config.json (path to steam.exe).")
        games = scan_all(steam_path)
    else:
        games = config.get("games", [])

    nsp_roms_folder = (config.get("nsp_roms_folder") or "").strip()
    if nsp_roms_folder:
        from scan_libraries import scan_nsp_games
        games = list(games) + scan_nsp_games(nsp_roms_folder)

    if not games:
        print(
            "No games to show: Steam/Epic scan empty or disabled, config 'games' empty, "
            "and nsp_roms_folder missing or contains no .nsp files."
        )
        sys.exit(1)

    list_items = build_categorized_game_list(games)
    game_row_numbers = {}
    section_game_index = 0
    for _i, _it in enumerate(list_items):
        if _it["kind"] == "header":
            section_game_index = 0
        else:
            section_game_index += 1
            game_row_numbers[_i] = section_game_index

    steam_path = get_steam_path(config)
    default_args = config.get("fullscreen_args", {})
    steam_start_args = (config.get("steam_start_args") or "").strip() or None
    # Steam games that should not auto-restore launcher focus on exit (e.g. games with external launchers like Fallout 76).
    steam_skip_restore_ids = {
        str(x)
        for x in (config.get("steam_skip_restore_ids") or [])
    }
    theme = _theme_from_config(config)
    bg_color = theme["background"]
    text_color = theme["text"]
    highlight_color = theme["cursor"]
    title_color = theme["title"]
    font_bold_title = theme["font_bold_title"]
    font_bold_list = theme["font_bold_list"]
    background_image_path = theme.get("background_image")

    pygame.init()
    pygame.joystick.init()

    info = pygame.display.Info()
    w, h = info.current_w, info.current_h
    _scale_theme_fonts_for_screen(theme, config.get("theme") or {}, h)
    font_size_title = theme["font_size_title"]
    font_size_list = theme["font_size_list"]
    # Borderless fullscreen window (non-exclusive fullscreen — better for streaming/Sunshine)
    screen = pygame.display.set_mode((w, h), pygame.NOFRAME)
    pygame.display.set_caption("Joypad Launcher")
    pygame.mouse.set_visible(False)

    # Background image (path relative to launcher folder or absolute)
    bg_surface = None
    if background_image_path:
        img_path = background_image_path if os.path.isabs(background_image_path) else os.path.join(_BASE_DIR, background_image_path)
        try:
            if os.path.isfile(img_path):
                img = pygame.image.load(img_path)
                bg_surface = pygame.transform.smoothscale(img, (w, h))
        except Exception:
            pass
    hwnd = pygame.display.get_wm_info().get("window") if sys.platform == "win32" else None
    if hwnd and sys.platform == "win32":
        try:
            from ctypes import windll
            SWP_NOZORDER = 0x0004
            windll.user32.SetWindowPos(hwnd, None, 0, 0, w, h, SWP_NOZORDER)
        except Exception:
            pass

    def rescan_joysticks():
        pygame.joystick.quit()
        pygame.joystick.init()
        js = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
        for j in js:
            j.init()
        pygame.event.clear()
        return js

    joysticks = rescan_joysticks()
    frames_since_rescan = 0
    RESCAN_INTERVAL = 120

    font_title = pygame.font.SysFont("Segoe UI", font_size_title, bold=font_bold_title)
    font_list = pygame.font.SysFont("Segoe UI", font_size_list, bold=font_bold_list)
    font_category = pygame.font.SysFont("Segoe UI", font_size_list, bold=True)

    line_h = max(36, int(font_size_list * 2))
    list_start_y = 40 + font_size_title * 2
    list_bottom_margin = max(50, font_size_title + 24)
    list_line_skip = font_list.get_linesize() + 3
    margin_right = 52
    list_left = 80

    def build_list_layout():
        cat_skip = font_category.get_linesize() + 8
        max_right = w - margin_right
        cum_starts = []
        specs = []
        y_acc = 0
        for idx, item in enumerate(list_items):
            cum_starts.append(y_acc)
            if item["kind"] == "header":
                h_row = cat_skip
                specs.append({"kind": "header", "height": h_row, "title": item["title"]})
            else:
                num = game_row_numbers[idx]
                prefix = "    %d. " % num
                pw = font_list.size(prefix)[0]
                x_text = list_left + pw
                usable = max(48, max_right - x_text)
                name = item["game"].get("name", "Untitled")
                name_lines = _wrap_words_to_width(font_list, name, usable)
                h_row = max(list_line_skip, len(name_lines) * list_line_skip + 6)
                specs.append({
                    "kind": "game",
                    "height": h_row,
                    "prefix": prefix,
                    "name_lines": name_lines,
                    "x_text": x_text,
                })
            y_acc += h_row
        total_h = y_acc
        return cum_starts, specs, total_h

    cum_starts, row_specs, list_content_height = build_list_layout()
    viewport_h = max(60, h - list_start_y - list_bottom_margin)
    max_scroll_y = max(0, list_content_height - viewport_h)
    scroll_y = 0
    list_snap_scroll_to_selection = True

    def move_selection_by_viewport(delta_pages):
        """Move highlight by roughly one screen (sum of game row heights), skipping category headers."""
        nonlocal selected
        if delta_pages == 0:
            return
        step_px = max(int(viewport_h * 0.85), list_line_skip * 4)
        direction = 1 if delta_pages > 0 else -1
        pixels_moved = 0
        max_steps = len(list_items) + 2
        for _ in range(max_steps):
            if direction > 0:
                nxt = None
                for j in range(selected + 1, len(list_items)):
                    if list_items[j]["kind"] == "game":
                        nxt = j
                        break
                if nxt is None:
                    break
                pixels_moved += row_specs[nxt]["height"]
                selected = nxt
            else:
                nxt = None
                for j in range(selected - 1, -1, -1):
                    if list_items[j]["kind"] == "game":
                        nxt = j
                        break
                if nxt is None:
                    break
                pixels_moved += row_specs[nxt]["height"]
                selected = nxt
            if pixels_moved >= step_px:
                break

    def page_scroll(delta_pages):
        nonlocal list_snap_scroll_to_selection
        move_selection_by_viewport(delta_pages)
        list_snap_scroll_to_selection = True

    def _first_game_row_index():
        for i, it in enumerate(list_items):
            if it["kind"] == "game":
                return i
        return 0

    def move_game_selection(delta):
        """Move selection only across game rows (skip category headers)."""
        nonlocal selected, list_snap_scroll_to_selection
        n = len(list_items)
        if n == 0:
            return
        for _ in range(n):
            selected = (selected + delta) % n
            if list_items[selected]["kind"] == "game":
                list_snap_scroll_to_selection = True
                return

    selected = _first_game_row_index()
    axis_held = 0  # pause between selection steps (lower = more responsive)
    AXIS_REPEAT_FRAMES = 18  # ~0.3s at 60 FPS — pause between selection steps

    # System submenu (B / Esc)
    system_menu_items = [
        {"key": "resume", "label": "Resume"},
        {"key": "exit", "label": "Exit launcher"},
        {"key": "shutdown", "label": "Shut down PC"},
        {"key": "reboot", "label": "Reboot PC"},
    ]
    in_system_menu = False
    system_menu_index = 0

    clock = pygame.time.Clock()
    running = True
    trig_page_arm_lt = True
    trig_page_arm_rt = True

    def try_launch_game(g):
        """Launches game g. Returns (exit_launcher, axis_held) or None on skip."""
        platform = g.get("platform")
        process = None
        skip_restore = False
        if platform == "steam":
            if not steam_path:
                if not in_system_menu:
                    print("Steam not found. Specify steam_path in config.json")
                return None
            aid = g.get("steam_app_id")
            if not aid:
                return None
            args = g.get("launch_args") or default_args.get("steam", "-fullscreen")
            process = launch_steam_game(steam_path, aid, args, steam_start_args)
            skip_restore = str(aid) in steam_skip_restore_ids
        elif platform == "epic":
            exe = g.get("exe_path")
            if not exe:
                return None
            args = g.get("launch_args") or default_args.get("epic", "-fullscreen")
            process = launch_epic_game(exe, args)
        elif platform == "nsp":
            nsp_path = g.get("nsp_path")
            if not nsp_path or not os.path.isfile(nsp_path):
                return None
            assoc_cfg = config.get("nsp_use_windows_association")
            if assoc_cfg is None:
                use_association = sys.platform == "win32"
            else:
                use_association = bool(assoc_cfg)
            emu = (config.get("nsp_emulator_path") or "").strip()
            args = g.get("launch_args")
            if args is None:
                extra = (default_args.get("nsp") or config.get("nsp_launch_args") or "").strip()
            else:
                extra = (args or "").strip()
            process = launch_nsp_game(emu, nsp_path, extra, use_association=use_association)
            if process is None and not in_system_menu:
                print(
                    "NSP: launch failed. On Windows set .nsp to open with your emulator (e.g. Ryujinx), "
                    "or set a valid nsp_emulator_path in config.json."
                )
        elif platform == "system":
            action = g.get("system_action")
            if action:
                perform_system_action(action)
                return (True, 0)
            return None
        else:
            return None
        if not process:
            return None
        _yield_for_game_window(2.0)
        if process and platform == "epic":
            _bring_game_to_foreground(process, 12)
        elif process and platform == "steam":
            _bring_game_to_foreground(process, 20)
        elif process and platform == "nsp":
            _bring_game_to_foreground(process, 12)
        elif process:
            _bring_process_window_to_foreground(process.pid)
            _yield_for_game_window(0.5)
            _bring_process_window_to_foreground(process.pid)
        _send_launcher_to_back(hwnd)
        pygame.display.iconify()
        if not skip_restore:
            _wait_for_game_and_restore(process, hwnd, platform)
        return (False, 15)

    # Cache static text surfaces (unchanged each frame)
    title_surface = font_title.render("Select a game or action (gamepad or keyboard)", True, title_color)
    hint_surface = font_title.render(
        "A / Enter — launch   B / Esc — menu   ↑↓ row   PgUp/PgDn   LB/RB   LT/RT — page",
        True,
        title_color,
    )

    def show_launching_overlay(_game_name=None):
        """Blurred overlay with rotating dots: large→small gradient, smooth fade."""
        saved = screen.copy()
        blur_scale = 5
        dim_alpha = 140
        dot_count = 12
        r_max, r_min = 7, 1  # head largest → tail smallest (stronger gradient)
        orbit_radius = 26
        frames = 36
        frame_delay = 0.1
        dim_color = tuple(max(0, min(255, int(c * 0.2))) for c in text_color)
        for i in range(frames):
            # Blur + dark overlay
            small = pygame.transform.smoothscale(saved, (max(1, w // blur_scale), max(1, h // blur_scale)))
            blurred = pygame.transform.smoothscale(small, (w, h))
            screen.blit(blurred, (0, 0))
            dim = pygame.Surface((w, h))
            dim.set_alpha(dim_alpha)
            dim.fill((0, 0, 0))
            screen.blit(dim, (0, 0))
            # Smooth phase for head position (0..dot_count)
            phase = (i / max(1, frames - 1)) * dot_count
            cx, cy = w // 2, h // 2
            for j in range(dot_count):
                # Distance from head along the trail (0 = head, 1, 2... = tail)
                raw = (phase - j) % dot_count
                dist = raw if raw <= dot_count / 2 else dot_count - raw
                if raw > dot_count / 2:
                    dist = 999  # ahead of head: fully dim (use long arc)
                # Size gradient: head largest, tail smallest (smooth over ~6 dots)
                t = min(1.0, dist / 6.0)
                radius = max(r_min, r_max - t * (r_max - r_min))
                # Smoother brightness: quadratic falloff for gentle on/off
                t_soft = t * t  # quadratic = smoother fade
                brightness = max(0.0, 1.0 - t_soft * 1.1)  # 1.0 at head → 0 at tail
                color = tuple(
                    max(0, min(255, int(dim_color[c] + (text_color[c] - dim_color[c]) * brightness)))
                    for c in range(3)
                )
                angle = math.radians(j * (360 / dot_count) - 90)
                x = cx + orbit_radius * math.cos(angle)
                y = cy + orbit_radius * math.sin(angle)
                pygame.draw.circle(screen, color, (int(x), int(y)), max(1, int(radius)))
            pygame.display.flip()
            pygame.event.pump()
            time.sleep(frame_delay)

    while running:
        frames_since_rescan += 1
        if frames_since_rescan >= RESCAN_INTERVAL:
            frames_since_rescan = 0
            joysticks = rescan_joysticks()

        try:
            events = pygame.event.get()
        except (KeyError, SystemError):
            events = []

        for event in events:
            if event.type == pygame.QUIT:
                running = False
            if event.type == getattr(pygame, "JOYDEVICEADDED", None):
                joysticks = rescan_joysticks()
            if event.type == pygame.KEYDOWN:
                if in_system_menu:
                    # System submenu navigation
                    if event.key == pygame.K_ESCAPE:
                        # Close submenu without exiting launcher
                        in_system_menu = False
                    if event.key == pygame.K_UP:
                        system_menu_index = (system_menu_index - 1) % len(system_menu_items)
                    if event.key == pygame.K_DOWN:
                        system_menu_index = (system_menu_index + 1) % len(system_menu_items)
                    if event.key == pygame.K_RETURN:
                        item = system_menu_items[system_menu_index]
                        if item["key"] == "resume":
                            in_system_menu = False
                        elif item["key"] == "exit":
                            running = False
                        elif item["key"] == "shutdown":
                            perform_system_action("shutdown")
                            running = False
                        elif item["key"] == "reboot":
                            perform_system_action("reboot")
                            running = False
                else:
                    if event.key == pygame.K_ESCAPE:
                        # Open system submenu
                        in_system_menu = True
                        system_menu_index = 0
                    if event.key == pygame.K_UP:
                        move_game_selection(-1)
                    if event.key == pygame.K_DOWN:
                        move_game_selection(1)
                    if event.key == pygame.K_PAGEUP:
                        page_scroll(-1)
                    if event.key == pygame.K_PAGEDOWN:
                        page_scroll(1)
                    if event.key == pygame.K_RETURN:
                        it = list_items[selected]
                        if it["kind"] != "game":
                            continue
                        g = it["game"]
                        if g.get("platform") in ("steam", "epic", "nsp"):
                            show_launching_overlay(g.get("name", "Game"))
                        result = try_launch_game(g)
                        if result is not None:
                            should_exit, axis_held_val = result
                            if should_exit:
                                running = False
                                break
                            axis_held = axis_held_val

            if event.type == pygame.JOYBUTTONDOWN:
                if in_system_menu:
                    # Gamepad in system submenu
                    if event.button == BTN_B or event.button == BTN_BACK:
                        # Close submenu
                        in_system_menu = False
                    if event.button == BTN_A or event.button == BTN_START:
                        item = system_menu_items[system_menu_index]
                        if item["key"] == "resume":
                            in_system_menu = False
                        elif item["key"] == "exit":
                            running = False
                        elif item["key"] == "shutdown":
                            perform_system_action("shutdown")
                            running = False
                        elif item["key"] == "reboot":
                            perform_system_action("reboot")
                            running = False
                else:
                    if event.button == BTN_A or event.button == BTN_START:
                        it = list_items[selected]
                        if it["kind"] != "game":
                            continue
                        g = it["game"]
                        if g.get("platform") in ("steam", "epic", "nsp"):
                            show_launching_overlay(g.get("name", "Game"))
                        result = try_launch_game(g)
                        if result is not None:
                            should_exit, axis_held_val = result
                            if should_exit:
                                running = False
                                break
                            axis_held = axis_held_val
                    if event.button == BTN_B or event.button == BTN_BACK:
                        # Open system submenu
                        in_system_menu = True
                        system_menu_index = 0
                    elif event.button == BTN_LB:
                        page_scroll(-1)
                    elif event.button == BTN_RB:
                        page_scroll(1)

            if event.type == pygame.JOYAXISMOTION and event.axis == AXIS_LEFT_Y:
                if axis_held <= 0:
                    if in_system_menu:
                        # System submenu navigation with stick
                        if event.value < -DEADZONE:
                            system_menu_index = (system_menu_index - 1) % len(system_menu_items)
                            axis_held = AXIS_REPEAT_FRAMES
                        elif event.value > DEADZONE:
                            system_menu_index = (system_menu_index + 1) % len(system_menu_items)
                            axis_held = AXIS_REPEAT_FRAMES
                    else:
                        if event.value < -DEADZONE:
                            move_game_selection(-1)
                            axis_held = AXIS_REPEAT_FRAMES
                        elif event.value > DEADZONE:
                            move_game_selection(1)
                            axis_held = AXIS_REPEAT_FRAMES
            elif event.type == pygame.JOYAXISMOTION:
                # LT (axis 4) / RT (axis 5): page up/down on many Xbox-style pads (L2/R2 triggers)
                if not in_system_menu and axis_held <= 0:
                    if event.axis == 5 and event.value > 0.72:
                        if trig_page_arm_rt:
                            page_scroll(1)
                            trig_page_arm_rt = False
                            axis_held = AXIS_REPEAT_FRAMES * 2
                    elif event.axis == 5 and event.value < 0.2:
                        trig_page_arm_rt = True
                    if event.axis == 4 and event.value > 0.72:
                        if trig_page_arm_lt:
                            page_scroll(-1)
                            trig_page_arm_lt = False
                            axis_held = AXIS_REPEAT_FRAMES * 2
                    elif event.axis == 4 and event.value < 0.2:
                        trig_page_arm_lt = True
            if event.type == pygame.JOYHATMOTION and event.hat == 0:
                if axis_held <= 0:
                    if in_system_menu:
                        # System submenu navigation with D-pad
                        if event.value[1] > 0:
                            system_menu_index = (system_menu_index - 1) % len(system_menu_items)
                            axis_held = AXIS_REPEAT_FRAMES
                        elif event.value[1] < 0:
                            system_menu_index = (system_menu_index + 1) % len(system_menu_items)
                            axis_held = AXIS_REPEAT_FRAMES
                    else:
                        if event.value[1] > 0:
                            move_game_selection(-1)
                            axis_held = AXIS_REPEAT_FRAMES
                        elif event.value[1] < 0:
                            move_game_selection(1)
                            axis_held = AXIS_REPEAT_FRAMES

        if axis_held > 0:
            axis_held -= 1

        # Smooth stick navigation only in main list (not in system menu)
        if not in_system_menu and joysticks and axis_held <= 0:
            y = joysticks[0].get_axis(AXIS_LEFT_Y)
            if y < -DEADZONE:
                move_game_selection(-1)
                axis_held = AXIS_REPEAT_FRAMES
            elif y > DEADZONE:
                move_game_selection(1)
                axis_held = AXIS_REPEAT_FRAMES

        # Keep selected row on screen only when navigating with ↑↓ / stick (page scroll must not snap back).
        if list_snap_scroll_to_selection:
            sel_top = cum_starts[selected]
            sel_h = row_specs[selected]["height"]
            sel_bot = sel_top + sel_h
            if sel_top < scroll_y:
                scroll_y = sel_top
            elif sel_bot > scroll_y + viewport_h:
                scroll_y = sel_bot - viewport_h
        scroll_y = max(0, min(scroll_y, max_scroll_y))

        # Rendering
        if bg_surface:
            screen.blit(bg_surface, (0, 0))
        else:
            screen.fill(bg_color)
        screen.blit(title_surface, (60, 40))
        screen.blit(hint_surface, (60, h - list_bottom_margin))

        # Category list with wrapped titles and pixel-based scrolling
        prev_clip = screen.get_clip()
        screen.set_clip(pygame.Rect(0, list_start_y, w, viewport_h))
        try:
            for idx in range(len(list_items)):
                y_content = cum_starts[idx]
                rh = row_specs[idx]["height"]
                screen_y = list_start_y + y_content - scroll_y
                if screen_y + rh < list_start_y or screen_y > list_start_y + viewport_h:
                    continue
                spec = row_specs[idx]
                if spec["kind"] == "header":
                    text = font_category.render("  %s" % spec["title"], True, title_color)
                    screen.blit(text, (60, screen_y))
                else:
                    color = highlight_color if idx == selected else text_color
                    screen.blit(font_list.render(spec["prefix"], True, color), (list_left, screen_y))
                    ly = screen_y
                    for li, chunk in enumerate(spec["name_lines"]):
                        surf = font_list.render(chunk, True, color)
                        screen.blit(surf, (spec["x_text"], ly))
                        ly += list_line_skip
        finally:
            screen.set_clip(prev_clip)

        # Scroll hint arrows
        if max_scroll_y > 0:
            if scroll_y > 0:
                up_arrow = font_list.render(" ▲", True, title_color)
                screen.blit(up_arrow, (w - 50, list_start_y + 4))
            if scroll_y < max_scroll_y:
                down_arrow = font_list.render(" ▼", True, title_color)
                screen.blit(down_arrow, (w - 50, list_start_y + viewport_h - font_list.get_linesize() - 4))

        # System submenu over list
        if in_system_menu:
            menu_width = min(w - 120, 600)
            # Slightly more space at top for header
            menu_height = len(system_menu_items) * line_h + 60
            menu_x = (w - menu_width) // 2
            # Slightly raise submenu above screen center
            menu_y = (h - menu_height) // 2 - 20

            # Submenu background (fully opaque)
            pygame.draw.rect(screen, (0, 0, 0), (menu_x, menu_y, menu_width, menu_height))
            pygame.draw.rect(screen, title_color, (menu_x, menu_y, menu_width, menu_height), 2)

            menu_title = font_title.render("System menu", True, title_color)
            # Center header horizontally and raise within frame
            title_x = menu_x + (menu_width - menu_title.get_width()) // 2
            title_y = menu_y + 2
            screen.blit(menu_title, (title_x, title_y))

            # Spacing between system menu items as in main list
            menu_line_h = line_h

            for idx, item in enumerate(system_menu_items):
                label = item["label"]
                color = highlight_color if idx == system_menu_index else text_color
                text = font_list.render(label, True, color)
                # Shift items below header and center horizontally
                row_y = menu_y + 70 + idx * menu_line_h
                row_x = menu_x + (menu_width - text.get_width()) // 2
                screen.blit(text, (row_x, row_y))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


def _show_error_message(message):
    """Show error dialog (Windows) for visibility when running exe without console."""
    if sys.platform == "win32":
        try:
            from ctypes import windll
            windll.user32.MessageBoxW(0, message, "Joypad Launcher — Error", 0x10)
        except Exception:
            pass


if __name__ == "__main__":
    try:
        run_launcher()
    except BaseException:
        import traceback
        log_path = os.path.join(_BASE_DIR, "launcher_error.log")
        err_text = traceback.format_exc()
        try:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(err_text)
        except Exception:
            pass
        traceback.print_exc()
        _show_error_message(f"Launch error.\nDetails written to:\n{log_path}")
        sys.exit(1)
