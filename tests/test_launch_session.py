"""Tests for launch session callbacks."""

from unittest.mock import patch

from joypad.app_state import AppState
from joypad.launch.session import LaunchSession, make_on_launch
from joypad.ui.loop import LoopContext


def _session():
    return LaunchSession(
        steam_path="C:/Steam",
        default_args={},
        steam_skip_restore_ids=set(),
        hwnd=None,
        active_remap_proc=[None],
    )


def test_on_launch_no_selection_returns_false():
    state = AppState()
    state.ui_mode = "list"
    state.list_items = []
    state.selected = 0
    loop_ctx = LoopContext()

    on_launch = make_on_launch(state, _session(), loop_ctx)
    assert on_launch() is False


@patch("joypad.launch.session.try_launch_game", return_value=(True, 42))
@patch("joypad.launch.session.ovl.begin_launching_overlay", return_value=(None, 0))
def test_on_launch_steam_game_delegates_to_try_launch(mock_overlay, mock_try):
    state = AppState()
    state.ui_mode = "list"
    game = {"name": "Test Game", "platform": "steam", "id": "123"}
    state.list_items = [{"kind": "game", "game": game}]
    state.selected = 0
    loop_ctx = LoopContext()

    on_launch = make_on_launch(state, _session(), loop_ctx)
    assert on_launch() is True
    assert loop_ctx.axis_held == 42
    mock_overlay.assert_called_once_with(state, "Test Game")
    mock_try.assert_called_once()
    assert mock_try.call_args[0][0] == game


@patch("joypad.launch.session.try_launch_game", return_value=(False, 0))
def test_on_launch_twitch_game_shows_overlay(mock_try):
    state = AppState()
    state.ui_mode = "list"
    game = {"name": "Zelda", "platform": "twitch", "nsp_path": r"C:\roms\zelda.nsp"}
    state.list_items = [{"kind": "game", "game": game}]
    state.selected = 0
    loop_ctx = LoopContext()

    with patch("joypad.launch.session.ovl.begin_launching_overlay", return_value=(None, 0)) as mock_overlay:
        on_launch = make_on_launch(state, _session(), loop_ctx)
        assert on_launch() is False
        mock_overlay.assert_called_once_with(state, "Zelda")
    mock_try.assert_called_once()


@patch("joypad.launch.session.try_launch_game", return_value=(False, 0))
def test_on_launch_non_platform_game_skips_overlay(mock_try):
    state = AppState()
    state.ui_mode = "list"
    game = {"name": "Folder", "platform": "folder"}
    state.list_items = [{"kind": "game", "game": game}]
    state.selected = 0
    loop_ctx = LoopContext()

    with patch("joypad.launch.session.ovl.begin_launching_overlay") as mock_overlay:
        on_launch = make_on_launch(state, _session(), loop_ctx)
        assert on_launch() is False
        mock_overlay.assert_not_called()
    mock_try.assert_called_once()
