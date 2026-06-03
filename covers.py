# -*- coding: utf-8 -*-
"""Game cover art: local files, Steam cache, CDN disk cache, placeholders."""

import glob
import os
import re
import threading

try:
    import pygame
except ImportError:
    pygame = None

from cover_cdn import CdnCoverStore, nsp_cover_stems

_PLATFORM_COLORS = {
    "steam": (35, 55, 85),
    "epic": (70, 55, 35),
    "nsp": (85, 45, 110),
}
_PLATFORM_LABEL = {
    "steam": "Steam",
    "epic": "Epic",
    "nsp": "Switch",
}


def _sanitize_filename(name):
    if not name:
        return "game"
    s = re.sub(r'[<>:"/\\|?*]', "_", str(name).strip())
    return s[:120] if s else "game"


def _steam_cover_path(steam_dir, app_id):
    if not steam_dir or not app_id:
        return None
    cache = os.path.join(steam_dir, "appcache", "librarycache")
    if not os.path.isdir(cache):
        return None
    app_id = str(app_id)
    for name in (
        "%s_library_600x900.jpg" % app_id,
        "%s_library_hero.jpg" % app_id,
        "%s_header.jpg" % app_id,
        "%s_logo.png" % app_id,
    ):
        path = os.path.join(cache, name)
        if os.path.isfile(path):
            return path
    for pattern in ("%s_*.jpg" % app_id, "%s_*.png" % app_id):
        hits = sorted(glob.glob(os.path.join(cache, pattern)))
        if hits:
            return hits[0]
    sub = os.path.join(cache, app_id)
    if os.path.isdir(sub):
        for name in ("library_600x900.jpg", "library_hero.jpg", "header.jpg"):
            path = os.path.join(sub, name)
            if os.path.isfile(path):
                return path
    return None


def _cover_candidates(game, covers_dir, steam_dir):
    """Ordered local paths to try (no network)."""
    platform = (game.get("platform") or "").lower()
    name = game.get("name") or "Game"
    safe = _sanitize_filename(name)
    paths = []

    if covers_dir and os.path.isdir(covers_dir):
        if platform == "steam" and game.get("steam_app_id"):
            aid = str(game["steam_app_id"])
            for stem in (aid, "steam_%s" % aid, safe):
                for ext in (".jpg", ".jpeg", ".png", ".webp"):
                    paths.append(os.path.join(covers_dir, stem + ext))
        elif platform == "epic" and game.get("exe_path"):
            base = os.path.splitext(os.path.basename(game["exe_path"]))[0]
            for stem in (_sanitize_filename(base), safe, "epic_%s" % _sanitize_filename(base)):
                for ext in (".jpg", ".jpeg", ".png", ".webp"):
                    paths.append(os.path.join(covers_dir, stem + ext))
        elif platform == "nsp" and game.get("nsp_path"):
            for stem in nsp_cover_stems(game):
                safe_stem = _sanitize_filename(stem)
                for s in (stem, safe_stem):
                    for ext in (".jpg", ".jpeg", ".png", ".webp"):
                        paths.append(os.path.join(covers_dir, s + ext))
        elif platform != "nsp":
            for ext in (".jpg", ".jpeg", ".png", ".webp"):
                paths.append(os.path.join(covers_dir, safe + ext))

    if platform == "steam" and steam_dir and game.get("steam_app_id"):
        sp = _steam_cover_path(steam_dir, game["steam_app_id"])
        if sp:
            paths.append(sp)

    seen = set()
    out = []
    for p in paths:
        key = p.lower()
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


def _game_cache_key(game):
    platform = (game.get("platform") or "").lower()
    if platform == "steam" and game.get("steam_app_id"):
        return ("steam", str(game["steam_app_id"]))
    if platform == "epic" and game.get("exe_path"):
        return ("epic", os.path.normcase(game["exe_path"]))
    if platform == "nsp" and game.get("nsp_path"):
        return ("nsp", os.path.normcase(game["nsp_path"]))
    return (platform, game.get("name") or "")


class CoverCache:
    """Loads and scales cover surfaces; local first, then CDN disk cache."""

    def __init__(
        self,
        base_dir,
        steam_dir=None,
        covers_subdir="covers",
        cdn_enabled=True,
        cdn_cache_subdir="cover_cdn_cache",
        rawg_api_key=None,
    ):
        self.base_dir = base_dir
        self.steam_dir = steam_dir
        self.covers_dir = (
            os.path.join(base_dir, covers_subdir)
            if covers_subdir and not os.path.isabs(covers_subdir)
            else (covers_subdir or "")
        )
        if self.covers_dir and not os.path.isdir(self.covers_dir):
            self.covers_dir = None
        self._scaled = {}
        self._source_hit = {}
        cdn_dir = (
            os.path.join(base_dir, cdn_cache_subdir)
            if cdn_cache_subdir and not os.path.isabs(cdn_cache_subdir)
            else (cdn_cache_subdir or "")
        )
        self._cdn = CdnCoverStore(
            cdn_dir,
            enabled=cdn_enabled,
            rawg_api_key=rawg_api_key,
        )
        self._on_cdn_ready = None
        self._fetch_scheduled = set()

    def set_on_cdn_ready(self, callback):
        """callback(game) — e.g. clear scaled cache so next frame reloads art."""
        self._on_cdn_ready = callback

    def prefetch_async(self, games):
        self._cdn.prefetch(games, _game_cache_key, on_ready=self._cdn_ready)

    def _cdn_ready(self, game):
        key = _game_cache_key(game)
        self._scaled = {k: v for k, v in self._scaled.items() if k[0] != key}
        if self._on_cdn_ready:
            try:
                self._on_cdn_ready(game)
            except Exception:
                pass

    def _maybe_fetch_async(self, game, key):
        if not self._cdn.enabled or key in self._fetch_scheduled:
            return
        if self._cdn.get_cached_file(game, key):
            return
        self._fetch_scheduled.add(key)

        def run():
            try:
                self._cdn.fetch(game, key)
            finally:
                self._fetch_scheduled.discard(key)
            self._cdn_ready(game)

        threading.Thread(target=run, daemon=True).start()

    def get(self, game, width, height):
        if pygame is None:
            return None
        key = _game_cache_key(game)
        self._maybe_fetch_async(game, key)
        size = (max(1, int(width)), max(1, int(height)))
        cache_key = (key, size)
        if cache_key in self._scaled:
            return self._scaled[cache_key]
        surf = self._load_scaled(game, size)
        self._scaled[cache_key] = surf
        return surf

    def _load_image_file(self, path, size, key):
        try:
            img = pygame.image.load(path)
            img = pygame.transform.smoothscale(img, size)
            self._source_hit[key] = path
            return img.convert_alpha() if img.get_flags() & pygame.SRCALPHA else img.convert()
        except Exception:
            return None

    def _load_scaled(self, game, size):
        key = _game_cache_key(game)
        for path in _cover_candidates(game, self.covers_dir, self.steam_dir):
            if not os.path.isfile(path):
                continue
            surf = self._load_image_file(path, size, key)
            if surf:
                return surf

        cdn_path = self._cdn.get_cached_file(game, key)
        if cdn_path and os.path.isfile(cdn_path):
            surf = self._load_image_file(cdn_path, size, key)
            if surf:
                return surf

        return self._placeholder(game, size)

    def _placeholder(self, game, size):
        platform = (game.get("platform") or "").lower()
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
