"""CLI entrypoint for card-news command."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from auto_card_news_v2.config import Settings, load_settings
from auto_card_news_v2.pipeline import run_pipeline


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="card-news",
        description="Generate Threads card-news carousels from RSS feeds.",
    )
    sub = parser.add_subparsers(dest="command")

    gen = sub.add_parser("generate", help="Fetch feeds and generate card news.")
    gen.add_argument("--feeds", type=str, default=None, help="Comma-separated RSS feed URLs (overrides NEWS_RSS_FEEDS).")
    gen.add_argument("--output-dir", type=str, default=None, help="Output directory (overrides NEWS_OUTPUT_DIR).")
    gen.add_argument("--dry-run", action="store_true", help="Print plan without writing files.")
    gen.add_argument("--limit", type=int, default=None, help="Max number of items to process.")
    gen.add_argument("--auto-publish", action="store_true", help="Automatically publish to Threads after generating.")

    auth = sub.add_parser("auth", help="Configure Threads access token.")
    auth.add_argument("--token", type=str, default=None, help="Access token (prompted if not provided).")
    auth.add_argument("--expires-in", type=int, default=5_184_000, help="Token lifetime in seconds (default: 60 days).")

    pub = sub.add_parser("publish", help="Publish an existing output directory to Threads.")
    pub.add_argument("output_path", type=str, help="Path to a card-news output directory.")

    run = sub.add_parser("run", help="Start the scheduler for periodic card news generation.")
    run.add_argument("--interval", type=int, default=None, help="Interval in minutes between runs (default: from NEWS_SCHEDULE_INTERVAL or 60).")
    run.add_argument("--no-publish", action="store_true", help="Disable automatic publishing to Threads.")
    run.add_argument("--limit", type=int, default=None, help="Max number of items per run.")

    sched = sub.add_parser("schedule", help="Manage cron-based auto-generation schedule.")
    sched_sub = sched.add_subparsers(dest="schedule_action")

    sched_install = sched_sub.add_parser("install", help="Install cron schedule.")
    sched_install.add_argument("--times", type=str, required=True, help="Comma-separated HH:MM times (e.g. '09:00,18:00').")
    sched_install.add_argument("--limit", type=int, default=3, help="Max items per run (default: 3).")
    sched_install.add_argument("--env-file", type=str, default=None, help="Path to .env file to source.")

    sched_sub.add_parser("uninstall", help="Remove cron schedule.")
    sched_sub.add_parser("status", help="Show current schedule.")

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "generate":
        _cmd_generate(args)
    elif args.command == "auth":
        _cmd_auth(args)
    elif args.command == "publish":
        _cmd_publish(args)
    elif args.command == "run":
        _cmd_run(args)
    elif args.command == "schedule":
        _cmd_schedule(args)


def _cmd_generate(args: argparse.Namespace) -> None:
    settings = load_settings(
        feeds_override=args.feeds,
        output_override=args.output_dir,
        dry_run=args.dry_run,
    )
    if args.limit is not None:
        settings = Settings(
            rss_feeds=settings.rss_feeds,
            output_dir=settings.output_dir,
            safety_enabled=settings.safety_enabled,
            max_items=args.limit,
            num_cards=settings.num_cards,
            brand_name=settings.brand_name,
            brand_handle=settings.brand_handle,
            dry_run=settings.dry_run,
            threads_user_id=settings.threads_user_id,
            cloudinary_cloud_name=settings.cloudinary_cloud_name,
            cloudinary_api_key=settings.cloudinary_api_key,
            cloudinary_api_secret=settings.cloudinary_api_secret,
        )

    if not settings.rss_feeds:
        print("Error: No RSS feeds configured. Set NEWS_RSS_FEEDS or use --feeds.")
        sys.exit(1)

    posts = run_pipeline(settings)
    print(f"Generated {len(posts)} card news post(s).")
    for post in posts:
        print(f"  -> {post.output_dir}")

    if args.auto_publish and posts:
        _publish_posts(posts, settings)


def _cmd_run(args: argparse.Namespace) -> None:
    from auto_card_news_v2.config import load_settings as _load
    from auto_card_news_v2.runner import start

    settings = _load()
    interval = args.interval if args.interval is not None else settings.schedule_interval_minutes
    auto_publish = not args.no_publish and settings.auto_publish

    start(
        interval_minutes=interval,
        auto_publish=auto_publish,
        limit=args.limit,
        timezone=settings.timezone,
    )


def _cmd_auth(args: argparse.Namespace) -> None:
    from auto_card_news_v2.threads.token_store import save_token

    token = args.token
    if not token:
        token = input("Enter your Threads access token: ").strip()

    if not token:
        print("Error: No token provided.")
        sys.exit(1)

    save_token(token, args.expires_in)
    print("Token saved successfully.")


def _cmd_publish(args: argparse.Namespace) -> None:
    output_path = Path(args.output_path)
    if not output_path.is_dir():
        print(f"Error: Not a directory: {output_path}")
        sys.exit(1)

    settings = load_settings()
    post = _load_post_from_dir(output_path)

    from auto_card_news_v2.threads.publisher import publish_post

    try:
        result = publish_post(post, settings)
        print(f"Published to Threads: {result.permalink}")
    except Exception as exc:
        print(f"Error publishing: {exc}")
        sys.exit(1)


def _publish_posts(posts, settings: Settings) -> None:
    from auto_card_news_v2.threads.publisher import PublishConfigError, publish_post

    for post in posts:
        try:
            result = publish_post(post, settings)
            print(f"  Published: {result.permalink}")
        except PublishConfigError as exc:
            print(f"  Publish skipped: {exc}")
            break
        except Exception as exc:
            print(f"  Publish failed for {post.output_dir}: {exc}")


def _cmd_schedule(args: argparse.Namespace) -> None:
    from auto_card_news_v2.scheduler import install_cron, show_status, uninstall_cron

    if args.schedule_action is None:
        print(show_status())
        return

    if args.schedule_action == "install":
        times = [t.strip() for t in args.times.split(",") if t.strip()]
        env_file = Path(args.env_file) if args.env_file else None
        try:
            result = install_cron(times, args.limit, env_file=env_file)
            print(f"Schedule installed:\n{result}")
        except (ValueError, RuntimeError) as exc:
            print(f"Error: {exc}")
            sys.exit(1)

    elif args.schedule_action == "uninstall":
        try:
            removed = uninstall_cron()
            if removed:
                print("Schedule removed.")
            else:
                print("No schedule was configured.")
        except RuntimeError as exc:
            print(f"Error: {exc}")
            sys.exit(1)

    elif args.schedule_action == "status":
        try:
            print(show_status())
        except RuntimeError as exc:
            print(f"Error: {exc}")
            sys.exit(1)


def _load_post_from_dir(output_path: Path):
    """Reconstruct a ThreadsPost from an output directory."""
    from auto_card_news_v2.models import ThreadsPost

    # Read caption
    caption_path = output_path / "caption.txt"
    if not caption_path.exists():
        print(f"Error: caption.txt not found in {output_path}")
        sys.exit(1)
    caption = caption_path.read_text(encoding="utf-8")

    # Read metadata
    metadata: dict = {}
    meta_path = output_path / "metadata.json"
    if meta_path.exists():
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))

    # Find PNG images
    image_paths = sorted(output_path.glob("*.png"))
    if not image_paths:
        print(f"Error: No PNG files found in {output_path}")
        sys.exit(1)

    return ThreadsPost(
        image_paths=tuple(image_paths),
        caption=caption,
        metadata=metadata,
        output_dir=output_path,
    )
