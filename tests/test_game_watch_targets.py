"""Tests for game exit watch targets."""

from joypad.input.watch.targets import game_watch_targets, game_watch_title


def test_game_watch_targets_epic():
    exe = r"C:\Games\Foo\Bar.exe"
    watch_exe, watch_dir = game_watch_targets({"platform": "epic", "exe_path": exe})
    assert watch_exe == "Bar.exe"
    assert watch_dir.endswith("Foo")


def test_game_watch_targets_steam_empty():
    assert game_watch_targets({"platform": "steam", "steam_app_id": "123"}) == (None, None)


def test_game_watch_title_steam():
    assert game_watch_title({"platform": "steam", "name": "Balatro"}) == "Balatro"
    assert game_watch_title({"platform": "steam", "name": "Go"}) is None
    assert game_watch_title({"platform": "epic", "name": "Long Name"}) is None
