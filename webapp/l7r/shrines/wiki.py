"""A shrine's Obsidian Portal wiki page (feature 228, FR-008): the only place a description and a
picture are saved (the GM: nothing is stored on fly.io).

The page is public, named after the shrine and tagged `shrine`; that name is how a link finds its
page, since it stays put while the options change. The body (Textile) is the picture, the
description and a link back to the design in the shrine builder. The GM-only notes hold the image
style and prompt between two marker lines, so a later visit can load them back. Everything here is
pure: the Obsidian Portal calls are passed in (`chargen.op` in the app, fakes in tests).
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, urlsplit

__all__ = [
    'LINK_TEXT',
    'TAG',
    'Saved',
    'build_body',
    'build_gm_info',
    'find_page',
    'merge_gm_info',
    'parse_page',
]

TAG = 'shrine'
LINK_TEXT = 'Open this shrine in the Shrine Builder'
_MARK_OPEN = '-- shrine builder: picture --'
_MARK_CLOSE = '-- end shrine builder --'
_FILE = re.compile(r'^\[\[File:\s*\d+[^\]]*\]\]$')
_LINK = re.compile(r'^"' + re.escape(LINK_TEXT) + r'":(\S+)$')
_IMG = re.compile(r'<img[^>]*\ssrc="([^"]+)"')


@dataclass(frozen=True, slots=True)
class Saved:
    """What a shrine's wiki page holds, read back."""

    url: str
    page_id: str
    params: dict[str, list[str]]
    description: str
    image_line: str
    image_url: str
    style: str
    prompt: str


def _norm(name: str) -> str:
    return ' '.join(name.split()).casefold()


def find_page(name: str, pages: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    """The listing entry for this shrine's page: same name (spacing and case aside), tagged."""
    for page in pages:
        if _norm(str(page.get('name', ''))) == _norm(name) and TAG in (page.get('tags') or []):
            return page
    return None


def _paragraphs(text: str) -> list[str]:
    return [
        ' '.join(p.split()) for p in re.split(r'\n\s*\n', text.replace('\r\n', '\n')) if p.strip()
    ]


def build_body(image_line: str, description: str, permalink: str) -> str:
    """Textile: the picture, the description's paragraphs, the link back. \\r\\n like OP's own."""
    blocks = [image_line, *_paragraphs(description), f'"{LINK_TEXT}":{permalink}']
    return '\r\n\r\n'.join(b for b in blocks if b)


def build_gm_info(style: str, prompt: str) -> str:
    return '\r\n'.join([_MARK_OPEN, f'style: {style}', 'prompt:', prompt.strip(), _MARK_CLOSE])


def merge_gm_info(existing: str, style: str, prompt: str) -> str:
    """Replace the shrine builder's block in the GM notes, keeping whatever the GM wrote there."""
    block = build_gm_info(style, prompt)
    pattern = re.compile(re.escape(_MARK_OPEN) + r'.*?' + re.escape(_MARK_CLOSE), re.S)
    if pattern.search(existing or ''):
        return pattern.sub(lambda _: block, existing)
    return f'{existing.rstrip()}\r\n\r\n{block}' if (existing or '').strip() else block


def parse_page(page: Mapping[str, Any]) -> Saved:
    body = str(page.get('body') or '')
    image_line = ''
    link = ''
    kept = []
    for block in re.split(r'\r?\n\s*\r?\n', body):
        stripped = block.strip()
        if not image_line and _FILE.match(stripped):
            image_line = stripped
        elif _LINK.match(stripped):
            link = _LINK.match(stripped).group(1)  # type: ignore[union-attr]
        elif stripped:
            kept.append(' '.join(stripped.split()))
    img = _IMG.search(str(page.get('body_html') or ''))
    gm = str(page.get('game_master_info') or '').replace('\r\n', '\n')
    style = re.search(r'^style: *(\S*)', gm, re.M)
    prompt = re.search(r'^prompt:\n(.*?)\n' + re.escape(_MARK_CLOSE), gm, re.S | re.M)
    return Saved(
        url=str(page.get('wiki_page_url') or ''),
        page_id=str(page.get('id') or ''),
        params=parse_qs(urlsplit(link).query) if link else {},
        description='\n\n'.join(kept),
        image_line=image_line,
        image_url=img.group(1).replace('&amp;', '&') if img else '',
        style=style.group(1) if style else '',
        prompt=prompt.group(1).strip() if prompt else '',
    )
