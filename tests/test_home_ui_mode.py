from joypad.config.theme.ui import ui_mode_from_theme, ui_mode_label
from joypad.config.settings.toggle import apply_setting_toggle


def test_default_mode_is_home():
    assert ui_mode_from_theme({}) == "home"
    assert ui_mode_from_theme(None) == "home"


def test_explicit_modes_recognized():
    assert ui_mode_from_theme({"ui_mode": "home"}) == "home"
    assert ui_mode_from_theme({"ui_mode": "tiles"}) == "tiles"
    assert ui_mode_from_theme({"ui_mode": "list"}) == "list"


def test_label():
    assert ui_mode_label("home") == "Home"
    assert ui_mode_label("tiles") == "Tiles"
    assert ui_mode_label("list") == "List"


def test_toggle_cycles_home_tiles_list(tmp_path, monkeypatch):
    import joypad.config.settings.toggle as tg
    monkeypatch.setattr(tg, "save_config", lambda cfg: None)
    cfg = {"theme": {"ui_mode": "home"}}
    apply_setting_toggle(cfg, "ui_mode")
    assert cfg["theme"]["ui_mode"] == "tiles"
    apply_setting_toggle(cfg, "ui_mode")
    assert cfg["theme"]["ui_mode"] == "list"
    apply_setting_toggle(cfg, "ui_mode")
    assert cfg["theme"]["ui_mode"] == "home"
