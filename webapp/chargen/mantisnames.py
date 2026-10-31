"""Mantis Clan given names (feature 232).

The GM (2026-10-31): Mantis names are based on Indonesian names and are heard by
Rokugani as gaijin names. Any given Mantis has one of four naming cases, at
odds the GM set and ``[mantis_names]`` in the config can change:

- ``rokugani`` (20%): simply a Rokugani name, from the ordinary pool;
- ``alias`` (10%): a Mantis name, but goes by an unrelated Rokugani name to
  blend in;
- ``rokuganized`` (10%): goes by the Rokugani form of their Mantis name
  (Amari for Amar, since "mar" is not a Rokugani syllable);
- ``mantis`` (60%): a plain Mantis name.

The name a character GOES BY is the one in their full name and on their record,
and in both "goes by" cases the meaning line also gives the real Mantis name
(spec-fidelity round 1: a nickname to blend in, not a secret identity). The list
is ``pool-mantis.jsonl`` beside the Rokugani pool; this module is the single
implementation behind both the chargen engine and the ``/name`` picker.
"""

from __future__ import annotations

import json
import random as _random
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from chargen.similarity import is_too_similar, set_conflict

CASES = ('rokugani', 'alias', 'rokuganized', 'mantis')
DEFAULT_ODDS = {'rokugani': 20, 'alias': 10, 'rokuganized': 10, 'mantis': 60}
POOL_FILE = 'pool-mantis.jsonl'

_VOWELS = 'aeiou'
# Consonant + vowel morae of Hepburn romaji, minus the gaps the language does
# not have (si/ti/tu/di/du/hu/zi are written shi/chi/tsu/ji/zu/fu/ji; y and w
# take only some vowels).
_MISSING = {
    'si',
    'ti',
    'tu',
    'di',
    'du',
    'hu',
    'zi',
    'yi',
    'ye',
    'wi',
    'wu',
    'we',
    'wo',
}
_CV = {c + v for c in 'kgsztdnhbpmyrw' for v in _VOWELS} - _MISSING
_SPECIAL = {'shi', 'chi', 'tsu', 'ji', 'fu'}
_YOUON = {c + 'y' + v for c in 'kgnhbpmr' for v in 'auo'} | {
    p + v for p in ('sh', 'ch', 'j') for v in 'auo'
}
MORAE = frozenset(_CV | _SPECIAL | _YOUON | set(_VOWELS))


def is_rokugani(name: str) -> bool:
    """True when ``name`` is spelled entirely in Rokugani (Japanese) syllables:
    morae of Hepburn romaji plus a syllabic ``n`` that is not followed by a
    vowel or ``y`` (a following vowel would make it the onset of the next mora).
    Greedy longest-first parsing is unambiguous for this inventory."""
    s = name.lower()
    i = 0
    while i < len(s):
        for size in (3, 2, 1):
            if s[i : i + size] in MORAE:
                i += size
                break
        else:
            if s[i] == 'n' and (i + 1 == len(s) or s[i + 1] not in _VOWELS + 'y'):
                i += 1
                continue
            return False
    return bool(s)


@dataclass(frozen=True, slots=True)
class MantisName:
    """One entry of the Mantis name list."""

    name: str
    gender: str  # 'male', 'female' or 'neutral'
    meaning: str
    source: str
    rokuganized: str
    gm: bool

    def fits(self, gender: str) -> bool:
        return self.gender in (gender, 'neutral')


@lru_cache(maxsize=8)
def load_mantis_pool(directory: Path) -> tuple[MantisName, ...]:
    """The Mantis list from ``directory``; empty when the file is absent."""
    path = directory / POOL_FILE
    if not path.exists():
        return ()
    lines = path.read_text(encoding='utf-8').splitlines()
    return tuple(MantisName(**json.loads(line)) for line in lines if line.strip())


def odds(config: Mapping[str, object] | None) -> dict[str, int]:
    """The four odds from ``[mantis_names]``, each falling back to the GM's
    default when absent."""
    section = (config or {}).get('mantis_names') or {}
    assert isinstance(section, Mapping)
    return {case: int(section.get(case, DEFAULT_ODDS[case])) for case in CASES}


def roll_case(chances: Mapping[str, int], rng: _random.Random | None = None) -> str:
    """One naming case, weighted by ``chances``."""
    chooser = rng if rng is not None else _random
    return chooser.choices(CASES, weights=[chances[c] for c in CASES])[0]


@dataclass(frozen=True, slots=True)
class MantisPick:
    """The outcome of naming a Mantis."""

    goes_by: str  # the given name in their full name and on their record
    meaning: str  # the name-meaning line
    case: str
    mantis_name: str  # the real Mantis name; '' in the rokugani case


def _pronoun(gender: str) -> str:
    return 'he' if gender == 'male' else 'she'


def mantis_meaning(entry: MantisName) -> str:
    return (
        f'{entry.name} is a Mantis name from the Islands of Spice and Silk, which '
        f'Rokugani hear as a gaijin name; it means "{entry.meaning}".'
    )


def rokuganized_meaning(entry: MantisName) -> str:
    return (
        f'{entry.rokuganized} is the Rokugani form of the Mantis name {entry.name}, '
        f'which means "{entry.meaning}".'
    )


def alias_meaning(rokugani_name: str, explanation: str, entry: MantisName, gender: str) -> str:
    who = _pronoun(gender)
    return (
        f'{explanation} {rokugani_name} is the name {who} goes by among Rokugani; '
        f'{"his" if who == "he" else "her"} Mantis name is {entry.name}, which '
        f'means "{entry.meaning}".'
    )


def _eligible(
    pool: Sequence[MantisName],
    gender: str,
    shown: Callable[[MantisName], str],
    used: Iterable[str],
    avoid: Sequence[str],
) -> list[MantisName]:
    used_list = sorted(used)
    return [
        e
        for e in pool
        if e.fits(gender)
        and not is_too_similar(shown(e), used_list)
        and not any(set_conflict(shown(e), a) for a in avoid)
    ]


def pick_mantis(
    gender: str,
    pool: Sequence[MantisName],
    rokugani: Callable[[], tuple[str, str]],
    used: Iterable[str],
    avoid: Sequence[str] = (),
    chances: Mapping[str, int] = DEFAULT_ODDS,
    rng: _random.Random | None = None,
) -> MantisPick:
    """Name one Mantis of ``gender``.

    ``rokugani`` picks an ordinary Rokugani name as ``(name, explanation)``
    under the caller's own exclusion rules; it serves the rokugani and alias
    cases, and is the fallback when a Mantis case has no eligible entry (FR-007).
    Exclusion (the campaign roster ``used``, the set's ``avoid``) applies to the
    name the character goes by - the one the players hear.
    """
    chooser = rng if rng is not None else _random
    used = frozenset(used)
    case = roll_case(chances, rng)
    if case == 'mantis':
        valid = _eligible(pool, gender, lambda e: e.name, used, avoid)
        if valid:
            entry = chooser.choice(valid)
            return MantisPick(entry.name, mantis_meaning(entry), case, entry.name)
    elif case == 'rokuganized':
        changed = [e for e in pool if e.rokuganized != e.name]
        valid = _eligible(changed, gender, lambda e: e.rokuganized, used, avoid)
        if valid:
            entry = chooser.choice(valid)
            return MantisPick(entry.rokuganized, rokuganized_meaning(entry), case, entry.name)
    elif case == 'alias':
        # The real Mantis name is never spoken at the table, so only the alias
        # is held to the exclusion rules.
        mantis_pool = [e for e in pool if e.fits(gender)]
        if mantis_pool:
            entry = chooser.choice(mantis_pool)
            name, explanation = rokugani()
            return MantisPick(
                name, alias_meaning(name, explanation, entry, gender), case, entry.name
            )
    name, explanation = rokugani()
    return MantisPick(name, explanation, 'rokugani', '')
