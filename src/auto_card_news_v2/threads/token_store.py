"""Manage Threads long-lived access token stored on disk."""

from __future__ import annotations

import json
import logging
import ssl
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

try:
    import certifi

    _SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CONTEXT = ssl.create_default_context()

logger = logging.getLogger(__name__)

_TOKEN_DIR = Path.home() / ".card-news"
_TOKEN_FILE = _TOKEN_DIR / "threads_token.json"
_GRAPH_API_BASE = "https://graph.threads.net"
_REFRESH_THRESHOLD_DAYS = 7
_TIMEOUT_SECONDS = 15


def _token_path() -> Path:
    """Return the token file path (test-friendly seam)."""
    return _TOKEN_FILE


def load_token(*, token_path: Path | None = None) -> str | None:
    """Load a valid access token from disk, or return None."""
    path = token_path or _token_path()
    if not path.exists():
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        logger.warning("Corrupted token file, ignoring")
        return None

    expires_at = data.get("expires_at", "")
    if not expires_at:
        return data.get("access_token") or None

    try:
        exp = datetime.fromisoformat(expires_at)
    except ValueError:
        return data.get("access_token") or None

    if datetime.now(timezone.utc) >= exp:
        logger.info("Token has expired")
        return None

    return data.get("access_token") or None


def save_token(
    access_token: str,
    expires_in: int,
    *,
    token_path: Path | None = None,
) -> None:
    """Persist token with computed expiry timestamp."""
    path = token_path or _token_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    expires_at = datetime.now(timezone.utc).isoformat()
    if expires_in > 0:
        from datetime import timedelta

        expires_at = (
            datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        ).isoformat()

    data = {
        "access_token": access_token,
        "expires_in": expires_in,
        "expires_at": expires_at,
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    path.chmod(0o600)
    logger.info("Token saved to %s", path)


def refresh_if_needed(
    access_token: str,
    *,
    token_path: Path | None = None,
    threshold_days: int = _REFRESH_THRESHOLD_DAYS,
) -> str:
    """Refresh the token if it expires within *threshold_days*. Returns the (possibly new) token."""
    path = token_path or _token_path()
    if not path.exists():
        return access_token

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return access_token

    expires_at = data.get("expires_at", "")
    if not expires_at:
        return access_token

    try:
        exp = datetime.fromisoformat(expires_at)
    except ValueError:
        return access_token

    from datetime import timedelta

    if datetime.now(timezone.utc) + timedelta(days=threshold_days) < exp:
        return access_token  # still fresh

    logger.info("Token expires soon, attempting refresh")
    return _do_refresh(access_token, token_path=path)


def _do_refresh(access_token: str, *, token_path: Path) -> str:
    """Call the Threads token refresh endpoint."""
    url = (
        f"{_GRAPH_API_BASE}/refresh_access_token"
        f"?grant_type=th_refresh_token&access_token={access_token}"
    )
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(
            req, timeout=_TIMEOUT_SECONDS, context=_SSL_CONTEXT
        ) as resp:
            body = json.loads(resp.read())
    except Exception:
        logger.warning("Token refresh failed, keeping current token")
        return access_token

    new_token = body.get("access_token", access_token)
    expires_in = body.get("expires_in", 0)
    save_token(new_token, expires_in, token_path=token_path)
    logger.info("Token refreshed successfully")
    return new_token
