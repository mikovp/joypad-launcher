"""Disk cache and background prefetch for remote cover art."""

import json
import os
import threading
import time

from joypad.covers.cdn.http import cache_filename, download_url
from joypad.covers.cdn.sources import cdn_urls_for_game, rawg_fetch_url


class CdnCoverStore:
    """Fetches remote cover images once and stores them under cache_dir."""

    def __init__(self, cache_dir, enabled=True, rawg_api_key=None, timeout=12):
        self.enabled = bool(enabled)
        self.cache_dir = cache_dir
        self.rawg_api_key = (rawg_api_key or "").strip() or None
        self.timeout = timeout
        self._session_failed = set()
        self._steam_search_cache = {}
        self._lock = threading.Lock()
        if self.enabled and cache_dir:
            os.makedirs(cache_dir, exist_ok=True)
            self._load_steam_search_cache()

    def _steam_search_path(self):
        if not self.cache_dir:
            return None
        return os.path.join(self.cache_dir, "_steam_search.json")

    def _load_steam_search_cache(self):
        path = self._steam_search_path()
        if not path or not os.path.isfile(path):
            return
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                self._steam_search_cache.update(data)
        except Exception:
            pass

    def _save_steam_search_cache(self):
        path = self._steam_search_path()
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._steam_search_cache, f, ensure_ascii=False, indent=0)
        except OSError:
            pass

    def cache_path(self, game, cache_key):
        if not self.cache_dir:
            return None
        return os.path.join(self.cache_dir, cache_filename(cache_key[0], cache_key[1]))

    def get_cached_file(self, game, cache_key):
        path = self.cache_path(game, cache_key)
        if path and os.path.isfile(path) and os.path.getsize(path) > 200:
            return path
        return None

    def fetch(self, game, cache_key):
        if not self.enabled or not self.cache_dir:
            return None
        if cache_key in self._session_failed:
            return None

        existing = self.get_cached_file(game, cache_key)
        if existing:
            return existing

        dest = self.cache_path(game, cache_key)
        if not dest:
            return None

        for url in cdn_urls_for_game(game, self._steam_search_cache):
            if download_url(url, dest, self.timeout):
                self._save_steam_search_cache()
                return dest

        if self.rawg_api_key:
            rawg_url = rawg_fetch_url(game, self.rawg_api_key, self.timeout)
            if rawg_url and download_url(rawg_url, dest, self.timeout):
                return dest

        with self._lock:
            self._session_failed.add(cache_key)
        return None

    def prefetch(self, games, cache_key_fn, on_ready=None):
        """Background download. cache_key_fn(game) -> hashable key tuple."""
        if not self.enabled or not games:
            return

        def worker():
            for i, game in enumerate(games):
                try:
                    key = cache_key_fn(game)
                except Exception:
                    continue
                if key in self._session_failed:
                    continue
                if self.get_cached_file(game, key):
                    continue
                path = self.fetch(game, key)
                if path and on_ready:
                    try:
                        on_ready(game)
                    except Exception:
                        pass
                if i < len(games) - 1:
                    time.sleep(0.15)

        threading.Thread(target=worker, daemon=True).start()
