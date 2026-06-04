import joypad.config.settings as settings_mod
from joypad.config.settings import (
    _cycle_option,
    apply_setting_toggle,
    build_settings_menu,
)


def test_cycle_option_wraps_around():
    opts = [1.0, 1.5, 2.0]
    assert _cycle_option(1.0, opts) == 1.5
    assert _cycle_option(1.5, opts) == 2.0
    assert _cycle_option(2.0, opts) == 1.0


def test_cycle_option_unknown_returns_first():
    assert _cycle_option(99, [1.0, 1.5, 2.0]) == 1.0


def test_cycle_option_float_approx_match():
    # current within 0.001 of an option matches that option (float branch)
    assert _cycle_option(1.0001, [1.0, 1.5, 2.0]) == 1.5


def _no_save(monkeypatch):
    monkeypatch.setattr(settings_mod, "save_config", lambda config: None)


def test_apply_toggle_ddcci_power(monkeypatch):
    _no_save(monkeypatch)
    config = {"theme": {}, "ddcci": {}}
    assert apply_setting_toggle(config, "ddcci_power") is True
    assert config["ddcci"]["power_off_on_start"] is True
    assert apply_setting_toggle(config, "ddcci_power") is True
    assert config["ddcci"]["power_off_on_start"] is False


def test_apply_toggle_ui_mode(monkeypatch):
    _no_save(monkeypatch)
    config = {"theme": {}, "ddcci": {}}
    assert apply_setting_toggle(config, "ui_mode") is True
    assert config["theme"]["ui_mode"] == "tiles"
    assert apply_setting_toggle(config, "ui_mode") is True
    assert config["theme"]["ui_mode"] == "list"


def test_apply_toggle_auto_scan(monkeypatch):
    _no_save(monkeypatch)
    config = {"theme": {}, "ddcci": {}}
    assert apply_setting_toggle(config, "auto_scan") is True
    assert config["auto_scan"] is True


def test_apply_toggle_steam_silent(monkeypatch):
    _no_save(monkeypatch)
    config = {"theme": {}, "ddcci": {}}
    assert apply_setting_toggle(config, "steam_silent") is True
    assert config["steam_start_args"] == "-silent"
    assert apply_setting_toggle(config, "steam_silent") is True
    assert config["steam_start_args"] == ""


def test_apply_toggle_cdn_covers(monkeypatch):
    _no_save(monkeypatch)
    config = {"theme": {}, "ddcci": {}}
    # default is treated as True, so first toggle flips to False
    assert apply_setting_toggle(config, "cdn_covers") is True
    assert config["theme"]["cdn_covers"] is False


def test_apply_toggle_unknown_and_back(monkeypatch):
    _no_save(monkeypatch)
    config = {"theme": {}, "ddcci": {}}
    assert apply_setting_toggle(config, "totally_unknown") is False
    assert apply_setting_toggle(config, "back") is False
    assert config == {"theme": {}, "ddcci": {}}


def test_build_settings_menu_structure():
    config = {"theme": {}, "ddcci": {}}
    items = build_settings_menu(config)
    assert items[0]["kind"] == "header"
    assert items[-1] == {"kind": "action", "key": "back", "label": "Back"}
    setting_keys = {i["key"] for i in items if i["kind"] == "setting"}
    assert "ui_mode" in setting_keys
    assert "tile_scale" in setting_keys
    assert "cdn_covers" in setting_keys
    kinds = {i["kind"] for i in items}
    assert kinds == {"header", "setting", "action"}
