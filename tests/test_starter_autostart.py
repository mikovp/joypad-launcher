"""Tests for gamepad starter command and autostart setting."""

from joypad.cli import GAMEPAD_STARTER_FLAG
from joypad.config.settings import apply_setting_toggle
from joypad.starter.command import (
    LAUNCHER_EXE_NAME,
    STARTER_EXE_NAME,
    format_gamepad_starter_command,
    gamepad_starter_command,
    launcher_command,
)


def test_gamepad_starter_command_dev_includes_flag():
    assert GAMEPAD_STARTER_FLAG in gamepad_starter_command()


def test_format_gamepad_starter_command_dev_includes_flag():
    assert GAMEPAD_STARTER_FLAG in format_gamepad_starter_command()


def test_frozen_starter_uses_separate_exes(monkeypatch, tmp_path):
    launcher = tmp_path / LAUNCHER_EXE_NAME
    starter_dir = tmp_path / "JoypadStarter"
    starter_dir.mkdir()
    starter = starter_dir / STARTER_EXE_NAME
    launcher.write_bytes(b"")
    starter.write_bytes(b"")
    monkeypatch.setattr("joypad.starter.command._BASE_DIR", str(tmp_path))
    monkeypatch.setattr("joypad.starter.command.sys.frozen", True, raising=False)
    monkeypatch.setattr("joypad.starter.command.sys.executable", str(starter))

    assert gamepad_starter_command() == [str(starter)]
    assert launcher_command() == [str(launcher)]
    assert GAMEPAD_STARTER_FLAG not in format_gamepad_starter_command()
    assert format_gamepad_starter_command() == str(starter)


def test_apply_toggle_gamepad_starter_autostart(monkeypatch):
    monkeypatch.setattr("joypad.config.settings.toggle.save_config", lambda config: None)
    monkeypatch.setattr("sys.platform", "win32")
    monkeypatch.setattr(
        "joypad.platform.windows.autostart.is_gamepad_starter_autostart_registered",
        lambda: False,
    )
    monkeypatch.setattr(
        "joypad.platform.windows.autostart.is_gamepad_starter_running",
        lambda: False,
    )
    calls = []
    monkeypatch.setattr(
        "joypad.platform.windows.autostart.set_gamepad_starter_autostart",
        lambda enabled: calls.append(enabled) or True,
    )
    config = {"theme": {}, "ddcci": {}}
    assert apply_setting_toggle(config, "gamepad_starter_autostart") is True
    assert config["gamepad_starter"]["autostart"] is True
    assert calls == [True]


def test_apply_toggle_gamepad_starter_autostart_registry_failure(monkeypatch):
    monkeypatch.setattr("joypad.config.settings.toggle.save_config", lambda config: None)
    monkeypatch.setattr("sys.platform", "win32")
    monkeypatch.setattr(
        "joypad.platform.windows.autostart.is_gamepad_starter_autostart_registered",
        lambda: False,
    )
    monkeypatch.setattr(
        "joypad.platform.windows.autostart.is_gamepad_starter_running",
        lambda: False,
    )
    monkeypatch.setattr(
        "joypad.platform.windows.autostart.set_gamepad_starter_autostart",
        lambda enabled: False,
    )
    config = {"theme": {}, "ddcci": {}}
    assert apply_setting_toggle(config, "gamepad_starter_autostart") is False
    assert "gamepad_starter" not in config


def test_ensure_gamepad_starter_running_spawns_when_missing(monkeypatch):
    monkeypatch.setattr(
        "joypad.platform.windows.autostart.is_gamepad_starter_autostart_registered",
        lambda: True,
    )
    monkeypatch.setattr(
        "joypad.platform.windows.autostart.is_gamepad_starter_running",
        lambda: False,
    )
    stops = []
    starts = []
    monkeypatch.setattr(
        "joypad.platform.windows.autostart._stop_all_starters",
        lambda: stops.append(True),
    )
    monkeypatch.setattr(
        "joypad.platform.windows.autostart._start_gamepad_starter_process",
        lambda: starts.append(True) or True,
    )
    monkeypatch.setattr("joypad.platform.windows.autostart.time.sleep", lambda _s: None)
    from joypad.platform.windows.autostart import ensure_gamepad_starter_running

    assert ensure_gamepad_starter_running() is True
    assert stops == [True]
    assert starts == [True]


def test_ensure_gamepad_starter_running_skips_when_running(monkeypatch):
    monkeypatch.setattr(
        "joypad.platform.windows.autostart.is_gamepad_starter_autostart_registered",
        lambda: True,
    )
    monkeypatch.setattr(
        "joypad.platform.windows.autostart.is_gamepad_starter_running",
        lambda: True,
    )

    def _fail():
        raise AssertionError("should not restart")

    monkeypatch.setattr("joypad.platform.windows.autostart._stop_all_starters", _fail)
    monkeypatch.setattr("joypad.platform.windows.autostart._start_gamepad_starter_process", _fail)
    from joypad.platform.windows.autostart import ensure_gamepad_starter_running

    assert ensure_gamepad_starter_running() is True
