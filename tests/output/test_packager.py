"""Tests for output packager."""

from __future__ import annotations

from pathlib import Path

from auto_card_news_v2.output.packager import package_output


def test_package_output_creates_files(sample_story, tmp_path):
    fake_images = []
    for i in range(3):
        p = tmp_path / f"card_{i:02d}.png"
        p.write_bytes(b"\x89PNG fake")
        fake_images.append(p)

    caption = "Test caption\n#test"
    post = package_output(sample_story, fake_images, caption, tmp_path)

    assert post.output_dir.exists()
    assert (post.output_dir / "caption.txt").exists()
    assert (post.output_dir / "metadata.json").exists()

    caption_text = (post.output_dir / "caption.txt").read_text()
    assert "Test caption" in caption_text
