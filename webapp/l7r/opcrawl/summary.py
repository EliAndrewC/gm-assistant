"""`content_summary.json` - Obsidian Portal's own manifest of one campaign's content.

The GM found this endpoint on 2026-08-28 and it replaces link discovery as the way a campaign's
pages are enumerated: one request returns every wiki page, adventure-log post, character, item
and forum topic, each with its path, title, tags and a `gm_only` flag. That is both the complete
crawl list AND, on its own, the answer to "who has uploaded a lot of content" - which is why the
CLI can fetch summaries alone and rank campaigns without reading a single content page.

Measured on the GM's own campaign, 2026-08-28 (four requests, 21 s apart):

* `?cc=<n>` is REQUIRED - without it the endpoint answers HTTP 400 - but its VALUE is ignored:
  `cc=1` returned content byte-identical to the timestamp a browser had sent (56,451 bytes both
  times). It is an ordinary cache-buster, not a token or a credential. We send the current Unix
  time, which is what the site's own pages do.
* The `human_check=` cookie is needed exactly as it is for every other campaign page; without it
  the pre-human-check gate HTML comes back instead. So this endpoint is reachable only for
  campaigns whose owners opted in - the same consent boundary, enforced the same way.
* `gm_only` marks pages the owner keeps private. We never request one: they are not ours to
  read, and the flag says so before we ask.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

# The JSON's list keys, and the page kind each holds. `tags` is a bare list of strings, not pages.
KINDS = {
    'wiki_pages': 'wiki',
    'blog_posts': 'post',
    'game_characters': 'character',
    'game_items': 'item',
    'forum_topics': 'forum',
}


@dataclass(frozen=True)
class SummaryPage:
    kind: str
    title: str
    path: str
    tags: tuple[str, ...]
    gm_only: bool


@dataclass(frozen=True)
class ContentSummary:
    campaign_id: int
    updated_at: str
    version: str
    pages: tuple[SummaryPage, ...]
    tags: tuple[str, ...]

    @property
    def public(self) -> list[SummaryPage]:
        """The pages we may read - everything the owner did not mark GM-only."""
        return [p for p in self.pages if not p.gm_only]

    @property
    def counts(self) -> dict[str, int]:
        """Public pages per kind - the "how much content is here" measure."""
        counts: dict[str, int] = {}
        for page in self.public:
            counts[page.kind] = counts.get(page.kind, 0) + 1
        return counts


def summary_url(slug: str, unix_time: int) -> str:
    """The endpoint for one campaign. `cc` is a cache-buster; any value works (see the module
    docstring), so we send the current Unix time as the site's own pages do."""
    return f'https://{slug}.obsidianportal.com/content_summary.json?cc={unix_time}'


def parse_content_summary(text: str) -> ContentSummary:
    """Parse the endpoint's JSON. Raises ValueError on anything that is not this shape."""
    raw = json.loads(text)
    if not isinstance(raw, dict) or 'wiki_pages' not in raw:
        raise ValueError('not a content_summary.json payload')
    pages = tuple(
        SummaryPage(
            kind=kind,
            title=str(entry.get('title') or ''),
            path=str(entry['path']),
            tags=tuple(str(t) for t in entry.get('tags') or ()),
            gm_only=bool(entry.get('gm_only')),
        )
        for key, kind in KINDS.items()
        for entry in raw.get(key) or ()
        if entry.get('path')
    )
    return ContentSummary(
        campaign_id=int(raw.get('id') or 0),
        updated_at=str(raw.get('updated_at') or ''),
        version=str(raw.get('version') or ''),
        pages=pages,
        tags=tuple(str(t) for t in raw.get('tags') or ()),
    )
