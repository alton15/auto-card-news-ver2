"""Tests for cron-based scheduler."""

from __future__ import annotations

from unittest.mock import patch

from auto_card_news_v2.scheduler import (
    _CRON_MARKER,
    _parse_time,
    install_cron,
    show_status,
    uninstall_cron,
)

import pytest


def test_parse_time_valid():
    assert _parse_time("09:00") == ("9", "0")
    assert _parse_time("18:30") == ("18", "30")
    assert _parse_time("0:00") == ("0", "0")
    assert _parse_time("23:59") == ("23", "59")


def test_parse_time_invalid():
    with pytest.raises(ValueError):
        _parse_time("25:00")
    with pytest.raises(ValueError):
        _parse_time("12:60")
    with pytest.raises(ValueError):
        _parse_time("noon")


@patch("auto_card_news_v2.scheduler._write_crontab")
@patch("auto_card_news_v2.scheduler._read_crontab", return_value=[])
@patch("auto_card_news_v2.scheduler._check_crontab_available")
def test_install_cron_single_time(mock_check, mock_read, mock_write):
    result = install_cron(["09:00"], limit=3)

    assert _CRON_MARKER in result
    assert "0 9 * * *" in result
    assert "--limit 3" in result
    assert "--auto-publish" in result
    mock_write.assert_called_once()


@patch("auto_card_news_v2.scheduler._write_crontab")
@patch("auto_card_news_v2.scheduler._read_crontab", return_value=[])
@patch("auto_card_news_v2.scheduler._check_crontab_available")
def test_install_cron_multiple_times(mock_check, mock_read, mock_write):
    result = install_cron(["09:00", "18:00"], limit=5)

    assert "0 9 * * *" in result
    assert "0 18 * * *" in result
    assert "--limit 5" in result


@patch("auto_card_news_v2.scheduler._write_crontab")
@patch("auto_card_news_v2.scheduler._read_crontab", return_value=[
    "0 12 * * * some-other-job",
    f"0 9 * * * card-news generate --auto-publish --limit 3 {_CRON_MARKER}",
])
@patch("auto_card_news_v2.scheduler._check_crontab_available")
def test_install_cron_replaces_existing(mock_check, mock_read, mock_write):
    install_cron(["18:00"], limit=2)

    written = mock_write.call_args[0][0]
    marker_entries = [l for l in written if _CRON_MARKER in l]
    assert len(marker_entries) == 1
    assert "0 18 * * *" in marker_entries[0]
    # Other jobs are preserved
    assert any("some-other-job" in l for l in written)


@patch("auto_card_news_v2.scheduler._write_crontab")
@patch("auto_card_news_v2.scheduler._read_crontab", return_value=[
    "0 12 * * * other-job",
    f"0 9 * * * card-news generate {_CRON_MARKER}",
])
@patch("auto_card_news_v2.scheduler._check_crontab_available")
def test_uninstall_cron_removes_entries(mock_check, mock_read, mock_write):
    result = uninstall_cron()

    assert result is True
    written = mock_write.call_args[0][0]
    assert not any(_CRON_MARKER in l for l in written)
    assert any("other-job" in l for l in written)


@patch("auto_card_news_v2.scheduler._read_crontab", return_value=[
    "0 12 * * * other-job",
])
@patch("auto_card_news_v2.scheduler._check_crontab_available")
def test_uninstall_cron_nothing_to_remove(mock_check, mock_read):
    result = uninstall_cron()
    assert result is False


@patch("auto_card_news_v2.scheduler._read_crontab", return_value=[
    f"0 9 * * * card-news generate --auto-publish --limit 3 {_CRON_MARKER}",
    f"30 18 * * * card-news generate --auto-publish --limit 5 {_CRON_MARKER}",
])
@patch("auto_card_news_v2.scheduler._check_crontab_available")
def test_show_status_with_entries(mock_check, mock_read):
    result = show_status()

    assert "Active schedules:" in result
    assert "09:00" in result
    assert "18:30" in result


@patch("auto_card_news_v2.scheduler._read_crontab", return_value=[])
@patch("auto_card_news_v2.scheduler._check_crontab_available")
def test_show_status_empty(mock_check, mock_read):
    result = show_status()
    assert "No card-news schedules configured." in result
