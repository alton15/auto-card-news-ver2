"""Cron-based scheduler for automatic card news generation."""

from __future__ import annotations

import logging
import shutil
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

_CRON_MARKER = "# card-news-auto"


def install_cron(
    times: list[str],
    limit: int = 3,
    *,
    env_file: Path | None = None,
) -> str:
    """Install crontab entries for card-news generation.

    Args:
        times: List of HH:MM time strings (e.g. ["09:00", "18:00"]).
        limit: Max items per run.
        env_file: Optional .env file to source before running.

    Returns:
        The crontab entries that were added.
    """
    _check_crontab_available()

    card_news_bin = shutil.which("card-news")
    if card_news_bin is None:
        card_news_bin = f"{sys.executable} -m auto_card_news_v2.cli"

    env_prefix = ""
    if env_file and env_file.exists():
        env_prefix = f"set -a && source {env_file} && set +a && "

    new_entries: list[str] = []
    for time_str in times:
        hour, minute = _parse_time(time_str)
        cmd = f"{env_prefix}{card_news_bin} generate --auto-publish --limit {limit}"
        entry = f"{minute} {hour} * * * {cmd} {_CRON_MARKER}"
        new_entries.append(entry)

    # Remove existing card-news entries first
    existing = _read_crontab()
    cleaned = [line for line in existing if _CRON_MARKER not in line]
    cleaned.extend(new_entries)
    _write_crontab(cleaned)

    result = "\n".join(new_entries)
    logger.info("Installed cron entries:\n%s", result)
    return result


def uninstall_cron() -> bool:
    """Remove all card-news crontab entries.

    Returns:
        True if entries were removed, False if none were found.
    """
    _check_crontab_available()

    existing = _read_crontab()
    cleaned = [line for line in existing if _CRON_MARKER not in line]

    if len(cleaned) == len(existing):
        return False

    _write_crontab(cleaned)
    logger.info("Removed card-news cron entries")
    return True


def show_status() -> str:
    """Show current card-news crontab entries.

    Returns:
        Formatted status string.
    """
    _check_crontab_available()

    existing = _read_crontab()
    entries = [line for line in existing if _CRON_MARKER in line]

    if not entries:
        return "No card-news schedules configured."

    lines = ["Active schedules:"]
    for entry in entries:
        parts = entry.split()
        minute, hour = parts[0], parts[1]
        lines.append(f"  {hour.zfill(2)}:{minute.zfill(2)} daily")
    return "\n".join(lines)


def _parse_time(time_str: str) -> tuple[str, str]:
    """Parse 'HH:MM' into (hour, minute) strings."""
    parts = time_str.strip().split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid time format: {time_str!r} (expected HH:MM)")

    hour, minute = parts
    h, m = int(hour), int(minute)
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ValueError(f"Time out of range: {time_str!r}")
    return str(h), str(m)


def _check_crontab_available() -> None:
    """Raise RuntimeError if crontab command is not available."""
    if shutil.which("crontab") is None:
        raise RuntimeError("crontab command not found on this system")


def _read_crontab() -> list[str]:
    """Read current user crontab entries."""
    try:
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return []
        return [line for line in result.stdout.splitlines() if line.strip()]
    except OSError:
        return []


def _write_crontab(lines: list[str]) -> None:
    """Write lines to user crontab."""
    content = "\n".join(lines) + "\n" if lines else ""
    subprocess.run(
        ["crontab", "-"],
        input=content,
        text=True,
        check=True,
    )
