"""Tests for threads token_store module."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from auto_card_news_v2.threads.token_store import (
    load_token,
    refresh_if_needed,
    save_token,
)


def test_save_and_load_token(tmp_path):
    path = tmp_path / "token.json"
    save_token("tok_abc123", expires_in=5_184_000, token_path=path)

    token = load_token(token_path=path)
    assert token == "tok_abc123"


def test_load_token_missing_file(tmp_path):
    path = tmp_path / "nonexistent.json"
    assert load_token(token_path=path) is None


def test_load_token_corrupted_file(tmp_path):
    path = tmp_path / "token.json"
    path.write_text("not json!!", encoding="utf-8")
    assert load_token(token_path=path) is None


def test_load_token_expired(tmp_path):
    path = tmp_path / "token.json"
    expired = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    data = {"access_token": "old_tok", "expires_in": 0, "expires_at": expired}
    path.write_text(json.dumps(data), encoding="utf-8")

    assert load_token(token_path=path) is None


def test_load_token_still_valid(tmp_path):
    path = tmp_path / "token.json"
    future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    data = {"access_token": "valid_tok", "expires_in": 5_184_000, "expires_at": future}
    path.write_text(json.dumps(data), encoding="utf-8")

    assert load_token(token_path=path) == "valid_tok"


def test_save_token_creates_parent_dirs(tmp_path):
    path = tmp_path / "nested" / "dir" / "token.json"
    save_token("tok_xyz", expires_in=3600, token_path=path)
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["access_token"] == "tok_xyz"


def test_refresh_if_needed_fresh_token(tmp_path):
    path = tmp_path / "token.json"
    future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    data = {"access_token": "fresh_tok", "expires_in": 5_184_000, "expires_at": future}
    path.write_text(json.dumps(data), encoding="utf-8")

    result = refresh_if_needed("fresh_tok", token_path=path)
    assert result == "fresh_tok"


def test_refresh_if_needed_expiring_soon(tmp_path, monkeypatch):
    path = tmp_path / "token.json"
    # Expires in 3 days — within the 7-day threshold
    soon = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    data = {"access_token": "expiring_tok", "expires_in": 259_200, "expires_at": soon}
    path.write_text(json.dumps(data), encoding="utf-8")

    # Mock _do_refresh to avoid actual HTTP call
    monkeypatch.setattr(
        "auto_card_news_v2.threads.token_store._do_refresh",
        lambda token, *, token_path: "refreshed_tok",
    )

    result = refresh_if_needed("expiring_tok", token_path=path)
    assert result == "refreshed_tok"


def test_refresh_if_needed_no_file(tmp_path):
    path = tmp_path / "missing.json"
    result = refresh_if_needed("my_tok", token_path=path)
    assert result == "my_tok"
