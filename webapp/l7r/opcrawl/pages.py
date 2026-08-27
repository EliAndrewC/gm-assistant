"""Parsers for the two Obsidian Portal pages the census reads: the pre-human-check gate (for the
exempt list) and the campaign browse listing (for the L5R roster). Regex over saved fixture
markup rather than a DOM walk - the markup is simple and the fixtures pin it."""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass

_EXEMPT = re.compile(r"data-exempt-cses='([^']*)'")
_TILE = re.compile(
    r"<a class='campaign-thumb-and-info' href='https://(?P<slug>[a-z0-9-]+)\.obsidianportal\.com/'>"
    r'.*?<h4 class=\'underlined name\'>\s*(?P<name>.*?)\s*</h4>'
    r'\s*<small class=\'underlined name\'>\s*(?P<visibility>.*?)\s*</small>'
    r'(?:.*?<span class=\'game-system\'>(?P<system>.*?)</span>)?'
    r'(?:.*?<time[^>]*datetime="(?P<updated>[^"]*)")?'
    r'.*?</a>',
    re.S,
)
_PAGE = re.compile(r'[?&;]page=(\d+)')


@dataclass(frozen=True)
class Campaign:
    slug: str
    name: str
    visibility: str
    game_system: str
    updated: str

    @property
    def url(self) -> str:
        return f'https://{self.slug}.obsidianportal.com/'


def parse_exempt_slugs(gate_html: str) -> frozenset[str]:
    """The `data-exempt-cses` list from the pre-human-check page - the site-wide set of
    campaigns whose owners turned on "allow bots"."""
    m = _EXEMPT.search(gate_html)
    if m is None:
        raise ValueError('no data-exempt-cses attribute on the gate page')
    slugs = json.loads(html.unescape(m.group(1)))
    if not isinstance(slugs, list) or not all(isinstance(s, str) for s in slugs):
        raise ValueError('data-exempt-cses is not a list of slugs')
    return frozenset(slugs)


def parse_browse(page_html: str) -> tuple[list[Campaign], int]:
    """The campaign tiles on one browse page, plus the total page count (max `page=N` seen;
    1 when the listing has no pagination)."""
    tiles = [
        Campaign(
            slug=m['slug'],
            name=html.unescape(m['name']),
            visibility=m['visibility'],
            game_system=html.unescape(m['system'] or ''),
            updated=m['updated'] or '',
        )
        for m in _TILE.finditer(page_html)
    ]
    pages = [int(n) for n in _PAGE.findall(page_html)]
    return tiles, max(pages, default=1)
