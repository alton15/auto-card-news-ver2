"""Tests for threads image_host module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from auto_card_news_v2.config import load_settings
from auto_card_news_v2.models import ImageUpload
from auto_card_news_v2.threads.image_host import cleanup_images, upload_images


@pytest.fixture
def settings(monkeypatch):
    monkeypatch.setenv("CLOUDINARY_CLOUD_NAME", "test-cloud")
    monkeypatch.setenv("CLOUDINARY_API_KEY", "123456")
    monkeypatch.setenv("CLOUDINARY_API_SECRET", "secret")
    return load_settings()


@pytest.fixture
def image_paths(tmp_path):
    paths = []
    for i in range(3):
        p = tmp_path / f"card_{i}.png"
        p.write_bytes(b"fake-png-data")
        paths.append(p)
    return tuple(paths)


@patch("auto_card_news_v2.threads.image_host.cloudinary.uploader.upload")
@patch("auto_card_news_v2.threads.image_host.cloudinary.config")
def test_upload_images_success(mock_config, mock_upload, settings, image_paths):
    mock_upload.side_effect = [
        {"secure_url": f"https://cdn.example.com/card_{i}.png", "public_id": f"card-news/card_{i}"}
        for i in range(3)
    ]

    uploads = upload_images(image_paths, settings)

    assert len(uploads) == 3
    assert all(isinstance(u, ImageUpload) for u in uploads)
    assert uploads[0].public_url == "https://cdn.example.com/card_0.png"
    assert uploads[0].upload_id == "card-news/card_0"
    assert mock_upload.call_count == 3


@patch("auto_card_news_v2.threads.image_host.cloudinary.uploader.destroy")
@patch("auto_card_news_v2.threads.image_host.cloudinary.uploader.upload")
@patch("auto_card_news_v2.threads.image_host.cloudinary.config")
def test_upload_images_partial_failure_cleans_up(
    mock_config, mock_upload, mock_destroy, settings, image_paths
):
    mock_upload.side_effect = [
        {"secure_url": "https://cdn.example.com/card_0.png", "public_id": "card-news/card_0"},
        Exception("upload failed"),
    ]

    with pytest.raises(Exception, match="upload failed"):
        upload_images(image_paths, settings)

    # Should clean up the one successful upload
    mock_destroy.assert_called_once_with("card-news/card_0", resource_type="image")


@patch("auto_card_news_v2.threads.image_host.cloudinary.uploader.destroy")
@patch("auto_card_news_v2.threads.image_host.cloudinary.config")
def test_cleanup_images_success(mock_config, mock_destroy, settings):
    uploads = (
        ImageUpload(local_path=Path("/a.png"), public_url="https://x/a.png", upload_id="id_a"),
        ImageUpload(local_path=Path("/b.png"), public_url="https://x/b.png", upload_id="id_b"),
    )
    cleanup_images(uploads, settings)
    assert mock_destroy.call_count == 2


@patch("auto_card_news_v2.threads.image_host.cloudinary.uploader.destroy")
@patch("auto_card_news_v2.threads.image_host.cloudinary.config")
def test_cleanup_images_failure_does_not_raise(mock_config, mock_destroy, settings):
    mock_destroy.side_effect = Exception("destroy failed")
    uploads = (
        ImageUpload(local_path=Path("/a.png"), public_url="https://x/a.png", upload_id="id_a"),
    )
    # Should not raise
    cleanup_images(uploads, settings)


def test_cleanup_images_empty_does_nothing(settings):
    # Should not raise or call anything
    cleanup_images((), settings)
