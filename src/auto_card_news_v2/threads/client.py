"""Low-level Threads Graph API client using urllib."""

from __future__ import annotations

import json
import logging
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request

try:
    import certifi

    _SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CONTEXT = ssl.create_default_context()

logger = logging.getLogger(__name__)

_GRAPH_API_BASE = "https://graph.threads.net/v1.0"
_TIMEOUT_SECONDS = 15
_POLL_INTERVAL_SECONDS = 2
_POLL_MAX_SECONDS = 60


class ThreadsAPIError(Exception):
    """Base error for Threads API failures."""

    def __init__(self, message: str, status_code: int = 0, body: str = "") -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class ThreadsRateLimitError(ThreadsAPIError):
    """Rate limit hit (HTTP 429)."""


class ThreadsPublishError(ThreadsAPIError):
    """Container failed to reach FINISHED status."""


def _post(url: str, data: dict) -> dict:
    """Send a POST request to the Threads API and return parsed JSON."""
    encoded = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(url, data=encoded, method="POST")
    try:
        with urllib.request.urlopen(
            req, timeout=_TIMEOUT_SECONDS, context=_SSL_CONTEXT
        ) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        if exc.code == 429:
            raise ThreadsRateLimitError(
                "Rate limit exceeded", status_code=exc.code, body=body
            ) from exc
        raise ThreadsAPIError(
            f"HTTP {exc.code}: {body}", status_code=exc.code, body=body
        ) from exc


def _get(url: str) -> dict:
    """Send a GET request to the Threads API and return parsed JSON."""
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(
            req, timeout=_TIMEOUT_SECONDS, context=_SSL_CONTEXT
        ) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        if exc.code == 429:
            raise ThreadsRateLimitError(
                "Rate limit exceeded", status_code=exc.code, body=body
            ) from exc
        raise ThreadsAPIError(
            f"HTTP {exc.code}: {body}", status_code=exc.code, body=body
        ) from exc


def create_image_container(
    user_id: str,
    image_url: str,
    access_token: str,
) -> str:
    """Create a single image container (carousel item). Returns container ID."""
    url = f"{_GRAPH_API_BASE}/{user_id}/threads"
    data = {
        "media_type": "IMAGE",
        "image_url": image_url,
        "is_carousel_item": "true",
        "access_token": access_token,
    }
    result = _post(url, data)
    container_id = result["id"]
    logger.info("Created image container %s for %s", container_id, image_url)
    return container_id


def create_carousel_container(
    user_id: str,
    children_ids: list[str],
    caption: str,
    access_token: str,
) -> str:
    """Create a carousel container with children. Returns container ID."""
    url = f"{_GRAPH_API_BASE}/{user_id}/threads"
    data = {
        "media_type": "CAROUSEL",
        "children": ",".join(children_ids),
        "text": caption,
        "access_token": access_token,
    }
    result = _post(url, data)
    container_id = result["id"]
    logger.info("Created carousel container %s with %d children", container_id, len(children_ids))
    return container_id


def check_container_status(
    container_id: str,
    access_token: str,
) -> str:
    """Check the status of a media container. Returns status string."""
    url = (
        f"{_GRAPH_API_BASE}/{container_id}"
        f"?fields=status,error_message&access_token={access_token}"
    )
    result = _get(url)
    return result.get("status", "UNKNOWN")


def wait_for_container(
    container_id: str,
    access_token: str,
    *,
    poll_interval: float = _POLL_INTERVAL_SECONDS,
    max_seconds: float = _POLL_MAX_SECONDS,
) -> None:
    """Poll until container reaches FINISHED status or timeout."""
    deadline = time.monotonic() + max_seconds
    while time.monotonic() < deadline:
        status = check_container_status(container_id, access_token)
        if status == "FINISHED":
            logger.info("Container %s is FINISHED", container_id)
            return
        if status == "ERROR":
            raise ThreadsPublishError(
                f"Container {container_id} failed with ERROR status"
            )
        logger.debug("Container %s status: %s, polling...", container_id, status)
        time.sleep(poll_interval)

    raise ThreadsPublishError(
        f"Container {container_id} did not finish within {max_seconds}s"
    )


def publish_container(
    user_id: str,
    container_id: str,
    access_token: str,
) -> str:
    """Publish a prepared container. Returns the published post ID."""
    url = f"{_GRAPH_API_BASE}/{user_id}/threads_publish"
    data = {
        "creation_id": container_id,
        "access_token": access_token,
    }
    result = _post(url, data)
    post_id = result["id"]
    logger.info("Published post %s", post_id)
    return post_id


def get_post_permalink(
    post_id: str,
    access_token: str,
) -> str:
    """Retrieve the public permalink for a published post."""
    url = (
        f"{_GRAPH_API_BASE}/{post_id}"
        f"?fields=permalink&access_token={access_token}"
    )
    result = _get(url)
    return result.get("permalink", "")
