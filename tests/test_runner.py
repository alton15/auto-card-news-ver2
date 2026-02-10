"""Tests for the runner scheduler module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from auto_card_news_v2.runner import run_job


@patch("auto_card_news_v2.runner.run_pipeline")
@patch("auto_card_news_v2.runner.load_settings")
def test_run_job_calls_pipeline(mock_load, mock_pipeline):
    """run_job should load settings and call run_pipeline."""
    mock_pipeline.return_value = []

    run_job(auto_publish=False)

    mock_load.assert_called_once()
    mock_pipeline.assert_called_once_with(mock_load.return_value)


@patch("auto_card_news_v2.runner._publish_posts")
@patch("auto_card_news_v2.runner.run_pipeline")
@patch("auto_card_news_v2.runner.load_settings")
def test_run_job_publishes_when_enabled(mock_load, mock_pipeline, mock_publish):
    """run_job should call _publish_posts when auto_publish is True and posts exist."""
    mock_posts = [MagicMock()]
    mock_pipeline.return_value = mock_posts

    run_job(auto_publish=True)

    mock_publish.assert_called_once_with(mock_posts, mock_load.return_value)


@patch("auto_card_news_v2.runner._publish_posts")
@patch("auto_card_news_v2.runner.run_pipeline")
@patch("auto_card_news_v2.runner.load_settings")
def test_run_job_skips_publish_when_disabled(mock_load, mock_pipeline, mock_publish):
    """run_job should not publish when auto_publish is False."""
    mock_pipeline.return_value = [MagicMock()]

    run_job(auto_publish=False)

    mock_publish.assert_not_called()


@patch("auto_card_news_v2.runner.run_pipeline")
@patch("auto_card_news_v2.runner.load_settings")
def test_run_job_catches_exceptions(mock_load, mock_pipeline):
    """run_job should catch exceptions and not re-raise them."""
    mock_pipeline.side_effect = RuntimeError("boom")

    # Should not raise
    run_job(auto_publish=False)


@patch("auto_card_news_v2.runner.run_pipeline")
@patch("auto_card_news_v2.runner.load_settings")
def test_run_job_with_limit(mock_load, mock_pipeline):
    """run_job with limit should create a new Settings with the limit applied."""
    mock_pipeline.return_value = []

    run_job(auto_publish=False, limit=3)

    mock_pipeline.assert_called_once()
    settings_used = mock_pipeline.call_args[0][0]
    assert settings_used.max_items == 3


def test_create_scheduler():
    """start() should create a BlockingScheduler with the correct config."""
    from unittest.mock import call

    with (
        patch("auto_card_news_v2.runner.BlockingScheduler") as mock_sched_cls,
        patch("auto_card_news_v2.runner.run_job"),
        patch("auto_card_news_v2.runner.signal.signal"),
        patch("auto_card_news_v2.runner._setup_logging"),
    ):
        mock_sched = MagicMock()
        mock_sched_cls.return_value = mock_sched

        from auto_card_news_v2.runner import start

        start(interval_minutes=30, auto_publish=False, limit=2, timezone="UTC")

        mock_sched_cls.assert_called_once_with(timezone="UTC")
        mock_sched.add_job.assert_called_once()
        mock_sched.start.assert_called_once()

        # Verify job kwargs
        job_kwargs = mock_sched.add_job.call_args
        assert job_kwargs.kwargs["kwargs"] == {"auto_publish": False, "limit": 2}
