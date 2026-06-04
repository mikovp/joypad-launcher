from joypad.config.types import LauncherConfig, ThemeConfig


def test_theme_config_accepts_ui_mode():
    theme: ThemeConfig = {"ui_mode": "tiles", "tile_scale": 2.5}
    assert theme["ui_mode"] == "tiles"


def test_launcher_config_shape():
    cfg: LauncherConfig = {
        "auto_scan": True,
        "steam_path": r"C:\Steam\steam.exe",
        "theme": {"background": "#14141c"},
    }
    assert cfg["auto_scan"] is True
    assert cfg["theme"]["background"] == "#14141c"
