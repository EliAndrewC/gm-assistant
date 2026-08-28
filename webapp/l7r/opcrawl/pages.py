"""Parsers for the two Obsidian Portal pages the census reads: the pre-human-check gate (for the
exempt list) and a campaign's own front page (for its name, game system and last-updated).
Regex over saved fixture markup rather than a DOM walk - the markup is simple and the fixtures
pin it."""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass

_EXEMPT = re.compile(r"data-exempt-cses='([^']*)'")
_TITLE = re.compile(r'<title>\s*(.*?)\s*\|\s*Obsidian Portal\s*</title>', re.S)
_SYSTEM = re.compile(
    r"<div class='system-logo-container[^']*'>\s*<a href='/campaigns\?game_system_id=(?P<id>\d+)'>"
    r"\s*<img alt='(?P<name>[^']*)'",
    re.S,
)
_UPDATED = re.compile(r'Last Updated:.*?<time[^>]*datetime="([^"]*)"', re.S)


@dataclass(frozen=True)
class FrontPage:
    name: str
    game_system: str
    game_system_id: int | None
    updated: str


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


def parse_front_page(page_html: str) -> FrontPage:
    """Name, game system and last-updated from a campaign's front page. A campaign with no game
    system set (or a page without the sidebar) yields an empty system and `None` id."""
    title = _TITLE.search(page_html)
    system = _SYSTEM.search(page_html)
    updated = _UPDATED.search(page_html)
    return FrontPage(
        name=html.unescape(title.group(1)) if title else '',
        game_system=html.unescape(system['name']) if system else '',
        game_system_id=int(system['id']) if system else None,
        updated=updated.group(1) if updated else '',
    )
