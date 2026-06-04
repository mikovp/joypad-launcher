"""Tests for platform integrations."""

from joypad.integrations import LAUNCHABLE_PLATFORMS, launch_twitch_game
from joypad.integrations.twitch import normalize_platform, scan_twitch_games


def test_launchable_platforms():
    assert LAUNCHABLE_PLATFORMS == frozenset({"steam", "epic", "twitch"})


def test_normalize_platform_nsp_is_twitch():
    assert normalize_platform("nsp") == "twitch"
    assert normalize_platform("twitch") == "twitch"


def test_scan_twitch_games_empty_for_missing_folder():
    assert scan_twitch_games("") == []
    assert scan_twitch_games("/nonexistent/path") == []


def test_launch_twitch_requires_valid_nsp_path(tmp_path):
    assert launch_twitch_game("", str(tmp_path / "missing.nsp"), "") is None
