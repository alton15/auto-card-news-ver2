"""Write images, caption, and metadata to output directory."""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from auto_card_news_v2.models import Story, ThreadsPost


def package_output(
    story: Story,
    image_paths: list[Path],
    caption: str,
    output_base: Path,
) -> ThreadsPost:
    """Package all outputs into a timestamped folder. Returns ThreadsPost."""
    folder_name = _build_folder_name(story)
    output_dir = output_base / folder_name
    output_dir.mkdir(parents=True, exist_ok=True)

    # Copy images into output folder
    final_paths: list[Path] = []
    for src in image_paths:
        dst = output_dir / src.name
        if src.resolve() != dst.resolve():
            shutil.copy2(src, dst)
        final_paths.append(dst)

    # Write caption
    caption_path = output_dir / "caption.txt"
    caption_path.write_text(caption, encoding="utf-8")

    # Write metadata
    metadata = _build_metadata(story, final_paths, caption)
    meta_path = output_dir / "metadata.json"
    meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    return ThreadsPost(
        image_paths=tuple(final_paths),
        caption=caption,
        metadata=metadata,
        output_dir=output_dir,
    )


def _build_folder_name(story: Story) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    slug = _slugify(story.hook_title)
    return f"{ts}_{slug}"


def _slugify(text: str, *, max_len: int = 40) -> str:
    slug = re.sub(r"[^a-zA-Z0-9\uac00-\ud7a3]+", "-", text.lower())
    slug = slug.strip("-")
    return slug[:max_len]


def _build_metadata(
    story: Story,
    image_paths: list[Path],
    caption: str,
) -> dict:
    return {
        "title": story.hook_title,
        "source_domain": story.source_domain,
        "source_url": story.source_url,
        "published_at": story.published_at,
        "tags": list(story.tags),
        "num_cards": len(image_paths),
        "image_files": [p.name for p in image_paths],
        "caption_length": len(caption),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
