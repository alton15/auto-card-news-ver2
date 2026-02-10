"""Orchestrate the full Threads publishing flow."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from auto_card_news_v2.config import Settings
from auto_card_news_v2.models import ImageUpload, ThreadsPost, ThreadsPublishResult
from auto_card_news_v2.threads.client import (
    ThreadsAPIError,
    create_carousel_container,
    create_image_container,
    get_post_permalink,
    publish_container,
    wait_for_container,
)
from auto_card_news_v2.threads.image_host import cleanup_images, upload_images
from auto_card_news_v2.threads.token_store import load_token, refresh_if_needed

logger = logging.getLogger(__name__)


class PublishConfigError(Exception):
    """Missing required configuration for publishing."""


def publish_post(
    post: ThreadsPost,
    settings: Settings,
    *,
    token_path=None,
) -> ThreadsPublishResult:
    """Publish a ThreadsPost as a Threads carousel.

    Steps:
        1. Load and refresh access token
        2. Upload images to Cloudinary
        3. Create image containers on Threads
        4. Create carousel container + poll for FINISHED
        5. Publish
        6. Get permalink
        7. Clean up Cloudinary images (always)
    """
    _validate_config(settings)

    # 1. Token
    access_token = load_token(token_path=token_path)
    if not access_token:
        raise PublishConfigError(
            "No Threads access token found. Run 'card-news auth' first."
        )
    access_token = refresh_if_needed(access_token, token_path=token_path)

    # 2. Upload images
    uploads: tuple[ImageUpload, ...] = ()
    try:
        uploads = upload_images(post.image_paths, settings)

        # 3. Create image containers and wait for each
        user_id = settings.threads_user_id
        children_ids: list[str] = []
        for upload in uploads:
            container_id = create_image_container(
                user_id, upload.public_url, access_token
            )
            wait_for_container(container_id, access_token)
            children_ids.append(container_id)

        # 4. Create carousel + wait
        carousel_id = create_carousel_container(
            user_id, children_ids, post.caption, access_token
        )
        wait_for_container(carousel_id, access_token)

        # 5. Publish
        post_id = publish_container(user_id, carousel_id, access_token)

        # 6. Permalink
        permalink = get_post_permalink(post_id, access_token)

        published_at = datetime.now(timezone.utc).isoformat()
        logger.info("Published to Threads: %s", permalink)

        return ThreadsPublishResult(
            post=post,
            threads_id=post_id,
            permalink=permalink,
            published_at=published_at,
        )
    finally:
        # 7. Always clean up Cloudinary
        if uploads:
            cleanup_images(uploads, settings)


def _validate_config(settings: Settings) -> None:
    """Check that all required settings are present."""
    missing: list[str] = []
    if not settings.threads_user_id:
        missing.append("THREADS_USER_ID")
    if not settings.cloudinary_cloud_name:
        missing.append("CLOUDINARY_CLOUD_NAME")
    if not settings.cloudinary_api_key:
        missing.append("CLOUDINARY_API_KEY")
    if not settings.cloudinary_api_secret:
        missing.append("CLOUDINARY_API_SECRET")

    if missing:
        raise PublishConfigError(
            f"Missing required env vars: {', '.join(missing)}"
        )
