"""Python scheduler for periodic card news generation."""

from __future__ import annotations

import logging
import signal
import sys
from types import FrameType

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from auto_card_news_v2.config import Settings, load_settings
from auto_card_news_v2.pipeline import run_pipeline

logger = logging.getLogger(__name__)


def _setup_logging() -> None:
    """Configure structured logging to stdout for Docker log collection."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )


def run_job(*, auto_publish: bool = True, limit: int | None = None) -> None:
    """Execute a single pipeline run.

    Catches all exceptions so the scheduler keeps running.
    """
    logger.info("Starting card news generation job")
    try:
        settings = load_settings()
        if limit is not None:
            settings = Settings(
                rss_feeds=settings.rss_feeds,
                output_dir=settings.output_dir,
                safety_enabled=settings.safety_enabled,
                max_items=limit,
                num_cards=settings.num_cards,
                brand_name=settings.brand_name,
                brand_handle=settings.brand_handle,
                dry_run=settings.dry_run,
                threads_user_id=settings.threads_user_id,
                cloudinary_cloud_name=settings.cloudinary_cloud_name,
                cloudinary_api_key=settings.cloudinary_api_key,
                cloudinary_api_secret=settings.cloudinary_api_secret,
                schedule_interval_minutes=settings.schedule_interval_minutes,
                auto_publish=settings.auto_publish,
                timezone=settings.timezone,
            )

        posts = run_pipeline(settings)
        logger.info("Generated %d card news post(s)", len(posts))

        if auto_publish and posts:
            _publish_posts(posts, settings)

    except Exception:
        logger.exception("Job failed")


def _publish_posts(posts: list, settings: Settings) -> None:
    """Publish generated posts to Threads."""
    from auto_card_news_v2.threads.publisher import PublishConfigError, publish_post

    for post in posts:
        try:
            result = publish_post(post, settings)
            logger.info("Published: %s", result.permalink)
        except PublishConfigError as exc:
            logger.warning("Publish skipped: %s", exc)
            break
        except Exception:
            logger.exception("Publish failed for %s", post.output_dir)


def start(
    *,
    interval_minutes: int = 60,
    auto_publish: bool = True,
    limit: int | None = None,
    timezone: str = "Asia/Seoul",
) -> None:
    """Start the blocking scheduler with signal handling."""
    _setup_logging()

    scheduler = BlockingScheduler(timezone=timezone)

    trigger = IntervalTrigger(minutes=interval_minutes, timezone=timezone)
    scheduler.add_job(
        run_job,
        trigger=trigger,
        kwargs={"auto_publish": auto_publish, "limit": limit},
        id="card_news_job",
        name="Card News Generation",
    )

    def _shutdown(signum: int, frame: FrameType | None) -> None:
        logger.info("Received signal %d, shutting down scheduler", signum)
        scheduler.shutdown(wait=False)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    logger.info(
        "Scheduler started: interval=%dm, auto_publish=%s, limit=%s, tz=%s",
        interval_minutes,
        auto_publish,
        limit,
        timezone,
    )

    # Run the job immediately on startup, then schedule repeats
    run_job(auto_publish=auto_publish, limit=limit)

    scheduler.start()
