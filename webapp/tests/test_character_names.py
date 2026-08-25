"""The chargen engine names characters from the /name skill pool with the
campaign roster excluded and set-distinctness applied INSIDE the engine
(feature 200) - so /chargen rolls a correctly named character in one call."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import l7r.app  # noqa: F401  -- force l7r to load first (chargen<->l7r circular import)
from chargen import constants as c
from chargen import namepool, opcache
from chargen.character import Monk, Peasant, Samurai
from chargen.similarity import set_conflict

_Samurai: Any = Samurai
_Peasant: Any = Peasant
_Monk: Any = Monk


@pytest.fixture
def roster(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """A campaign cache holding one live NPC per gender that is ALSO in the pool."""
    p = tmp_path / 'characters.json'
    opcache.save_cache(
        {'1': {'name': 'Hida no Reiji Isao'}, '2': {'name': 'Hida no Reiji Chiyoko'}}, p
    )
    monkeypatch.setattr(opcache, '_CACHE_PATH', p)
    monkeypatch.setattr(opcache.used_given_names, '__defaults__', (p,))
    return p


def test_pinned_gender_is_honored_on_the_first_roll(roster: Path) -> None:
    assert all(_Samurai(base_rank=3, gender='female').gender == 'female' for _ in range(40))
    assert all(_Peasant(gender='male').gender == 'male' for _ in range(40))
    assert all(_Monk(base_rank=2, gender='female').gender == 'female' for _ in range(40))


def test_roster_names_are_never_rolled(roster: Path) -> None:
    pool = namepool.load_pool(namepool.pool_dir())
    assert {'Isao', 'Chiyoko'} <= {e.name for g in pool.values() for e in g}
    rolled = {_Samurai(base_rank=3).personal_name for _ in range(300)}
    assert not rolled & {'Isao', 'Chiyoko'}


def test_in_process_used_names_are_excluded_too(
    roster: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(c, 'USED_NAMES', {'Masahiro'})
    assert 'Masahiro' not in {
        _Samurai(base_rank=3, gender='male').personal_name for _ in range(200)
    }


def test_avoid_list_keeps_a_set_mutually_distinct(roster: Path) -> None:
    for _ in range(30):
        names: list[str] = []
        for _i in range(3):
            names.append(_Samurai(base_rank=3, avoid=names).personal_name)
        for i, a in enumerate(names):
            for b in names[i + 1 :]:
                assert not set_conflict(a, b), names


def test_exhausted_pool_raises_instead_of_looping(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / 'pool-male.jsonl').write_text(
        json.dumps({'name': 'Akira', 'gender': 'male', 'format': 1, 'explanation': 'x'}) + '\n'
    )
    (tmp_path / 'pool-female.jsonl').write_text('')
    monkeypatch.setenv('L7R_NAMES_DIR', str(tmp_path))
    monkeypatch.setattr(c, 'USED_NAMES', {'Akira'})
    with pytest.raises(namepool.NamePoolExhausted):
        _Peasant(gender='male')


def test_name_meaning_comes_from_the_pool_explanation(roster: Path) -> None:
    s = _Samurai(base_rank=3)
    pool = namepool.load_pool(namepool.pool_dir())
    by_name = {e.name: e.explanation for e in pool[s.gender]}
    assert s.name_meaning == by_name[s.personal_name]
