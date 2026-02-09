"""Tests for threads client module."""

from __future__ import annotations

import json
import urllib.error
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from auto_card_news_v2.threads.client import (
    ThreadsAPIError,
    ThreadsPublishError,
    ThreadsRateLimitError,
    check_container_status,
    create_carousel_container,
    create_image_container,
    get_post_permalink,
    publish_container,
    wait_for_container,
)


def _mock_response(data: dict) -> MagicMock:
    """Create a mock urllib response."""
    body = json.dumps(data).encode()
    resp = MagicMock()
    resp.read.return_value = body
    resp.__enter__ = lambda self: self
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def _mock_http_error(code: int, body: str = "error") -> urllib.error.HTTPError:
    err = urllib.error.HTTPError(
        url="https://graph.threads.net/test",
        code=code,
        msg="Error",
        hdrs={},
        fp=BytesIO(body.encode()),
    )
    return err


@patch("auto_card_news_v2.threads.client.urllib.request.urlopen")
def test_create_image_container(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"id": "container_123"})

    result = create_image_container("user_1", "https://cdn.example.com/img.png", "tok_abc")
    assert result == "container_123"


@patch("auto_card_news_v2.threads.client.urllib.request.urlopen")
def test_create_carousel_container(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"id": "carousel_456"})

    result = create_carousel_container(
        "user_1", ["c1", "c2", "c3"], "My caption", "tok_abc"
    )
    assert result == "carousel_456"


@patch("auto_card_news_v2.threads.client.urllib.request.urlopen")
def test_check_container_status(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"status": "FINISHED"})

    result = check_container_status("container_123", "tok_abc")
    assert result == "FINISHED"


@patch("auto_card_news_v2.threads.client.urllib.request.urlopen")
def test_publish_container(mock_urlopen):
    mock_urlopen.return_value = _mock_response({"id": "post_789"})

    result = publish_container("user_1", "carousel_456", "tok_abc")
    assert result == "post_789"


@patch("auto_card_news_v2.threads.client.urllib.request.urlopen")
def test_get_post_permalink(mock_urlopen):
    mock_urlopen.return_value = _mock_response(
        {"permalink": "https://www.threads.net/@user/post/abc123"}
    )

    result = get_post_permalink("post_789", "tok_abc")
    assert result == "https://www.threads.net/@user/post/abc123"


@patch("auto_card_news_v2.threads.client.urllib.request.urlopen")
def test_api_error_raised_on_http_error(mock_urlopen):
    mock_urlopen.side_effect = _mock_http_error(400, '{"error": "bad request"}')

    with pytest.raises(ThreadsAPIError) as exc_info:
        create_image_container("user_1", "https://example.com/img.png", "tok")

    assert exc_info.value.status_code == 400


@patch("auto_card_news_v2.threads.client.urllib.request.urlopen")
def test_rate_limit_error_on_429(mock_urlopen):
    mock_urlopen.side_effect = _mock_http_error(429, "rate limited")

    with pytest.raises(ThreadsRateLimitError):
        create_image_container("user_1", "https://example.com/img.png", "tok")


@patch("auto_card_news_v2.threads.client.time.sleep")
@patch("auto_card_news_v2.threads.client.check_container_status")
def test_wait_for_container_success(mock_check, mock_sleep):
    mock_check.side_effect = ["IN_PROGRESS", "IN_PROGRESS", "FINISHED"]

    wait_for_container("c_123", "tok_abc", poll_interval=0.01, max_seconds=10)
    assert mock_check.call_count == 3


@patch("auto_card_news_v2.threads.client.time.sleep")
@patch("auto_card_news_v2.threads.client.check_container_status")
def test_wait_for_container_error_status(mock_check, mock_sleep):
    mock_check.return_value = "ERROR"

    with pytest.raises(ThreadsPublishError, match="ERROR status"):
        wait_for_container("c_123", "tok_abc", poll_interval=0.01, max_seconds=10)


@patch("auto_card_news_v2.threads.client.time.monotonic")
@patch("auto_card_news_v2.threads.client.time.sleep")
@patch("auto_card_news_v2.threads.client.check_container_status")
def test_wait_for_container_timeout(mock_check, mock_sleep, mock_monotonic):
    mock_check.return_value = "IN_PROGRESS"
    # First call sets deadline, second call exceeds it
    mock_monotonic.side_effect = [0.0, 100.0]

    with pytest.raises(ThreadsPublishError, match="did not finish"):
        wait_for_container("c_123", "tok_abc", poll_interval=0.01, max_seconds=5)
