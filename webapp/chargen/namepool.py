"""Given-name picking for the chargen engine (feature 200).

The ``/name`` skill's pool (``pool-male.jsonl`` / ``pool-female.jsonl``) is the
SINGLE source of given names for the skill, the ``/names`` page and the engine
(FR-005). A pick is a pure function of the pool, the used-name set and an avoid
list - never a network call - so the engine stays testable offline; refreshing
the used-name cache against Obsidian Portal is the caller's job (see
``opcache.refresh_if_stale``).
"""

from __future__ import annotations

import os
import random as _random
from collections.abc import Iterable, Sequence
from functools import lru_cache
from pathlib import Path

from chargen.similarity import is_too_similar, set_conflict
from l7r.names import GeneratedName, load_names

GENDERS = ('male', 'female')

_WEBAPP = Path(__file__).resolve().parent.parent


class NamePoolExhausted(RuntimeError):
    """No pool name satisfies the exclusions for the requested gender (FR-011)."""

    def __init__(self, gender: str, n_pool: int, n_used: int, n_avoid: int) -> None:
        super().__init__(
            f'no unused {gender} name left: pool={n_pool}, used={n_used}, avoid={n_avoid}'
        )
        self.gender = gender


def pool_dir() -> Path:
    """Where the pool files live: ``L7R_NAMES_DIR`` if set; the deploy bundle
    ``webapp/skills/name`` if present; else the skill dir in the repo."""
    env_override = os.environ.get('L7R_NAMES_DIR')
    if env_override:
        return Path(env_override)
    bundled = _WEBAPP / 'skills' / 'name'
    if bundled.is_dir():
        return bundled
    return (_WEBAPP.parent / '.claude' / 'skills' / 'name').resolve()


@lru_cache(maxsize=8)
def load_pool(directory: Path) -> dict[str, tuple[GeneratedName, ...]]:
    """Pool entries by gender, memoized per directory (the engine constructs
    hundreds of characters in a test run; the pool is read once)."""
    by_gender: dict[str, list[GeneratedName]] = {g: [] for g in GENDERS}
    for entry in load_names(directory):
        if entry.gender in by_gender:
            by_gender[entry.gender].append(entry)
    return {g: tuple(entries) for g, entries in by_gender.items()}


@lru_cache(maxsize=32)
def roster_clean(
    pool: tuple[GeneratedName, ...], used: frozenset[str]
) -> tuple[GeneratedName, ...]:
    """Pool entries not too similar to any used name (the loose rule).

    Memoized on (pool, roster): the check is 200 pool names x ~120 roster names
    of edit distance, ~50 ms, and the engine's tests roll thousands of
    characters against one unchanging roster. Unmemoized, the webapp's 3 s test
    suite took 686 s (measured 2026-08-25, feature 200)."""
    used_list = sorted(used)
    return tuple(e for e in pool if not is_too_similar(e.name, used_list))


def candidates(
    pool: Sequence[GeneratedName], used: Iterable[str], avoid: Sequence[str]
) -> list[GeneratedName]:
    """Pool entries that are neither too similar to a used name (loose rule)
    nor in set-conflict with an avoided name (strict rule)."""
    clean = roster_clean(tuple(pool), frozenset(used))
    return [e for e in clean if not any(set_conflict(e.name, a) for a in avoid)]


def pick_name(
    gender: str,
    pool: dict[str, tuple[GeneratedName, ...]],
    used: Iterable[str],
    avoid: Sequence[str] = (),
    rng: _random.Random | None = None,
    peasant: bool | None = None,
) -> GeneratedName:
    """One random unused, non-conflicting name of ``gender``; raises
    :class:`NamePoolExhausted` rather than looping when none is left.

    ``peasant`` is the caste of the character being named (GM 2026-08-26):

    - ``True`` - a peasant draws ONLY from ``peasant``-flagged entries. The
      flag means "suitable for a commoner" (short kana register names,
      everyday -emon/-bei/-suke names); the two-kanji samurai formal name
      (nanori) came with genpuku and a lord, so a farmer called Hidetsuna is
      wrong in the way a farmer wearing a daisho is wrong.
    - ``False`` - a samurai PREFERS the non-peasant entries (plus the
      peasant-flagged names carrying ``samurai: true`` - two-mora names
      attested on warrior-house women such as Sen-hime or Hosokawa Tama) and
      falls back to the whole pool only when the strict set/roster rules
      exhaust them. Not
      an even draw from both: 81% of the female pool is peasant-flagged, so an
      even draw would name most samurai women after village registers. No
      sumptuary rule ever reserved given names for the nobility (surnames,
      dress and swords, yes), so the fallback is historically honest - Kiku
      could be a samurai's daughter - and the preference is what keeps the
      samurai-style stock from being spent on peasants.
    - ``None`` - no caste known: the whole pool.
    """
    used_set = frozenset(used)
    everyone = pool.get(gender, ())
    if peasant is True:
        tiers: list[tuple[GeneratedName, ...]] = [tuple(e for e in everyone if e.peasant)]
    elif peasant is False:
        tiers = [tuple(e for e in everyone if not e.peasant or e.samurai), everyone]
    else:
        tiers = [everyone]
    for tier in tiers:
        valid = candidates(tier, used_set, avoid)
        if valid:
            chooser = rng if rng is not None else _random
            return chooser.choice(valid)
    raise NamePoolExhausted(gender, len(everyone), len(used_set), len(avoid))
