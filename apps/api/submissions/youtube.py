"""Parsing and validating YouTube links.

Mirrors the client-side check in `apps/web/src/pages/usulkan.astro`.
"""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

ALLOWED_HOSTS = frozenset(
    {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "music.youtube.com",
        "youtu.be",
        "www.youtu.be",
    }
)

# YouTube ids are 11 characters of an unpadded base64url alphabet.
_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")
_PATH_PREFIXES = ("shorts", "live", "embed", "v")


def extract_youtube_id(url: str) -> str | None:
    """Return the video id in `url`, or None if it is not a YouTube video link.

    Accepts youtu.be/<id>, /watch?v=<id>, /shorts/<id>, /live/<id>, and embeds.
    """

    if not url:
        return None

    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return None

    if parsed.scheme not in ("http", "https"):
        return None
    if parsed.hostname is None or parsed.hostname.lower() not in ALLOWED_HOSTS:
        return None

    segments = [segment for segment in parsed.path.split("/") if segment]

    if parsed.hostname.lower().endswith("youtu.be"):
        candidate = segments[0] if segments else None
    elif parsed.path == "/watch":
        candidate = parse_qs(parsed.query).get("v", [None])[0]
    elif len(segments) >= 2 and segments[0] in _PATH_PREFIXES:
        candidate = segments[1]
    else:
        candidate = None

    if candidate and _ID_PATTERN.match(candidate):
        return candidate
    return None
