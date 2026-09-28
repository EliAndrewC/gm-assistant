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

The sheet's generated NPCs (its combat tracker, feature 213) are NOT on that
public page - they are invisible to players - so their names come from the
sheet's authenticated ``GET /api/characters``, which flags them ``is_npc``
(the GM's design, character-sheet ``combat-design/design.md`` 4.6). They ride
in the same cache file under ``npcs`` and count as used like everyone else.
"""

from __future__ import annotations

import configparser
import json
import logging
import re
import time
from collections.abc import Callable
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

INDEX_URL = 'https://l7r-character-sheet.fly.dev/'
API_URL = 'https://l7r-character-sheet.fly.dev/api/characters'
SECRETS = Path(__file__).resolve().parent.parent / 'development-secrets.ini'
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


def query_token(path: Path | None = None) -> str:
    """The sheet's GM read token, ``[character_sheet] roll_query_token``.

    The same key ``l7r.repl.rolls.sheet.query_token`` reads; a test pins the two
    together. Not imported from there because that would pull the whole REPL
    namespace into the webapp at refresh time. ``path`` resolves at call time."""
    parser = configparser.ConfigParser()  # exactly as the REPL client reads it
    parser.read(path or SECRETS)
    return parser.get('character_sheet', 'roll_query_token', fallback='').strip()


def parse_npcs(payload: object) -> list[str]:
    """Full names of the characters ``/api/characters`` flags ``is_npc``.
    A payload with no ``characters`` list is malformed (``ValueError``) - NOT
    "no NPCs", which would wipe the cached list."""
    characters = payload.get('characters') if isinstance(payload, dict) else None
    if not isinstance(characters, list):
        raise ValueError('no characters list in the /api/characters payload')
    return [
        str(c['name'])
        for c in characters
        if isinstance(c, dict) and c.get('is_npc') and c.get('name')
    ]


def fetch_npc_names() -> list[str]:
    token = query_token()
    if not token:
        raise RuntimeError('no [character_sheet] roll_query_token in development-secrets.ini')
    response = requests.get(API_URL, headers={'Authorization': f'Bearer {token}'}, timeout=20)
    response.raise_for_status()
    return parse_npcs(response.json())


def cache_age(path: Path = CACHE_PATH) -> float | None:
    try:
        return time.time() - path.stat().st_mtime
    except FileNotFoundError:
        return None


def refresh_if_stale(
    max_age_seconds: float = 3600.0,
    path: Path = CACHE_PATH,
    fetch: Callable[[], str] | None = None,
    fetch_npcs: Callable[[], list[str]] | None = None,
) -> bool:
    """Re-read the index (and the NPC list) when the cache is missing or older
    than ``max_age_seconds``. Fail-soft like the OP cache: a fetch error or an
    empty page is logged and the last cache is kept. True when written.

    The NPC fetch runs only once the index has succeeded, and its failure keeps
    the cached ``npcs`` (an empty list from a WORKING fetch is a real answer).
    Writing on an index failure is avoided on purpose: the file's age is the
    retry signal, and a half-success would make it look fresh for an hour."""
    age = cache_age(path)
    if age is not None and age < max_age_seconds:
        return False
    # Resolved at CALL time, not as a default argument: a default binds the
    # function object at import, so tests patching ``fetch_index`` still hit
    # the network (measured 2026-08-27 - a real cache file appeared mid-test).
    fetch = fetch or fetch_index
    fetch_npcs = fetch_npcs or fetch_npc_names
    try:
        names = parse_index(fetch())
    except Exception as e:  # network boundary
        logger.warning('sheetroster: could not fetch %s: %s', INDEX_URL, e)
        return False
    if not names:
        logger.warning('sheetroster: no characters parsed from %s; keeping the cache', INDEX_URL)
        return False
    try:
        npcs = fetch_npcs()
    except Exception as e:  # network boundary
        logger.warning('sheetroster: could not fetch NPCs from %s: %s', API_URL, e)
        npcs = npc_names(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'names': names, 'npcs': npcs}, indent=2), encoding='utf-8')
    logger.info('sheetroster: refreshed %s (%d characters, %d NPCs)', path, len(names), len(npcs))
    return True


def _cached_list(path: Path, key: str) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except OSError, ValueError:
        return []
    names = data.get(key) if isinstance(data, dict) else None
    return [str(n) for n in names] if isinstance(names, list) else []


def full_names(path: Path = CACHE_PATH) -> list[str]:
    """The cached index names, or [] when there is no usable cache."""
    return _cached_list(path, 'names')


def npc_names(path: Path = CACHE_PATH) -> list[str]:
    """The cached NPC names (feature 213), or [] when there are none."""
    return _cached_list(path, 'npcs')


_LATIN = re.compile(r"[A-Za-z][A-Za-z'\-]*")


def given_name(full: str) -> str:
    """The last LATIN token: ``Tsuruchi Makoto 鶴知誠`` -> ``Makoto`` (the
    sheet app lets a player append kanji to their name).

    THE ONE PLACE THE RULE LIVES (GM 2026-09-26: *"what I want to see in the
    notes and in my annotation and just everything is 'Yudai' not '勇大'"*).
    ``l7r.repl.rolls.rules.personal_name``, ``l7r.repl.sheets.PC.given`` and the
    Obsidian Portal used-name tracking in ``op.py`` all delegate here; a fifth
    copy of ``name.split()[-1]`` is a bug waiting for the next kanji."""
    latin = [t for t in full.split() if _LATIN.fullmatch(t)]
    return latin[-1] if latin else ''


def given_names(path: Path = CACHE_PATH) -> frozenset[str]:
    """Given name of each cached character and NPC (see :func:`given_name`)."""
    everyone = [*full_names(path), *npc_names(path)]
    return frozenset(g for g in (given_name(n) for n in everyone) if g)
