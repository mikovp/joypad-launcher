"""Steam library scan filters."""

_STEAM_SKIP_TYPES = frozenset(("tool", "music", "video", "series", "advertising"))
_STEAM_SKIP_NAME_PARTS = (
    "steamworks common redistributables",
    "steam linux runtime",
    "proton ",
    "directx",
    "vc_redist",
    "spacewar",
)


def should_skip_steam_app(name, app_type):
    name_lower = (name or "").lower()
    if any(part in name_lower for part in _STEAM_SKIP_NAME_PARTS):
        return True
    return (app_type or "").lower() in _STEAM_SKIP_TYPES
