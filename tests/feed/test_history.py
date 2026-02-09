"""Tests for persistent publish history."""

from __future__ import annotations

import json

from auto_card_news_v2.feed.history import (
    filter_already_published,
    load_history,
    save_url,
)
from auto_card_news_v2.models import FeedItem


def _make_item(url: str, title: str = "Test") -> FeedItem:
    return FeedItem(title=title, url=url)


def test_load_history_missing_file(tmp_path):
    path = tmp_path / "history.json"
    result = load_history(history_path=path)
    assert result == set()


def test_load_history_empty_file(tmp_path):
    path = tmp_path / "history.json"
    path.write_text('{"urls": {}}', encoding="utf-8")
    result = load_history(history_path=path)
    assert result == set()


def test_load_history_corrupted_json(tmp_path):
    path = tmp_path / "history.json"
    path.write_text("not valid json!!!", encoding="utf-8")
    result = load_history(history_path=path)
    assert result == set()


def test_save_url_creates_file(tmp_path):
    path = tmp_path / "history.json"
    save_url("https://example.com/article1", history_path=path)

    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "https://example.com/article1" in data["urls"]


def test_save_url_appends(tmp_path):
    path = tmp_path / "history.json"
    save_url("https://example.com/a", history_path=path)
    save_url("https://example.com/b", history_path=path)

    urls = load_history(history_path=path)
    assert "https://example.com/a" in urls
    assert "https://example.com/b" in urls


def test_save_url_normalizes(tmp_path):
    path = tmp_path / "history.json"
    save_url("https://Example.COM/Article/", history_path=path)

    urls = load_history(history_path=path)
    assert "https://example.com/article" in urls


def test_save_url_creates_parent_dirs(tmp_path):
    path = tmp_path / "nested" / "dir" / "history.json"
    save_url("https://example.com/x", history_path=path)
    assert path.exists()


def test_save_url_handles_corrupted_existing(tmp_path):
    path = tmp_path / "history.json"
    path.write_text("bad json", encoding="utf-8")
    save_url("https://example.com/recover", history_path=path)

    urls = load_history(history_path=path)
    assert "https://example.com/recover" in urls


def test_load_history_reflects_saved(tmp_path):
    path = tmp_path / "history.json"
    save_url("https://example.com/saved", history_path=path)

    urls = load_history(history_path=path)
    assert "https://example.com/saved" in urls


def test_filter_already_published_removes_known(tmp_path):
    path = tmp_path / "history.json"
    save_url("https://example.com/old", history_path=path)

    items = [
        _make_item("https://example.com/old", "Old"),
        _make_item("https://example.com/new", "New"),
    ]
    result = filter_already_published(items, history_path=path)
    assert len(result) == 1
    assert result[0].title == "New"


def test_filter_already_published_empty_history(tmp_path):
    path = tmp_path / "history.json"
    items = [_make_item("https://example.com/a")]
    result = filter_already_published(items, history_path=path)
    assert len(result) == 1


def test_filter_already_published_normalizes_urls(tmp_path):
    path = tmp_path / "history.json"
    save_url("https://example.com/article", history_path=path)

    items = [_make_item("https://Example.COM/Article/")]
    result = filter_already_published(items, history_path=path)
    assert len(result) == 0
