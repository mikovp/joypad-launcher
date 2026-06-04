"""Twitch platform id and game entry normalization."""

from __future__ import annotations

PLATFORM = "twitch"


def normalize_platform(platform: str | None) -> str:
    """Legacy config entries used platform \"nsp\" for the same integration."""
    p = (platform or "").lower()
    return PLATFORM if p == "nsp" else p


def normalize_game_entry(game: dict) -> dict:
    """Return a copy with platform normalized to twitch when applicable."""
    if normalize_platform(game.get("platform")) == PLATFORM and game.get("platform") != PLATFORM:
        out = dict(game)
        out["platform"] = PLATFORM
        return out
    return game
