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
