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
from collections.abc import Sequence
from pathlib import Path

from chargen import namepool, opcache
from l7r import places as _places

logger = logging.getLogger(__name__)

_WEBAPP = Path(__file__).resolve().parent.parent.parent
MAX_AGE = 3600.0

SCALES = ('province', 'town', 'village', 'hamlet')


class Pick(str):
    """A picked name: a plain ``str`` with ``.explanation`` (the pool's
    meaning line) and ``.entry`` (the pool record) attached."""

    explanation: str
    entry: object

    def __new__(cls, name: str, explanation: str, entry: object) -> Pick:
        self = super().__new__(cls, name)
        # Some pool formats open with the name itself; do not print it twice.
        self.explanation = explanation.removeprefix(f'{name} - ')
        self.entry = entry
        return self

    def describe(self) -> str:
        return f'{self} - {self.explanation}'


def places_dir() -> Path:
    env_override = os.environ.get('L7R_PLACES_DIR')
    if env_override:
        return Path(env_override)
    bundled = _WEBAPP / 'skills' / 'place-names'
    if bundled.is_dir():
        return bundled
    return (_WEBAPP.parent / '.claude' / 'skills' / 'place-names').resolve()


def used_names(refresh: bool | None = None) -> frozenset[str]:
    """Given names on the campaign roster. ``refresh``: None = refresh the
    cache if older than an hour, True = force, False = offline read."""
    if refresh is not False:
        try:
            opcache.refresh_if_stale(0.0 if refresh else MAX_AGE)
        except Exception as e:  # OP boundary: warn, never block a pick
            print(f'WARNING: campaign cache refresh failed: {e}')
    if opcache.cache_age() is None:
        print('WARNING: no campaign cache - picking against an EMPTY roster')
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
        tag = '' if gender else f' ({chosen.gender})'
        picks.append(Pick(chosen.name, f'{chosen.explanation}{tag}', chosen))
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
    chosen = _places.random_place(pool)
    if chosen is None:
        raise ValueError(f'no place names in the pool at {places_dir()}')
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
