"""Name and place picks of the GM REPL (l7r.repl.names). The real pools are
read; the campaign roster is a fixture so no test reaches Obsidian Portal."""

import importlib
from pathlib import Path

import pytest

from l7r.names import GeneratedName
from l7r.places import Place
from l7r.repl.names import (
    Pick,
    bank,
    hamlet_name,
    name,
    names,
    place,
    places_dir,
    province_name,
    town_name,
    used_names,
    village_name,
)

# `l7r.repl.names` the MODULE is shadowed by `names` the function on the package.
mod = importlib.import_module('l7r.repl.names')

ROSTER = frozenset({'Toturi', 'Kachiko'})


def _entry(p: Pick) -> GeneratedName:
    assert isinstance(p.entry, GeneratedName)
    return p.entry


def _place(p: Pick) -> Place:
    assert isinstance(p.entry, Place)
    return p.entry


@pytest.fixture(autouse=True)
def roster(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    calls: list[float] = []
    monkeypatch.setattr(mod.opcache, 'refresh_if_stale', lambda age: calls.append(age))
    monkeypatch.setattr(mod.opcache, 'cache_age', lambda: 10.0)
    monkeypatch.setattr(mod.opcache, 'used_given_names', lambda: ROSTER)
    monkeypatch.delenv('L7R_NAMES_DIR', raising=False)
    monkeypatch.delenv('L7R_PLACES_DIR', raising=False)
    return calls


class TestUsedNames:
    def test_default_refreshes_if_stale(self, roster: list[float]) -> None:
        assert used_names() == ROSTER
        assert roster == [mod.MAX_AGE]

    def test_force_and_offline(self, roster: list[float]) -> None:
        used_names(refresh=True)
        used_names(refresh=False)
        assert roster == [0.0]

    def test_refresh_failure_warns(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        def boom(age: float) -> None:
            raise RuntimeError('no creds')

        monkeypatch.setattr(mod.opcache, 'refresh_if_stale', boom)
        used_names()
        assert 'WARNING: campaign cache refresh failed: no creds' in capsys.readouterr().out

    def test_missing_cache_warns(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(mod.opcache, 'cache_age', lambda: None)
        used_names()
        assert 'EMPTY roster' in capsys.readouterr().out


class TestNames:
    def test_pick_strips_a_leading_name(self) -> None:
        p = Pick('Kiku', 'Kiku - chrysanthemum', None)
        assert p.describe() == 'Kiku - chrysanthemum'

    def test_pick_is_a_str_with_an_explanation(self, capsys: pytest.CaptureFixture[str]) -> None:
        n = name('f')
        assert isinstance(n, Pick)
        assert isinstance(n, str)
        assert _entry(n).gender == 'female'
        assert capsys.readouterr().out == f'{n} - {n.explanation}\n'

    def test_gender_aliases_and_random(self) -> None:
        assert _entry(name('male')).gender == 'male'
        assert _entry(name('M')).gender == 'male'
        assert _entry(name('female')).gender == 'female'
        unlabeled = name()
        assert unlabeled.explanation.endswith(('(male)', '(female)'))

    def test_bad_gender(self) -> None:
        with pytest.raises(ValueError, match='gender'):
            name('x')

    def test_set_is_distinct_and_avoids(self) -> None:
        picks = names('m', 4, avoid=['Zenko'])
        assert len(picks) == 4
        initials = {p[0] for p in picks}
        assert len(initials) == 4
        assert 'Z' not in initials

    def test_peasant_filter(self) -> None:
        for _ in range(5):
            assert _entry(name('f', peasant=True)).peasant is True

    def test_bank(self, capsys: pytest.CaptureFixture[str]) -> None:
        picks = bank(2)
        assert [_entry(p).gender for p in picks] == ['male', 'male', 'female', 'female']
        assert len({p[0] for p in picks}) == 4
        assert capsys.readouterr().out.count('\n') == 4


class TestPlace:
    def test_any_scale(self, capsys: pytest.CaptureFixture[str]) -> None:
        p = place()
        assert isinstance(p, Pick)
        assert _place(p).kanji in p.explanation
        assert capsys.readouterr().out.endswith(')\n')

    def test_scale_prefix_and_villageify(self) -> None:
        v = place('vil', quiet=True)
        assert 'village' in _place(v).place_types
        assert v.explanation.endswith('(village)')
        assert v.startswith(_place(v).name)
        t = place('town', quiet=True)
        assert 'town' in _place(t).place_types
        assert t == _place(t).name

    def test_scale_aliases(self) -> None:
        for fn, scale in (
            (province_name, 'province'),
            (town_name, 'town'),
            (village_name, 'village'),
            (hamlet_name, 'hamlet'),
        ):
            p = fn(quiet=True)
            assert p.explanation.endswith(f'({scale})')
            assert scale in _place(p).place_types

    def test_bad_scale(self) -> None:
        with pytest.raises(ValueError, match='scale'):
            place('city')

    def test_empty_pool(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setenv('L7R_PLACES_DIR', str(tmp_path))
        assert places_dir() == tmp_path
        with pytest.raises(ValueError, match='no place names'):
            place()

    def test_places_dir_bundled(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setattr(mod, '_WEBAPP', tmp_path)
        assert places_dir() == (tmp_path.parent / '.claude' / 'skills' / 'place-names').resolve()
        (tmp_path / 'skills' / 'place-names').mkdir(parents=True)
        assert places_dir() == tmp_path / 'skills' / 'place-names'
