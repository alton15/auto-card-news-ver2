"""Upload card images to Cloudinary for public HTTPS URLs."""

from __future__ import annotations

import logging
from pathlib import Path

import cloudinary
import cloudinary.uploader

from auto_card_news_v2.config import Settings
from auto_card_news_v2.models import ImageUpload

logger = logging.getLogger(__name__)

_UPLOAD_FOLDER = "card-news"


def _configure(settings: Settings) -> None:
    """Set Cloudinary credentials from Settings."""
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )


def upload_images(
    image_paths: tuple[Path, ...],
    settings: Settings,
) -> tuple[ImageUpload, ...]:
    """Upload local PNGs to Cloudinary. Cleans up on partial failure."""
    _configure(settings)
    uploads: list[ImageUpload] = []

    for path in image_paths:
        try:
            result = cloudinary.uploader.upload(
                str(path),
                folder=_UPLOAD_FOLDER,
                resource_type="image",
            )
            upload = ImageUpload(
                local_path=path,
                public_url=result["secure_url"],
                upload_id=result["public_id"],
            )
            uploads.append(upload)
            logger.info("Uploaded %s -> %s", path.name, upload.public_url)
        except Exception as exc:
            logger.error("Failed to upload %s: %s", path.name, exc)
            # Clean up already-uploaded images before re-raising
            cleanup_images(tuple(uploads), settings)
            raise

    return tuple(uploads)


def cleanup_images(
    uploads: tuple[ImageUpload, ...],
    settings: Settings,
) -> None:
    """Delete uploaded images from Cloudinary. Logs but does not raise on failure."""
    if not uploads:
        return

    _configure(settings)
    for upload in uploads:
        try:
            cloudinary.uploader.destroy(upload.upload_id, resource_type="image")
            logger.info("Cleaned up %s", upload.upload_id)
        except Exception as exc:
            logger.warning("Failed to clean up %s: %s", upload.upload_id, exc)
