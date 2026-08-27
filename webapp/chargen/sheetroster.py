"""Characters on the GM's character-sheet app, as a given-name exclusion source.

<https://l7r-character-sheet.fly.dev/> lists every character that belongs to
a gaming group on its index page. A PC there may have no Obsidian Portal
record at all, so the OP roster alone misses them - the motivating case is
Hidemasa, a PC on the sheet app, handed out as a fresh name on 2026-08-25
(GM 2026-08-27). The index is fetched at most once per ``max_age`` and
cached in ``webapp/opcache/sheet-characters.json`` (gitignored) under the
same rules as the OP roster cache; ``opcache.used_given_names`` reads it.

Only characters INSIDE a group count (a section with a ``/groups/<id>``
link); the unassigned bucket is skipped, as the GM specified.
"""

from __future__ import annotations

import json
import logging
import re
import time
from collections.abc import Callable
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

INDEX_URL = 'https://l7r-character-sheet.fly.dev/'
CACHE_PATH = Path(__file__).resolve().parent.parent / 'opcache' / 'sheet-characters.json'

_SECTION_RE = re.compile(r'<section[^>]*data-group-section=(.*?)</section>', re.DOTALL)
_NAME_RE = re.compile(r'<h2 class="text-lg font-bold text-accent truncate">\s*([^<]*?)\s*</h2>')


def parse_index(html: str) -> list[str]:
    """Full names of every character in a gaming group, in page order."""
    names: list[str] = []
    for section in _SECTION_RE.findall(html):
        if 'data-testid="group-link"' not in section:
            continue  # the unassigned bucket has no group link
        names.extend(n for n in _NAME_RE.findall(section) if n)
    return names


def fetch_index() -> str:
    response = requests.get(INDEX_URL, timeout=20)
    response.raise_for_status()
    return str(response.text)


def cache_age(path: Path = CACHE_PATH) -> float | None:
    try:
        return time.time() - path.stat().st_mtime
    except FileNotFoundError:
        return None


def refresh_if_stale(
    max_age_seconds: float = 3600.0,
    path: Path = CACHE_PATH,
    fetch: Callable[[], str] | None = None,
) -> bool:
    """Re-read the index when the cache is missing or older than
    ``max_age_seconds``. Fail-soft like the OP cache: a fetch error or an
    empty page is logged and the last cache is kept. True when written."""
    age = cache_age(path)
    if age is not None and age < max_age_seconds:
        return False
    # Resolved at CALL time, not as a default argument: a default binds the
    # function object at import, so tests patching ``fetch_index`` still hit
    # the network (measured 2026-08-27 - a real cache file appeared mid-test).
    fetch = fetch or fetch_index
    try:
        names = parse_index(fetch())
    except Exception as e:  # network boundary
        logger.warning('sheetroster: could not fetch %s: %s', INDEX_URL, e)
        return False
    if not names:
        logger.warning('sheetroster: no characters parsed from %s; keeping the cache', INDEX_URL)
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'names': names}, indent=2), encoding='utf-8')
    logger.info('sheetroster: refreshed %s (%d characters)', path, len(names))
    return True


def full_names(path: Path = CACHE_PATH) -> list[str]:
    """The cached names, or [] when there is no usable cache."""
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except OSError, ValueError:
        return []
    names = data.get('names') if isinstance(data, dict) else None
    return [str(n) for n in names] if isinstance(names, list) else []


_LATIN = re.compile(r"[A-Za-z][A-Za-z'\-]*")


def given_name(full: str) -> str:
    """The last LATIN token: ``Tsuruchi Makoto 鶴知誠`` -> ``Makoto`` (the
    sheet app lets a player append kanji to their name)."""
    latin = [t for t in full.split() if _LATIN.fullmatch(t)]
    return latin[-1] if latin else ''


def given_names(path: Path = CACHE_PATH) -> frozenset[str]:
    """Given name of each cached character (see :func:`given_name`)."""
    return frozenset(g for g in (given_name(n) for n in full_names(path)) if g)
