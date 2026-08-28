"""Generic HTML -> text for cached campaign pages. Structure-light on purpose: the pages are only
read locally, by a session answering the GM's questions, so a faithful-enough plain text with
headings and paragraphs preserved beats a brittle per-template parser."""

from __future__ import annotations

import html
import re

_DROP = re.compile(r'<(script|style|noscript|svg|head)\b.*?</\1\s*>', re.S | re.I)
_COMMENT = re.compile(r'<!--.*?-->', re.S)
_BLOCK = re.compile(
    r'</?(p|div|br|li|ul|ol|h[1-6]|tr|table|blockquote|section|article|header|footer|nav|dd|dt|dl|hr)\b[^>]*>',
    re.I,
)
_TAG = re.compile(r'<[^>]+>')
_TITLE = re.compile(r'<title>\s*(.*?)\s*</title>', re.S | re.I)
_BLANKS = re.compile(r'\n\s*\n+')
_SPACES = re.compile(r'[ \t\r\f\v\xa0]+')


def page_title(page_html: str) -> str:
    """The `<title>` minus Obsidian Portal's ` | Campaign | Obsidian Portal` suffixes."""
    m = _TITLE.search(page_html)
    if m is None:
        return ''
    parts = [p.strip() for p in html.unescape(m.group(1)).split('|')]
    if parts and parts[-1] == 'Obsidian Portal':
        parts.pop()
    return parts[0] if parts else ''


def strip_scripts(page_html: str) -> str:
    """Drop script/style/head blocks and comments - never a source of links or prose."""
    return _COMMENT.sub(' ', _DROP.sub(' ', page_html))


def html_to_text(page_html: str) -> str:
    body = strip_scripts(page_html)
    body = _BLOCK.sub('\n', body)
    body = _TAG.sub(' ', body)
    body = html.unescape(body)
    lines = [_SPACES.sub(' ', line).strip() for line in body.split('\n')]
    return _BLANKS.sub('\n\n', '\n'.join(lines)).strip()
