"""
Download cover art from free public sources into a local disk cache.
No API keys required (Steam store search, Steam CDN, Libretro, Wikipedia).
"""

from joypad.covers.cdn.nsp import nsp_cover_stems
from joypad.covers.cdn.store import CdnCoverStore

__all__ = ["CdnCoverStore", "nsp_cover_stems"]
