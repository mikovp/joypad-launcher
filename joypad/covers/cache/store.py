"""CoverCache: local files, Steam cache, CDN disk cache."""

import os
import threading

try:
    import pygame
except ImportError:
    pygame = None

from joypad.covers.cache.local import cover_candidates, game_cache_key
from joypad.covers.cache.placeholder import make_placeholder
from joypad.covers.cdn import CdnCoverStore


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
        self._cdn.prefetch(games, game_cache_key, on_ready=self._cdn_ready)

    def _cdn_ready(self, game):
        key = game_cache_key(game)
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
        key = game_cache_key(game)
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
        key = game_cache_key(game)
        for path in cover_candidates(game, self.covers_dir, self.steam_dir):
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

        return make_placeholder(pygame, game, size)
