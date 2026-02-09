"""Frozen dataclasses for all data flowing through the pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class FeedItem:
    """A single item fetched from an RSS feed."""

    title: str
    url: str
    summary: str | None = None
    published_at: str | None = None
    source_domain: str | None = None
    full_text: str | None = None


@dataclass(frozen=True)
class Story:
    """Structured story built from a feed item."""

    hook_title: str
    what_happened: str
    where_when: str
    impact: str
    key_details: tuple[str, ...]
    what_next: str
    tags: tuple[str, ...]
    source_domain: str | None = None
    source_url: str | None = None
    published_at: str | None = None


@dataclass(frozen=True)
class CardContent:
    """Content specification for a single card image."""

    title: str
    body: str
    card_index: int
    card_total: int
    footer: str = ""
    header: str = ""


@dataclass(frozen=True)
class ThreadsPost:
    """Complete output package ready for Threads upload."""

    image_paths: tuple[Path, ...]
    caption: str
    metadata: dict = field(default_factory=dict)
    output_dir: Path = Path(".")


@dataclass(frozen=True)
class ImageUpload:
    """Result of uploading a local image to a public host."""

    local_path: Path
    public_url: str
    upload_id: str  # Cloudinary public_id for cleanup


@dataclass(frozen=True)
class ThreadsPublishResult:
    """Result of a successful Threads publish."""

    post: ThreadsPost
    threads_id: str
    permalink: str
    published_at: str  # ISO 8601
