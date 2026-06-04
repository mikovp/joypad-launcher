"""Placeholder cover surfaces when no art is available."""

from joypad.covers.cache.constants import _PLATFORM_COLORS, _PLATFORM_LABEL
from joypad.integrations.twitch import normalize_platform


def make_placeholder(pygame, game, size):
    platform = normalize_platform(game.get("platform"))
    if platform not in _PLATFORM_COLORS:
        platform = "steam"
    w, h = size
    surf = pygame.Surface((w, h))
    surf.fill(_PLATFORM_COLORS.get(platform, (45, 45, 55)))
    try:
        font_sm = pygame.font.SysFont("Segoe UI", max(11, min(w, h) // 8), bold=True)
        font_lg = pygame.font.SysFont("Segoe UI", max(16, min(w, h) // 5), bold=True)
        badge = font_sm.render(_PLATFORM_LABEL.get(platform, platform), True, (230, 230, 240))
        surf.blit(badge, (6, 6))
        name = (game.get("name") or "?").strip()
        short = name[:1].upper() if name else "?"
        letter = font_lg.render(short, True, (240, 240, 250))
        surf.blit(letter, ((w - letter.get_width()) // 2, (h - letter.get_height()) // 2))
    except Exception:
        pass
    if surf.get_size() == size:
        return surf.convert()
    return pygame.transform.smoothscale(surf, size).convert()
