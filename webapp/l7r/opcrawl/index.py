"""Stage 3: the local index over cached campaigns that lets a session act as summarizer and
search engine - "which campaigns have deep wikis", "whose characters have real backstories",
"who is running a Scorpion court game" - and point the GM at the page on Obsidian Portal.

Everything here reads the cache only. A campaign counts as indexed once EITHER its
`content_summary.json` or its page manifest is present, so a summaries-only pass (one request
per campaign) already answers "who has uploaded a lot of content", with every page's title and
tags listed and marked cached or not. `build_index` writes `index.json` and `index.md`, the
digest a session reads whole; `search` greps the text of the pages that were fetched.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from l7r.opcrawl.census import OUT_DIR
from l7r.opcrawl.fetch import Manifest, PageRecord, Store

SNIPPET = 240
CONTENT_KINDS = ('wiki', 'character', 'post', 'item', 'forum')


@dataclass
class PageEntry:
    kind: str
    title: str
    url: str
    chars: int
    snippet: str
    cached: bool
    tags: tuple[str, ...] = ()


@dataclass
class CampaignEntry:
    slug: str
    name: str
    url: str
    counts: dict[str, int] = field(default_factory=dict)  # pages CACHED, by kind
    chars: dict[str, int] = field(default_factory=dict)
    available: dict[str, int] = field(default_factory=dict)  # pages the campaign PUBLISHES
    tags: tuple[str, ...] = ()
    pages: list[PageEntry] = field(default_factory=list)

    @property
    def total_chars(self) -> int:
        return sum(self.chars.values())

    @property
    def total_available(self) -> int:
        return sum(self.available.values())


def _snippet(text: str) -> str:
    flat = re.sub(r'\s+', ' ', text).strip()
    return flat[:SNIPPET] + ('...' if len(flat) > SNIPPET else '')


def _page_text(root: Path, slug: str, rec: PageRecord) -> str:
    if not rec.file:
        return ''
    return (root / slug / 'pages' / f'{rec.file}.txt').read_text()


def iter_slugs(root: Path = OUT_DIR) -> list[str]:
    """Every campaign with something cached - a page manifest, a content summary, or both."""
    found = {p.parent.name for p in root.glob('*/manifest.json')}
    found |= {p.parent.name for p in root.glob('*/content_summary.json')}
    return sorted(found)


def build_entry(root: Path, slug: str, names: dict[str, str] | None = None) -> CampaignEntry:
    store = Store(root)
    manifest = Manifest.load(store.manifest_path(slug), slug)
    summary = store.read_summary(slug)
    front = next((r for r in manifest.pages.values() if r.kind == 'front'), None)
    entry = CampaignEntry(
        slug,
        (names or {}).get(slug) or (front.title if front else '') or slug,
        f'https://{slug}.obsidianportal.com/',
        available=summary.counts if summary else {},
        tags=summary.tags if summary else (),
    )
    cached = {
        rec.url: rec
        for rec in manifest.pages.values()
        if rec.status == 200 and rec.kind in CONTENT_KINDS
    }
    listed = (
        [
            PageEntry(
                p.kind, p.title, f'https://{slug}.obsidianportal.com{p.path}', 0, '', False, p.tags
            )
            for p in summary.public
        ]
        if summary
        else []
    )
    for page in listed:
        rec = cached.pop(page.url, None)
        if rec is not None:
            page.cached = True
            page.chars = rec.chars
            page.snippet = _snippet(_page_text(root, slug, rec))
            page.title = page.title or rec.title
    # Pages fetched by link discovery that no summary listed (a campaign without the endpoint).
    listed += [
        PageEntry(r.kind, r.title, r.url, r.chars, _snippet(_page_text(root, slug, r)), True)
        for r in cached.values()
    ]
    for page in listed:
        if page.cached:
            entry.counts[page.kind] = entry.counts.get(page.kind, 0) + 1
            entry.chars[page.kind] = entry.chars.get(page.kind, 0) + page.chars
    entry.pages = sorted(listed, key=lambda p: (p.kind, -p.chars, p.title))
    return entry


def digest(entries: list[CampaignEntry]) -> str:
    lines = ['# Obsidian Portal L5R campaigns - local index', '']
    for e in sorted(entries, key=lambda e: (-e.total_available, -e.total_chars, e.slug)):
        published = (
            ', '.join(f'{n} {k}s' for k, n in sorted(e.available.items())) or 'nothing listed'
        )
        cached = ', '.join(f'{n} {k}s' for k, n in sorted(e.counts.items())) or 'no pages'
        lines += [
            f'## {e.name} ({e.slug})',
            f'{e.url}',
            f'publishes {published}; cached {cached}, {e.total_chars:,} characters of text',
        ]
        if e.tags:
            lines.append(f'tags: {", ".join(e.tags[:40])}')
        lines.append('')
        for p in e.pages:
            mark = '' if p.cached else ' [not cached]'
            tags = f'  {{{", ".join(p.tags)}}}' if p.tags else ''
            lines.append(
                f'- [{p.kind}] {p.title or "(untitled)"} ({p.chars:,}){mark} {p.url}{tags}'
            )
            if p.snippet:
                lines.append(f'  {p.snippet}')
        lines.append('')
    return '\n'.join(lines).rstrip() + '\n'


def build_index(root: Path = OUT_DIR, names: dict[str, str] | None = None) -> list[CampaignEntry]:
    entries = [build_entry(root, slug, names) for slug in iter_slugs(root)]
    (root / 'index.json').write_text(json.dumps([asdict(e) for e in entries], indent=1) + '\n')
    (root / 'index.md').write_text(digest(entries))
    return entries


@dataclass(frozen=True)
class Hit:
    slug: str
    title: str
    url: str
    context: str


def search(pattern: str, root: Path = OUT_DIR, *, width: int = 80) -> list[Hit]:
    """Case-insensitive regex search over every cached page's text; one hit per page."""
    rx = re.compile(pattern, re.I)
    hits: list[Hit] = []
    for slug in iter_slugs(root):
        manifest = Manifest.load(Store(root).manifest_path(slug), slug)
        for rec in manifest.pages.values():
            text = _page_text(root, slug, rec)
            m = rx.search(text)
            if m is None:
                continue
            lo, hi = max(0, m.start() - width), min(len(text), m.end() + width)
            hits.append(Hit(slug, rec.title, rec.url, re.sub(r'\s+', ' ', text[lo:hi]).strip()))
    return hits
