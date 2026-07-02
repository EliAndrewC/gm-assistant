"""Assemble the full-corpus setting brief for backstory synthesis.

This is the production home of the prompt a blind evaluation selected: the design
brief, the GM's "The Great Clans" framing (sliced live from l7r.md), the per-clan
flavor summary, and the entire canonical corpus (l7r.md + budgets.md).

It is a standalone, fully typed, fully covered module (Principle X) so the brief
assembly lives outside the grace-listed chargen modules. ``synthesis.py``
delegates ``load_brief`` here; the Gemini call stays the fixture-tested boundary.

Corpus resolution (first match wins):

1. ``$L7R_SETTING_DIR`` when set (explicit override).
2. The dev bind-mount at ``/host-l7r-repo/setting`` (live; preferred in dev so
   the GM's edits take effect immediately).
3. The bundled snapshot at ``<webapp>/setting`` (the prod fallback, produced by
   ``make prepare-deploy``; the deployed app has no bind-mount).

If no candidate holds both ``l7r.md`` and ``budgets.md`` a ``CorpusNotFound`` is
raised: the brief is never silently degraded to a thinner prompt.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

_CHARGEN_DIR = Path(__file__).resolve().parent
_BRIEF_PATH = _CHARGEN_DIR / 'synthesis_brief.md'
_FLAVOR_PATH = _CHARGEN_DIR / 'flavor_clans.md'

#: The dev bind-mount (live, preferred) and the bundled snapshot dir (sibling of
#: chargen, under webapp/; the prod fallback), tried in that order after the env
#: override.
_MOUNT_DIR = Path('/host-l7r-repo/setting')
_BUNDLED_DIR = _CHARGEN_DIR.parent / 'setting'

#: Heading in l7r.md whose block carries the materialist clan framing.
_CLAN_BLURB_HEADING = 'The Great Clans'


class CorpusNotFound(RuntimeError):
    """Raised when the canonical setting corpus cannot be located."""


def _read(path: Path) -> str:
    with open(path, encoding='utf-8') as f:
        return f.read()


def _candidate_dirs() -> list[Path]:
    """Corpus directories to try, in priority order."""
    dirs: list[Path] = []
    env = os.environ.get('L7R_SETTING_DIR')
    if env:
        dirs.append(Path(env))
    dirs.append(_MOUNT_DIR)
    dirs.append(_BUNDLED_DIR)
    return dirs


def _has_corpus(directory: Path) -> bool:
    return (directory / 'l7r.md').is_file() and (directory / 'budgets.md').is_file()


def resolve_corpus_dir() -> Path:
    """Return the first candidate dir holding both l7r.md and budgets.md."""
    tried: list[str] = []
    for directory in _candidate_dirs():
        tried.append(str(directory))
        if _has_corpus(directory):
            return directory
    raise CorpusNotFound(
        'Canonical setting corpus (l7r.md + budgets.md) not found. Tried: '
        + ', '.join(tried)
        + '. In the deployed app this means `make prepare-deploy` did not bundle '
        'the snapshot into webapp/setting/.'
    )


def extract_section(md_text: str, title: str) -> str:
    """Return one ATX heading's block: the heading plus its body up to the next
    heading of the same or higher level. Raises ``ValueError`` if not found."""
    lines = md_text.splitlines()
    start: int | None = None
    level = 0
    for i, line in enumerate(lines):
        match = re.match(r'^(#{1,6})\s+(.*?)\s*$', line)
        if match and match.group(2) == title:
            start = i
            level = len(match.group(1))
            break
    if start is None:
        raise ValueError(f'heading not found in canonical notes: {title!r}')

    end = len(lines)
    for j in range(start + 1, len(lines)):
        match = re.match(r'^(#{1,6})\s+', lines[j])
        if match and len(match.group(1)) <= level:
            end = j
            break
    return '\n'.join(lines[start:end]).strip()


def build_full_brief(corpus_dir: Path | None = None) -> str:
    """Assemble the full-corpus setting brief.

    The full-corpus assembly a blind evaluation selected: design brief + "The
    Great Clans" blurb + per-clan flavor + the entire l7r.md + a labeled
    budgets.md block. Pass ``corpus_dir`` to override resolution (e.g. in tests).
    """
    corpus = corpus_dir if corpus_dir is not None else resolve_corpus_dir()
    if not _has_corpus(corpus):
        raise CorpusNotFound(f'corpus dir is missing l7r.md or budgets.md: {corpus}')

    brief = _read(_BRIEF_PATH).strip()
    l7r = _read(corpus / 'l7r.md')
    flavor = _read(_FLAVOR_PATH).strip()
    clan_blurb = extract_section(l7r, _CLAN_BLURB_HEADING)
    budgets = _read(corpus / 'budgets.md').strip()

    base = '\n\n'.join([brief, clan_blurb, flavor])
    corpus_block = f'{l7r.strip()}\n\n# BUDGETS AND ECONOMIC MODEL (budgets.md)\n\n{budgets}'
    return '\n\n'.join([base, '# FULL CANONICAL NOTES\n\n' + corpus_block])
