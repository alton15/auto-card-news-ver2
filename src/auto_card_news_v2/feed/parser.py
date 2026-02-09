"""Parse RSS/Atom feed bytes into FeedItem objects."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

from auto_card_news_v2.models import FeedItem

try:
    import feedparser  # type: ignore[import-untyped]

    _HAS_FEEDPARSER = True
except ImportError:
    _HAS_FEEDPARSER = False


def parse_feed(data: bytes, *, feed_url: str = "") -> list[FeedItem]:
    """Parse raw feed bytes into a list of FeedItem objects."""
    if _HAS_FEEDPARSER:
        return _parse_with_feedparser(data, feed_url)
    return _parse_with_xml(data, feed_url)


def _parse_with_feedparser(data: bytes, feed_url: str) -> list[FeedItem]:
    parsed = feedparser.parse(data)
    items: list[FeedItem] = []
    for entry in parsed.entries:
        title = getattr(entry, "title", "") or ""
        link = getattr(entry, "link", "") or ""
        summary = getattr(entry, "summary", None)
        published = getattr(entry, "published", None)
        domain = _extract_domain(link) or _extract_domain(feed_url)

        if title and link:
            items.append(FeedItem(
                title=_clean_html(title),
                url=link,
                summary=_clean_html(summary) if summary else None,
                published_at=published,
                source_domain=domain,
            ))
    return items


def _parse_with_xml(data: bytes, feed_url: str) -> list[FeedItem]:
    """Fallback XML parser for RSS and Atom feeds."""
    root = ET.fromstring(data)
    items: list[FeedItem] = []

    # RSS 2.0
    for item_el in root.iter("item"):
        title = _text(item_el, "title")
        link = _text(item_el, "link")
        summary = _text(item_el, "description")
        pub_date = _text(item_el, "pubDate")
        if title and link:
            items.append(FeedItem(
                title=_clean_html(title),
                url=link,
                summary=_clean_html(summary) if summary else None,
                published_at=pub_date,
                source_domain=_extract_domain(link) or _extract_domain(feed_url),
            ))

    # Atom
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for entry_el in root.iter("{http://www.w3.org/2005/Atom}entry"):
        title = _text(entry_el, "atom:title", ns)
        link_el = entry_el.find("atom:link[@rel='alternate']", ns)
        if link_el is None:
            link_el = entry_el.find("atom:link", ns)
        link = link_el.get("href", "") if link_el is not None else ""
        summary = _text(entry_el, "atom:summary", ns)
        updated = _text(entry_el, "atom:updated", ns)
        if title and link:
            items.append(FeedItem(
                title=_clean_html(title),
                url=link,
                summary=_clean_html(summary) if summary else None,
                published_at=updated,
                source_domain=_extract_domain(link) or _extract_domain(feed_url),
            ))

    return items


def _text(
    el: ET.Element, tag: str, ns: dict[str, str] | None = None,
) -> str | None:
    child = el.find(tag, ns) if ns else el.find(tag)
    if child is not None and child.text:
        return child.text.strip()
    return None


_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _clean_html(text: str) -> str:
    return _HTML_TAG_RE.sub("", text).strip()


def _extract_domain(url: str) -> str | None:
    if not url:
        return None
    try:
        host = urlparse(url).hostname or ""
        return host.removeprefix("www.") if host else None
    except Exception:
        return None
