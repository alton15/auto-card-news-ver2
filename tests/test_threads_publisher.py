"""Tests for threads publisher module."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from auto_card_news_v2.config import load_settings
from auto_card_news_v2.models import ImageUpload, ThreadsPost, ThreadsPublishResult
from auto_card_news_v2.threads.client import ThreadsAPIError
from auto_card_news_v2.threads.publisher import PublishConfigError, publish_post


@pytest.fixture
def publish_settings(monkeypatch):
    monkeypatch.setenv("THREADS_USER_ID", "user_123")
    monkeypatch.setenv("CLOUDINARY_CLOUD_NAME", "test-cloud")
    monkeypatch.setenv("CLOUDINARY_API_KEY", "key_123")
    monkeypatch.setenv("CLOUDINARY_API_SECRET", "secret_123")
    return load_settings()


@pytest.fixture
def sample_post(tmp_path):
    paths = []
    for i in range(3):
        p = tmp_path / f"card_{i}.png"
        p.write_bytes(b"fake-png")
        paths.append(p)
    return ThreadsPost(
        image_paths=tuple(paths),
        caption="Test caption #news",
        metadata={"title": "Test"},
        output_dir=tmp_path,
    )


@pytest.fixture
def token_path(tmp_path):
    path = tmp_path / "token.json"
    future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    data = {"access_token": "tok_valid", "expires_in": 5_184_000, "expires_at": future}
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_publish_missing_config(monkeypatch, sample_post):
    monkeypatch.delenv("THREADS_USER_ID", raising=False)
    monkeypatch.delenv("CLOUDINARY_CLOUD_NAME", raising=False)
    monkeypatch.delenv("CLOUDINARY_API_KEY", raising=False)
    monkeypatch.delenv("CLOUDINARY_API_SECRET", raising=False)
    settings = load_settings()

    with pytest.raises(PublishConfigError, match="Missing required env vars"):
        publish_post(sample_post, settings)


def test_publish_missing_token(publish_settings, sample_post, tmp_path):
    token_path = tmp_path / "no_token.json"

    with pytest.raises(PublishConfigError, match="No Threads access token"):
        publish_post(sample_post, publish_settings, token_path=token_path)


@patch("auto_card_news_v2.threads.publisher.cleanup_images")
@patch("auto_card_news_v2.threads.publisher.get_post_permalink")
@patch("auto_card_news_v2.threads.publisher.publish_container")
@patch("auto_card_news_v2.threads.publisher.wait_for_container")
@patch("auto_card_news_v2.threads.publisher.create_carousel_container")
@patch("auto_card_news_v2.threads.publisher.create_image_container")
@patch("auto_card_news_v2.threads.publisher.upload_images")
def test_publish_full_flow(
    mock_upload,
    mock_create_img,
    mock_create_carousel,
    mock_wait,
    mock_publish,
    mock_permalink,
    mock_cleanup,
    publish_settings,
    sample_post,
    token_path,
):
    # Setup mocks
    mock_upload.return_value = tuple(
        ImageUpload(local_path=p, public_url=f"https://cdn/{p.name}", upload_id=f"id_{i}")
        for i, p in enumerate(sample_post.image_paths)
    )
    mock_create_img.side_effect = ["img_c0", "img_c1", "img_c2"]
    mock_create_carousel.return_value = "carousel_c"
    mock_publish.return_value = "post_999"
    mock_permalink.return_value = "https://www.threads.net/@user/post/abc"

    result = publish_post(sample_post, publish_settings, token_path=token_path)

    assert isinstance(result, ThreadsPublishResult)
    assert result.threads_id == "post_999"
    assert result.permalink == "https://www.threads.net/@user/post/abc"
    assert result.post is sample_post

    # Verify carousel was created with correct children
    mock_create_carousel.assert_called_once_with(
        "user_123", ["img_c0", "img_c1", "img_c2"], "Test caption #news", "tok_valid"
    )

    # Cleanup should always be called
    mock_cleanup.assert_called_once()


@patch("auto_card_news_v2.threads.publisher.cleanup_images")
@patch("auto_card_news_v2.threads.publisher.create_image_container")
@patch("auto_card_news_v2.threads.publisher.upload_images")
def test_publish_cleans_up_on_api_error(
    mock_upload,
    mock_create_img,
    mock_cleanup,
    publish_settings,
    sample_post,
    token_path,
):
    uploads = tuple(
        ImageUpload(local_path=p, public_url=f"https://cdn/{p.name}", upload_id=f"id_{i}")
        for i, p in enumerate(sample_post.image_paths)
    )
    mock_upload.return_value = uploads
    mock_create_img.side_effect = ThreadsAPIError("API down", status_code=500)

    with pytest.raises(ThreadsAPIError):
        publish_post(sample_post, publish_settings, token_path=token_path)

    # Cleanup still called via finally block
    mock_cleanup.assert_called_once_with(uploads, publish_settings)
