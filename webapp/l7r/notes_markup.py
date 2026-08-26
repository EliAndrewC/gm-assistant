"""Markup for a name entry's authenticity notes on the /names page.

Two enrichments, both requested by the GM on 2026-08-26 after reading the
notes cold ("I had to look nanori up"):

- **Glossary tooltips.** Naming terms the notes lean on (nanori, tsusho,
  on-yomi ...) are wrapped in a ``<span class="term">`` carrying a short
  definition in ``data-tip``; the stylesheet draws a dotted underline and a
  tooltip on hover or keyboard focus. The definitions are deliberately one
  sentence: enough to read on, not a lecture.
- **Wikipedia links.** Historical bearers named in the notes ("Hojo Tokimune,
  the regent who faced the Mongol invasions") link to their English Wikipedia
  article. The mapping is data, not guesswork: ``wiki-links.json`` next to the
  pool holds only names that were checked against the Wikipedia API and
  resolved to a page in a person category (110 of 328 candidate phrases on
  2026-08-26; the rest were festivals, offices, places or phrases). Unknown
  names stay plain text.

The notes are trusted GM-side prose but are escaped anyway before markup is
added, so a stray ``<`` in a note can never become a tag.
"""

from __future__ import annotations

import html
import json
import re
from collections.abc import Callable
from functools import partial
from pathlib import Path

from markupsafe import Markup

#: Term -> one-sentence definition. Matched whole-word, case-insensitively.
#: Hyphen and space variants are listed explicitly so the regex stays simple.
GLOSSARY: dict[str, str] = {
    'nanori': "A samurai's formal two-kanji name, taken at coming of age; its characters use "
    'special name-only readings.',
    'tsusho': 'An everyday name used in place of the formal one, often a birth-order or '
    'office-style name such as Goro or Sukezaemon.',
    'yomyo': 'A childhood name, dropped at coming of age; often ends in -maru or -chiyo.',
    'on-yomi': 'The Chinese-derived reading of a kanji, used in words like Teishi or Genshin.',
    'on reading': 'The Chinese-derived reading of a kanji, used in words like Teishi or Genshin.',
    'on-reading': 'The Chinese-derived reading of a kanji, used in words like Teishi or Genshin.',
    'kun-yomi': 'The native Japanese reading of a kanji, the usual one in given names.',
    'kun reading': 'The native Japanese reading of a kanji, the usual one in given names.',
    'kun-reading': 'The native Japanese reading of a kanji, the usual one in given names.',
    'kana': 'The Japanese syllabic script (hiragana or katakana); a register written in kana '
    'records how a name sounded but not which kanji it used.',
    'hiragana': 'The cursive Japanese syllabary, used for native words and, in Edo registers, '
    "for most commoner women's names.",
    'katakana': 'The angular Japanese syllabary, used for foreign words and sometimes for names '
    'in old documents.',
    'kanji': 'The Chinese-derived characters; a name written in kanji carries a meaning as well '
    'as a sound.',
    'romaji': 'Japanese written in the Latin alphabet, as the names on this page are.',
    'ateji': 'Kanji chosen for their sound rather than their meaning.',
    'rendaku': 'The voicing of a consonant at the start of a second element (kami + kaze = '
    'kamikaze; ume + kae = Umegae).',
    'jukujikun': 'A whole-word reading assigned to a kanji compound that does not follow the '
    'characters one by one.',
    'genpuku': 'The coming-of-age ceremony at which a samurai boy received his adult name.',
    'kuge': 'The court nobility, as distinct from the warrior houses.',
    'daimyo': 'A great lord holding a domain.',
    'hatamoto': 'A direct retainer of the shogun.',
    'shumon aratame': 'The Edo-period household registers kept by temples, the main record of '
    "commoners' names.",
    'shumon-aratame-cho': 'The Edo-period household registers kept by temples, the main record of '
    "commoners' names.",
}

_TERM_RE = re.compile(
    r'(?<![\w-])('
    + '|'.join(re.escape(t) for t in sorted(GLOSSARY, key=len, reverse=True))
    + r')(?![\w-])',
    re.IGNORECASE,
)


def load_wiki_links(pool_dir: Path) -> dict[str, str]:
    """``wiki-links.json`` from the pool directory: ``{"Hojo Tokimune": url}``.
    Missing or malformed -> ``{}`` (the page still renders, links just do not
    appear)."""
    path = pool_dir / 'wiki-links.json'
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError, ValueError, OSError:
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(k): str(v) for k, v in data.items() if isinstance(v, str)}


def _link_once(pattern: re.Pattern[str], anchor: str, segment: str) -> str:
    """Replace the first whole-word match of ``pattern`` in ``segment`` with ``anchor``."""
    return pattern.sub(anchor, segment, count=1)


def render_notes(notes: str, links: dict[str, str] | None = None) -> Markup:
    """Escape ``notes`` and add bearer links and glossary tooltips."""
    text = html.escape(notes, quote=False)

    def outside_anchors(s: str, fn: Callable[[str], str]) -> str:
        """Apply ``fn`` to the stretches of ``s`` that are not already links,
        so a shorter bearer name never re-links inside a longer one's anchor
        and a glossary term inside link text stays plain."""
        parts = re.split(r'(<a [^>]*>.*?</a>)', s)
        return ''.join(p if p.startswith('<a ') else fn(p) for p in parts)

    if links:
        # Longest names first so "Minamoto no Yoshitsune" wins over "Yoshitsune".
        for name in sorted(links, key=len, reverse=True):
            escaped = html.escape(name, quote=False)
            pattern = re.compile(r'(?<!\w)' + re.escape(escaped) + r'(?!\w)')
            url = html.escape(links[name], quote=True)
            anchor = f'<a class="wiki" href="{url}" target="_blank" rel="noopener">{escaped}</a>'
            text = outside_anchors(text, partial(_link_once, pattern, anchor))

    def _term(m: re.Match[str]) -> str:
        tip = html.escape(GLOSSARY[m.group(1).lower()], quote=True)
        return f'<span class="term" tabindex="0" data-tip="{tip}">{m.group(1)}</span>'

    return Markup(outside_anchors(text, lambda p: _TERM_RE.sub(_term, p)))
