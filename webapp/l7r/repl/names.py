"""Name and place picks for the GM's REPL.

``name()`` / ``names()`` / ``bank()`` draw from the ONE given-name pool
(``.claude/skills/name/pool-*.jsonl``) through the same engine ``/chargen``
uses (``chargen.namepool.pick_name``), so a pick excludes the campaign roster
and is set-distinct within a call. The roster comes from the campaign cache;
it is refreshed from Obsidian Portal when older than an hour and the refresh
is fail-soft (a warning, then the last cached roster).

``place()`` draws from the place-name pool (``.claude/skills/place-names``).

Each function returns a ``Pick`` - a ``str`` (so it composes) that also
carries the entry's explanation, and prints it, since at the prompt you
want to read the meaning without asking twice.
"""

from __future__ import annotations

import logging
import os
import random as _random
import threading
from collections.abc import Sequence
from pathlib import Path

from chargen import namepool, opcache, placeuse
from l7r import places as _places
from l7r.names import GeneratedName

logger = logging.getLogger(__name__)

_WEBAPP = Path(__file__).resolve().parent.parent.parent
#: Six hours (GM 2026-08-27): the REPL's roster window, wider than the skill's
#: one hour because a REPL session is a game night and the roster does not
#: move during one. A warm-up thread at REPL start refreshes both caches.
MAX_AGE = 6 * 3600.0
_refresh_lock = threading.Lock()
CACHE_STATUS: dict[str, str] = {'roster': 'not checked'}

SCALES = ('province', 'town', 'village', 'hamlet')


class Pick(str):
    """A picked name: a plain ``str`` with ``.explanation`` (the pool's
    meaning line), ``.notes`` (the authenticity notes) and ``.tags`` (gender,
    caste, provenance) attached, and ``.entry`` the pool record."""

    explanation: str
    notes: str
    tags: tuple[str, ...]
    entry: object

    def __new__(
        cls,
        name: str,
        explanation: str,
        entry: object,
        notes: str = '',
        tags: tuple[str, ...] = (),
    ) -> Pick:
        self = super().__new__(cls, name)
        # Some pool formats open with the name itself; do not print it twice.
        self.explanation = explanation.removeprefix(f'{name} - ')
        self.notes = notes
        self.tags = tags
        self.entry = entry
        return self

    def describe(self) -> str:
        """The name and its meaning, then the authenticity notes and the tags
        (GM 2026-08-27: both printed on every pick), indented under it."""
        lines = [f'{self} - {self.explanation}']
        if self.notes:
            lines.append(f'  notes: {self.notes}')
        if self.tags:
            lines.append(f'  tags: {", ".join(self.tags)}')
        return '\n'.join(lines)


def name_tags(entry: GeneratedName) -> tuple[str, ...]:
    """``male``/``female``; ``peasant`` (a commoner-register name), ``samurai``,
    or both when a peasant-flagged name is attested on warrior-house women;
    then the provenance (``historical`` / ``idiom`` / ``invented``)."""
    caste = 'samurai'
    if entry.peasant:
        caste = 'peasant + samurai' if entry.samurai else 'peasant'
    return tuple(t for t in (entry.gender, caste, entry.provenance) if t)


def places_dir() -> Path:
    env_override = os.environ.get('L7R_PLACES_DIR')
    if env_override:
        return Path(env_override)
    bundled = _WEBAPP / 'skills' / 'place-names'
    if bundled.is_dir():
        return bundled
    return (_WEBAPP.parent / '.claude' / 'skills' / 'place-names').resolve()


def warm_caches(max_age: float = MAX_AGE) -> str:
    """Refresh the OP roster (and, inside it, the character-sheet roster) if
    older than ``max_age``. Run by the REPL in a background thread at start
    so the prompt is never blocked on Obsidian Portal; a pick that arrives
    while it runs waits on the lock rather than fetching twice. Returns a
    one-line status, also kept in ``CACHE_STATUS['roster']``."""
    with _refresh_lock:
        try:
            written = opcache.refresh_if_stale(max_age)
        except Exception as e:  # OP boundary: report, never block a pick
            CACHE_STATUS['roster'] = f'refresh failed: {e}'
            return CACHE_STATUS['roster']
    age = opcache.cache_age()
    if age is None:
        CACHE_STATUS['roster'] = 'no campaign cache - every name looks free'
    else:
        CACHE_STATUS['roster'] = f'{"refreshed" if written else "fresh"} ({age / 3600:.1f} h old)'
    return CACHE_STATUS['roster']


def cache_status() -> str:
    """What the warm-up thread found (``help_l7r()`` lists this)."""
    print(CACHE_STATUS['roster'])
    return CACHE_STATUS['roster']


def used_names(refresh: bool | None = None) -> frozenset[str]:
    """Given names on the campaign roster. ``refresh``: None = refresh the
    cache if older than :data:`MAX_AGE`, True = force, False = offline read."""
    if refresh is not False:
        status = warm_caches(0.0 if refresh else MAX_AGE)
        if 'failed' in status or 'no campaign cache' in status:
            print(f'WARNING: {status}')
    return opcache.used_given_names()


def _gender(g: str | None) -> str:
    if g is None:
        return _random.choice(namepool.GENDERS)
    g = g.lower()
    if g.startswith('m'):
        return 'male'
    if g.startswith('f'):
        return 'female'
    raise ValueError(f'gender must be m/male or f/female, not {g!r}')


def names(
    gender: str | None = None,
    n: int = 1,
    peasant: bool | None = None,
    avoid: Sequence[str] = (),
    refresh: bool | None = None,
    quiet: bool = False,
) -> list[Pick]:
    """``n`` given names, mutually set-distinct and clear of the roster.
    ``gender`` = ``'m'`` / ``'f'`` / None (random per name); ``peasant`` =
    True for commoner-register names, False for samurai, None for either."""
    used = used_names(refresh)
    pool = namepool.load_pool(namepool.pool_dir())
    picks: list[Pick] = []
    for _ in range(n):
        g = _gender(gender)
        chosen = namepool.pick_name(g, pool, used, [*avoid, *picks], peasant=peasant)
        picks.append(Pick(chosen.name, chosen.explanation, chosen, chosen.notes, name_tags(chosen)))
    if not quiet:
        for p in picks:
            print(p.describe())
    return picks


def name(
    gender: str | None = None,
    peasant: bool | None = None,
    avoid: Sequence[str] = (),
    refresh: bool | None = None,
) -> Pick:
    """One given name (see :func:`names`)."""
    return names(gender, 1, peasant, avoid, refresh)[0]


def bank(n: int = 3, avoid: Sequence[str] = (), refresh: bool | None = None) -> list[Pick]:
    """``n`` male + ``n`` female names as ONE distinct set - the supporting
    cast for a backstory."""
    males = names('m', n, avoid=avoid, refresh=refresh, quiet=True)
    females = names('f', n, avoid=[*avoid, *males], refresh=False, quiet=True)
    picks = males + females
    for p in picks:
        print(p.describe())
    return picks


def place(scale: str | None = None, quiet: bool = False) -> Pick:
    """One place name. ``scale`` = province / town / village / hamlet (or a
    prefix); None picks any entry at its primary scale. A bare element
    surfacing as a village gets a random ``-mura``-style suffix."""
    pool = _places.load_places(places_dir())
    if scale is not None:
        matches = [s for s in SCALES if s.startswith(scale.lower())]
        if len(matches) != 1:
            raise ValueError(f'scale must be one of {SCALES}, not {scale!r}')
        scale = matches[0]
        pool = _places.filter_places(pool, place_type=scale)
    # Names already in use at this scale (OP tags + the chargen house config)
    # are excluded; with no scale, in use at ANY scale. Per-scale by design -
    # see chargen/placeuse.py.
    in_use = placeuse.used_place_names()
    taken = {
        placeuse.normalize(n) for s, ns in in_use.items() if scale is None or s == scale for n in ns
    }
    pool = [p for p in pool if placeuse.normalize(p.name) not in taken]
    chosen = _places.random_place(pool)
    if chosen is None:
        raise ValueError(f'no unused place names in the pool at {places_dir()}')
    shown = chosen.name
    if scale == 'village':
        shown, _ = _places.villageify(chosen)
    at = scale or chosen.place_types[0]
    pick = Pick(shown, f'{chosen.kanji}, "{chosen.meaning}" ({at})', chosen)
    if not quiet:
        print(pick.describe())
    return pick


def province_name(quiet: bool = False) -> Pick:
    """``place('province')``."""
    return place('province', quiet)


def town_name(quiet: bool = False) -> Pick:
    """``place('town')``."""
    return place('town', quiet)


def village_name(quiet: bool = False) -> Pick:
    """``place('village')``."""
    return place('village', quiet)


def hamlet_name(quiet: bool = False) -> Pick:
    """``place('hamlet')``."""
    return place('hamlet', quiet)
