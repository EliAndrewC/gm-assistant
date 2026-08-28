"""Stage 3: the local index over cached campaigns that lets a session act as summarizer and
search engine - "which campaigns have deep wikis", "whose characters have real backstories",
"who is running a Scorpion court game" - and point the GM at the page on Obsidian Portal.

Everything here reads the cache only. `build_index` writes `opcache/opcrawl/index.json` (per
campaign: page counts by kind, prose volume, every page's title/url/length/snippet) and
`index.md`, a digest a session can read whole. `search` greps the cached text."""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from dataclasses import asdict, dataclass, field
from pathlib import Path

from l7r.opcrawl.census import OUT_DIR
from l7r.opcrawl.fetch import Manifest, PageRecord

SNIPPET = 240


@dataclass
class PageEntry:
    kind: str
    title: str
    url: str
    chars: int
    snippet: str


@dataclass
class CampaignEntry:
    slug: str
    name: str
    url: str
    counts: dict[str, int] = field(default_factory=dict)
    chars: dict[str, int] = field(default_factory=dict)
    pages: list[PageEntry] = field(default_factory=list)

    @property
    def total_chars(self) -> int:
        return sum(self.chars.values())


def _snippet(text: str) -> str:
    flat = re.sub(r'\s+', ' ', text).strip()
    return flat[:SNIPPET] + ('...' if len(flat) > SNIPPET else '')


def _page_text(root: Path, slug: str, rec: PageRecord) -> str:
    if not rec.file:
        return ''
    return (root / slug / 'pages' / f'{rec.file}.txt').read_text()


def iter_manifests(root: Path = OUT_DIR) -> Iterator[Manifest]:
    for path in sorted(root.glob('*/manifest.json')):
        yield Manifest.load(path, path.parent.name)


def build_entry(root: Path, manifest: Manifest) -> CampaignEntry:
    front = next((r for r in manifest.pages.values() if r.kind == 'front'), None)
    entry = CampaignEntry(
        manifest.slug,
        front.title if front else manifest.slug,
        f'https://{manifest.slug}.obsidianportal.com/',
    )
    for rec in manifest.pages.values():
        if rec.status != 200 or rec.kind in ('front', 'index', 'other'):
            continue
        entry.counts[rec.kind] = entry.counts.get(rec.kind, 0) + 1
        entry.chars[rec.kind] = entry.chars.get(rec.kind, 0) + rec.chars
        entry.pages.append(
            PageEntry(
                rec.kind,
                rec.title,
                rec.url,
                rec.chars,
                _snippet(_page_text(root, manifest.slug, rec)),
            )
        )
    entry.pages.sort(key=lambda p: (p.kind, -p.chars))
    return entry


def digest(entries: list[CampaignEntry]) -> str:
    lines = ['# Obsidian Portal L5R campaigns - local index', '']
    for e in sorted(entries, key=lambda e: -e.total_chars):
        counts = ', '.join(f'{n} {k}s' for k, n in sorted(e.counts.items())) or 'no content pages'
        lines += [
            f'## {e.name} ({e.slug})',
            f'{e.url}  -  {counts}, {e.total_chars:,} characters of text',
            '',
        ]
        for p in e.pages:
            lines.append(f'- [{p.kind}] {p.title or "(untitled)"} ({p.chars:,}) {p.url}')
            if p.snippet:
                lines.append(f'  {p.snippet}')
        lines.append('')
    return '\n'.join(lines).rstrip() + '\n'


def build_index(root: Path = OUT_DIR) -> list[CampaignEntry]:
    entries = [build_entry(root, m) for m in iter_manifests(root)]
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
    for manifest in iter_manifests(root):
        for rec in manifest.pages.values():
            text = _page_text(root, manifest.slug, rec)
            m = rx.search(text)
            if m is None:
                continue
            lo, hi = max(0, m.start() - width), min(len(text), m.end() + width)
            hits.append(
                Hit(manifest.slug, rec.title, rec.url, re.sub(r'\s+', ' ', text[lo:hi]).strip())
            )
    return hits
