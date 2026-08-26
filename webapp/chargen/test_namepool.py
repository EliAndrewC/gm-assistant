"""Behavior tests for ``chargen.namepool`` - pool-backed given-name picking."""

from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from chargen import namepool

ENTRIES = [
    ('Akira', 'male'),
    ('Benjiro', 'male'),
    ('Chiyo', 'female'),
    ('Daiki', 'male'),
    ('Emiko', 'female'),
    ('Fumiko', 'female'),
]


@pytest.fixture
def pool_dir(tmp_path: Path) -> Path:
    for gender in namepool.GENDERS:
        lines = [
            json.dumps({'name': n, 'gender': g, 'format': 1, 'explanation': f'{n} means x'})
            for n, g in ENTRIES
            if g == gender
        ]
        (tmp_path / f'pool-{gender}.jsonl').write_text('\n'.join(lines) + '\n')
    return tmp_path


CASTE_ENTRIES = [
    # (name, peasant, samurai) - all female; a court name, register names, and
    # Sen: a register name also attested on a warrior-house woman (Sen-hime)
    ('Akiko', False, False),
    ('Kiku', True, False),
    ('Matsu', True, False),
    ('Sen', True, True),
]


@pytest.fixture
def caste_pool_dir(tmp_path: Path) -> Path:
    lines = [
        json.dumps(
            {
                'name': n,
                'gender': 'female',
                'format': 1,
                'explanation': 'x',
                'peasant': p,
                'samurai': s,
            }
        )
        for n, p, s in CASTE_ENTRIES
    ]
    (tmp_path / 'pool-female.jsonl').write_text('\n'.join(lines) + '\n')
    (tmp_path / 'pool-male.jsonl').write_text('')
    return tmp_path


def _picks(pool_dir: Path, n: int = 40, **kw: object) -> set[str]:
    pool = namepool.load_pool(pool_dir)
    rng = random.Random(1)
    return {namepool.pick_name('female', pool, used=(), rng=rng, **kw).name for _ in range(n)}  # type: ignore[arg-type]


def test_peasant_draws_only_peasant_flagged_names(caste_pool_dir: Path) -> None:
    assert _picks(caste_pool_dir, peasant=True) == {'Kiku', 'Matsu', 'Sen'}


def test_samurai_prefers_court_and_warrior_house_names(caste_pool_dir: Path) -> None:
    # 40 draws with two plain register names available: an even draw would
    # leak them almost surely; the preference tier holds the court name and
    # the warrior-house-attested one only.
    assert _picks(caste_pool_dir, peasant=False) == {'Akiko', 'Sen'}


def test_samurai_falls_back_to_whole_pool_when_preferred_tier_exhausted(
    caste_pool_dir: Path,
) -> None:
    pool = namepool.load_pool(caste_pool_dir)
    got = namepool.pick_name('female', pool, used=('Akiko', 'Sen'), peasant=False)
    assert got.name in {'Kiku', 'Matsu'}


def test_peasant_raises_when_peasant_tier_exhausted(caste_pool_dir: Path) -> None:
    pool = namepool.load_pool(caste_pool_dir)
    with pytest.raises(namepool.NamePoolExhausted):
        namepool.pick_name('female', pool, used=('Kiku', 'Matsu', 'Sen'), peasant=True)


def test_no_caste_draws_from_whole_pool(caste_pool_dir: Path) -> None:
    assert _picks(caste_pool_dir) == {'Akiko', 'Kiku', 'Matsu', 'Sen'}


def test_load_pool_splits_by_gender(pool_dir: Path) -> None:
    pool = namepool.load_pool(pool_dir)
    assert [e.name for e in pool['male']] == ['Akira', 'Benjiro', 'Daiki']
    assert [e.name for e in pool['female']] == ['Chiyo', 'Emiko', 'Fumiko']


def test_load_pool_is_memoized_per_directory(pool_dir: Path) -> None:
    assert namepool.load_pool(pool_dir) is namepool.load_pool(pool_dir)


def test_pick_excludes_used_and_near_used(pool_dir: Path) -> None:
    pool = namepool.load_pool(pool_dir)
    # 'Chiyoko' extends 'Chiyo' -> too similar; 'Emiko' exact.
    names = {namepool.pick_name('female', pool, {'Chiyoko', 'Emiko'}).name for _ in range(50)}
    assert names == {'Fumiko'}


def test_pick_honors_avoid_list_with_set_rule(pool_dir: Path) -> None:
    pool = namepool.load_pool(pool_dir)
    # 'Akemi' shares A with Akira; 'Toshiki' rhymes with Daiki -> only Benjiro.
    names = {
        namepool.pick_name('male', pool, (), avoid=['Akemi', 'Toshiki']).name for _ in range(50)
    }
    assert names == {'Benjiro'}


def test_pick_uses_injected_rng(pool_dir: Path) -> None:
    pool = namepool.load_pool(pool_dir)
    a = namepool.pick_name('male', pool, (), rng=random.Random(7)).name
    b = namepool.pick_name('male', pool, (), rng=random.Random(7)).name
    assert a == b


def test_pick_raises_when_exhausted(pool_dir: Path) -> None:
    pool = namepool.load_pool(pool_dir)
    with pytest.raises(namepool.NamePoolExhausted, match='no unused male name left') as exc:
        namepool.pick_name('male', pool, {'Akira', 'Benjiro', 'Daiki'})
    assert exc.value.gender == 'male'


def test_pick_unknown_gender_is_exhausted(pool_dir: Path) -> None:
    with pytest.raises(namepool.NamePoolExhausted):
        namepool.pick_name('other', namepool.load_pool(pool_dir), ())


def test_pool_dir_env_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv('L7R_NAMES_DIR', str(tmp_path))
    assert namepool.pool_dir() == tmp_path


def test_pool_dir_prefers_deploy_bundle(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv('L7R_NAMES_DIR', raising=False)
    monkeypatch.setattr(namepool, '_WEBAPP', tmp_path)
    assert namepool.pool_dir() == (tmp_path.parent / '.claude' / 'skills' / 'name').resolve()
    (tmp_path / 'skills' / 'name').mkdir(parents=True)
    assert namepool.pool_dir() == tmp_path / 'skills' / 'name'


def test_real_pool_loads_both_genders() -> None:
    pool = namepool.load_pool(namepool.pool_dir())
    assert pool['male']
    assert pool['female']
