"""Tests for Twitch config keys and legacy nsp_* fallback."""

from joypad.config.twitch import (
    ensure_twitch_config_keys,
    get_twitch_fullscreen_args,
    get_twitch_launch_args,
    get_twitch_roms_folder,
    get_twitch_use_windows_association,
    set_twitch_use_windows_association,
)


def test_legacy_nsp_roms_folder_fallback():
    cfg = {"nsp_roms_folder": r"\\share\roms"}
    assert get_twitch_roms_folder(cfg) == r"\\share\roms"


def test_twitch_roms_folder_preferred_over_legacy():
    cfg = {
        "twitch_roms_folder": r"C:\new",
        "nsp_roms_folder": r"C:\old",
    }
    assert get_twitch_roms_folder(cfg) == r"C:\new"


def test_ensure_twitch_config_keys_migrates_in_memory():
    cfg = {
        "nsp_roms_folder": r"\\share",
        "nsp_emulator_path": r"C:\emu.exe",
        "nsp_launch_args": "-f",
        "nsp_use_windows_association": False,
        "fullscreen_args": {"steam": "-fullscreen", "nsp": "--fullscreen"},
    }
    ensure_twitch_config_keys(cfg)
    assert cfg["twitch_roms_folder"] == r"\\share"
    assert cfg["twitch_emulator_path"] == r"C:\emu.exe"
    assert cfg["twitch_launch_args"] == "-f"
    assert cfg["twitch_use_windows_association"] is False
    assert cfg["fullscreen_args"]["twitch"] == "--fullscreen"


def test_get_twitch_launch_args_and_fullscreen():
    cfg = {"twitch_launch_args": "--foo"}
    assert get_twitch_launch_args(cfg) == "--foo"
    assert get_twitch_fullscreen_args({"twitch": "-bar"}) == "-bar"
    assert get_twitch_fullscreen_args({"nsp": "-legacy"}) == "-legacy"


def test_set_twitch_use_windows_association():
    cfg = {}
    set_twitch_use_windows_association(cfg, True)
    assert get_twitch_use_windows_association(cfg) is True
