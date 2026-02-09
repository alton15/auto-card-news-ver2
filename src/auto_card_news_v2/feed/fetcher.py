"""HTTP fetching for RSS feed URLs."""

from __future__ import annotations

import ssl
import urllib.request

try:
    import certifi

    _SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CONTEXT = ssl.create_default_context()

_TIMEOUT_SECONDS = 15
_USER_AGENT = "auto-card-news-v2/0.1 (+https://github.com/auto-card-news)"


def fetch_feed(url: str, *, timeout: int = _TIMEOUT_SECONDS) -> bytes:
    """Fetch raw bytes from a feed URL with SSL and timeout."""
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CONTEXT) as resp:
        return resp.read()  # type: ignore[no-any-return]
