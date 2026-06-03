# -*- coding: utf-8 -*-
"""
Download cover art from free public sources into a local disk cache.
No API keys required (Steam store search, Steam CDN, Libretro, Wikipedia).
"""

import hashlib
import json
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

_USER_AGENT = "JoypadLauncher/1.0"

_STEAM_CDN_TEMPLATES = (
    "https://cdn.cloudflare.steamstatic.com/steam/apps/{id}/library_600x900.jpg",
    "https://cdn.cloudflare.steamstatic.com/steam/apps/{id}/library_hero.jpg",
    "https://cdn.cloudflare.steamstatic.com/steam/apps/{id}/header.jpg",
    "https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/{id}/library_600x900.jpg",
    "https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/{id}/library_hero.jpg",
    "https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/{id}/header.jpg",
)

_STEAM_STORE_SEARCH = "https://store.steampowered.com/api/storesearch/?term={term}&l=english&cc=US"

# Libretro thumbnail CDN (free, no key) — try several platform folders by game name.
_LIBRETRO_PLATFORMS = (
    "Nintendo - Nintendo Switch",
    "Sony - PlayStation 4",
    "Sony - PlayStation 3",
    "Sony - PlayStation 2",
    "Microsoft - Xbox 360",
    "Microsoft - Xbox",
    "Nintendo - Wii U",
    "Nintendo - Wii",
    "Nintendo - GameCube",
    "Nintendo - Nintendo 64",
    "Nintendo - Super Nintendo Entertainment System",
    "Sega - Dreamcast",
    "Nintendo - Nintendo DS",
    "Nintendo - Game Boy Advance",
)

_LIBRETRO_ART_KIND = ("Named_Boxarts", "Named_Titles")

_LIBRETRO_SWITCH_ONLY = (
    "https://thumbnails.libretro.com/Nintendo%20-%20Nintendo%20Switch/Named_Boxarts/{name}.png",
    "https://thumbnails.libretro.com/Nintendo%20-%20Nintendo%20Switch/Named_Titles/{name}.png",
)


def _looks_like_image(data):
    if not data or len(data) < 200:
        return False
    if data[:3] == b"\xff\xd8\xff":
        return True
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return True
    if data[:4] == b"RIFF" and len(data) > 12 and data[8:12] == b"WEBP":
        return True
    return False


def _http_json(url, timeout=12):
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception:
        return None


def _download_url(url, dest_path, timeout=12):
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if getattr(resp, "status", 200) != 200:
                return False
            data = resp.read()
    except (urllib.error.URLError, OSError, TimeoutError):
        return False
    if not _looks_like_image(data):
        return False
    tmp = dest_path + ".part"
    try:
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, dest_path)
        return True
    except OSError:
        try:
            if os.path.isfile(tmp):
                os.remove(tmp)
        except OSError:
            pass
        return False


def _cache_filename(platform, stable_id):
    digest = hashlib.sha1(str(stable_id).encode("utf-8", errors="replace")).hexdigest()[:16]
    safe_plat = re.sub(r"[^a-z0-9]", "", (platform or "x").lower())[:12]
    return "%s_%s.jpg" % (safe_plat, digest)


def _nsp_art_name(game):
    """NSP cover lookup uses the .nsp filename (stem), not the folder display name."""
    path = game.get("nsp_path") or ""
    return os.path.splitext(os.path.basename(path))[0]


# NSP filenames on disk (examples from user library):
#   Super Mario Bros. Wonder [010015100B514000][v0].nsp
#   No Mans Sky [0100853015E86800][v4915200].nsp
#   STALKER ... [01004A001E32E000][v0] (7.41 GB).nsp
_NSP_DUMP_SUFFIX_RE = re.compile(
    r"\s*"
    r"(?:\[[0-9A-Fa-f]{16}\]\s*\[v\d+\])"  # Switch title ID + version
    r"(?:\s*\([\d.]+\s*(?:GB|MB|GiB|MiB)\))?"  # optional "(7.41 GB)"
    r"\s*$",
    re.IGNORECASE,
)
_NSP_SIZE_SUFFIX_RE = re.compile(
    r"\s*\([\d.]+\s*(?:GB|MB|GiB|MiB)\)\s*$",
    re.IGNORECASE,
)
_NSP_TITLE_ID_RE = re.compile(r"\[([0-9A-Fa-f]{16})\]")


def _nsp_title_id_cdn_urls(stem):
    """Switch cover by 16-digit title ID embedded in the .nsp filename."""
    m = _NSP_TITLE_ID_RE.search(stem or "")
    if not m:
        return []
    tid = m.group(1).upper()
    return ["https://tinfoil.media/ti/%s/0/0" % tid]


def _nsp_title_aliases(title):
    """
    Extra search names when the filename omits punctuation (e.g. STALKER vs S.T.A.L.K.E.R.).
    """
    aliases = []
    t = (title or "").strip()
    if not t:
        return aliases

    if re.match(r"^STALKER\b", t, re.I) and "S.T.A.L.K.E.R" not in t.upper():
        dotted = re.sub(r"^STALKER\b", "S.T.A.L.K.E.R.", t, count=1, flags=re.I)
        aliases.append(dotted)
        if ":" not in dotted:
            aliases.append(re.sub(r"^S\.T\.A\.L\.K\.E\.R\.\s+", "S.T.A.L.K.E.R.: ", dotted, count=1))

    if "chornobyl" in t.lower():
        aliases.append(re.sub(r"chornobyl", "Chernobyl", t, flags=re.I))
    if "chernobyl" in t.lower() and "chornobyl" not in t.lower():
        aliases.append(re.sub(r"chernobyl", "Chornobyl", t, flags=re.I))

    return aliases


def nsp_cover_stems(game):
    """
    Variants from the .nsp filename only (not the folder display name in the list).
    """
    stem = (game.get("nsp_filename") or _nsp_art_name(game) or "").strip()
    if not stem:
        return []

    seen = set()
    out = []

    def add(val):
        val = (val or "").strip()
        if not val:
            return
        key = val.lower()
        if key not in seen:
            seen.add(key)
            out.append(val)

    add(stem)
    no_dump = _NSP_DUMP_SUFFIX_RE.sub("", stem).strip()
    if no_dump:
        add(no_dump)
    no_size = _NSP_SIZE_SUFFIX_RE.sub("", no_dump or stem).strip()
    if no_size:
        add(no_size)
    head = stem.split("[", 1)[0].strip() if "[" in stem else ""
    if head:
        add(head)

    for base in (no_dump, no_size, head):
        if not base:
            continue
        for alt in _nsp_title_aliases(base):
            add(alt)

    return out


def _art_name_variants(game):
    """Names to try on Libretro / Steam search / Wikipedia."""
    if (game.get("platform") or "").lower() == "nsp":
        return nsp_cover_stems(game)

    seen = set()
    out = []

    def add(val):
        val = (val or "").strip()
        if not val:
            return
        key = val.lower()
        if key not in seen:
            seen.add(key)
            out.append(val)

    add(game.get("name"))
    name = (game.get("name") or "").strip()
    if " / " in name:
        add(name.split(" / ")[-1])
    exe = game.get("exe_path")
    if exe:
        add(os.path.splitext(os.path.basename(exe))[0])
    return out


def _steam_cdn_urls(app_id):
    aid = str(app_id)
    return [tpl.format(id=aid) for tpl in _STEAM_CDN_TEMPLATES]


def _steam_store_search_app_id(name, timeout=12, cache=None):
    """
    Free Steam store search API (no key). Returns app id string or None.
    """
    if not name:
        return None
    key = name.strip().lower()
    if cache is not None and key in cache:
        return cache[key]

    url = _STEAM_STORE_SEARCH.format(term=urllib.parse.quote(name.strip()))
    data = _http_json(url, timeout)
    if not data:
        if cache is not None:
            cache[key] = None
        return None

    items = data.get("items") or []
    app_id = None
    name_l = key
    for item in items:
        if not isinstance(item, dict):
            continue
        iname = (item.get("name") or "").strip().lower()
        iid = item.get("id")
        if iid is None:
            continue
        if iname == name_l:
            app_id = str(iid)
            break
    if app_id is None and items:
        first = items[0]
        if isinstance(first, dict) and first.get("id") is not None:
            app_id = str(first["id"])

    if cache is not None:
        cache[key] = app_id
    return app_id


def _libretro_urls(name):
    enc_name = urllib.parse.quote(name)
    urls = []
    for platform in _LIBRETRO_PLATFORMS:
        enc_plat = urllib.parse.quote(platform)
        for kind in _LIBRETRO_ART_KIND:
            urls.append(
                "https://thumbnails.libretro.com/%s/%s/%s.png"
                % (enc_plat, kind, enc_name)
            )
    return urls


def _wikipedia_thumbnail_url(name, timeout=12):
    """Wikipedia REST summary — free thumbnail when article exists."""
    if not name:
        return None
    titles = [name.strip()]
    if " / " in name:
        titles.append(name.split(" / ")[-1].strip())
    for title in titles:
        enc = urllib.parse.quote(title.replace(" ", "_"))
        data = _http_json(
            "https://en.wikipedia.org/api/rest_v1/page/summary/%s" % enc,
            timeout,
        )
        if not data:
            continue
        thumb = data.get("thumbnail") or {}
        src = thumb.get("source")
        if isinstance(src, str) and src.startswith("http"):
            return src
    return None


def _cdn_urls_for_game(game, steam_search_cache=None):
    """Ordered remote image URLs (all free, no API key)."""
    platform = (game.get("platform") or "").lower()
    urls = []
    seen = set()

    def add(u):
        if u and u not in seen:
            seen.add(u)
            urls.append(u)

    if platform == "steam" and game.get("steam_app_id"):
        for u in _steam_cdn_urls(game["steam_app_id"]):
            add(u)

    epic_url = game.get("epic_image_url")
    if isinstance(epic_url, str) and epic_url.startswith("http"):
        add(epic_url.strip())

    if platform == "nsp":
        raw_stem = (game.get("nsp_filename") or _nsp_art_name(game) or "").strip()
        for u in _nsp_title_id_cdn_urls(raw_stem):
            add(u)
        for name in _art_name_variants(game):
            enc = urllib.parse.quote(name)
            for tpl in _LIBRETRO_SWITCH_ONLY:
                add(tpl.format(name=enc))
        for name in _art_name_variants(game):
            for u in _libretro_urls(name):
                add(u)
    else:
        for name in _art_name_variants(game):
            for u in _libretro_urls(name):
                add(u)

    if platform != "steam" or not game.get("steam_app_id"):
        for name in _art_name_variants(game):
            app_id = _steam_store_search_app_id(name, cache=steam_search_cache)
            if app_id:
                for u in _steam_cdn_urls(app_id):
                    add(u)

    for name in _art_name_variants(game):
        wiki = _wikipedia_thumbnail_url(name)
        if wiki:
            add(wiki)

    return urls


def _rawg_fetch_url(game, api_key, timeout=12):
    """Optional: only if user set rawg_api_key in config."""
    name = (game.get("name") or "").strip()
    if not name or not api_key:
        return None
    q = urllib.parse.quote(name)
    url = "https://api.rawg.io/api/games?search=%s&page_size=1&key=%s" % (q, urllib.parse.quote(api_key))
    data = _http_json(url, timeout)
    if not data:
        return None
    results = data.get("results") or []
    if not results:
        return None
    img = results[0].get("background_image") or results[0].get("background_image_additional")
    if isinstance(img, str) and img.startswith("http"):
        return img
    return None


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
            with open(path, "r", encoding="utf-8") as f:
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
        return os.path.join(self.cache_dir, _cache_filename(cache_key[0], cache_key[1]))

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

        for url in _cdn_urls_for_game(game, self._steam_search_cache):
            if _download_url(url, dest, self.timeout):
                self._save_steam_search_cache()
                return dest

        if self.rawg_api_key:
            rawg_url = _rawg_fetch_url(game, self.rawg_api_key, self.timeout)
            if rawg_url and _download_url(rawg_url, dest, self.timeout):
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
