"""HTTP helpers and on-disk cache filenames for cover downloads."""

import hashlib
import json
import os
import re
import urllib.error
import urllib.request

_USER_AGENT = "JoypadLauncher/1.0"


def looks_like_image(data):
    if not data or len(data) < 200:
        return False
    if data[:3] == b"\xff\xd8\xff":
        return True
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return True
    if data[:4] == b"RIFF" and len(data) > 12 and data[8:12] == b"WEBP":
        return True
    return False


def http_json(url, timeout=12):
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception:
        return None


def download_url(url, dest_path, timeout=12):
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if getattr(resp, "status", 200) != 200:
                return False
            data = resp.read()
    except (urllib.error.URLError, OSError, TimeoutError):
        return False
    if not looks_like_image(data):
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


def cache_filename(platform, stable_id):
    digest = hashlib.sha1(str(stable_id).encode("utf-8", errors="replace")).hexdigest()[:16]
    safe_plat = re.sub(r"[^a-z0-9]", "", (platform or "x").lower())[:12]
    return "%s_%s.jpg" % (safe_plat, digest)
