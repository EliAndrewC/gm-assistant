"""Mantis Clan names (feature 232): the list, the syllable check, the four
naming cases at the GM's odds, and their exclusion and fallback rules."""

from __future__ import annotations

import json
import random
from collections import Counter
from collections.abc import Callable
from pathlib import Path

import pytest

from chargen import mantisnames as m
from chargen.namepool import pool_dir

POOL = m.load_mantis_pool(pool_dir())

# The GM's examples, verbatim glosses (2026-10-31).
GM_EXAMPLES = {
    'Irehemu': ('male', 'father of multitudes'),
    'Irahim': ('male', 'father of multitudes (a variant of Irehemu)'),
    'Kauri': ('male', 'tree'),
    'Mohanda': ('male', 'servant of the gods'),
    'Jamiru': ('male', "beautiful (a man's name)"),
    'Surama': ('male', 'man of peace'),
    'Noru': ('male', 'light'),
    'Muhama': ('male', 'praised, commendable'),
    'Putera': ('male', 'prince'),
    'Anaru': ('male', 'fisherman'),
    'Marama': ('female', 'moon, the moon goddess'),
    'Fatama': ('female', 'daughter of the prophet'),
    'Amar': ('neutral', 'immortal, eternal'),
    'Mariyamu': ('female', 'wished-for child'),
    'Jamiko': ('female', "beautiful (a woman's name)"),
    'Latifu': ('female', 'gentle and kind'),
}


def rok(
    name: str = 'Kenji', explanation: str = 'Kenji means "healthy second son".'
) -> Callable[[], tuple[str, str]]:
    return lambda: (name, explanation)


# --- syllables -------------------------------------------------------------


@pytest.mark.parametrize(
    'name', ['Amari', 'Irehemu', 'Shinta', 'Chahaya', 'Guntoru', 'Intan', 'Hasan', 'Kyoma', 'Jun']
)
def test_rokugani_names_parse(name: str) -> None:
    assert m.is_rokugani(name)


@pytest.mark.parametrize(
    'name', ['Amar', 'Latifu', 'Fatama', 'Dewi', 'Budi', 'Agus', 'Kartika', 'Embun', '', 'Wo']
)
def test_gaijin_names_do_not_parse(name: str) -> None:
    assert not m.is_rokugani(name)


def test_n_before_a_vowel_is_not_syllabic() -> None:
    assert m.is_rokugani('Kana')
    assert not m.is_rokugani('Knaa')


# --- the list --------------------------------------------------------------


def test_every_gm_example_is_present_with_the_gm_gloss() -> None:
    by_name = {e.name: e for e in POOL}
    for name, (gender, meaning) in GM_EXAMPLES.items():
        entry = by_name[name]
        assert (entry.gender, entry.meaning, entry.gm) == (gender, meaning, True)
    assert sum(e.gm for e in POOL) == len(GM_EXAMPLES)


def test_every_entry_has_a_meaning_and_a_source() -> None:
    assert all(e.meaning for e in POOL)
    assert all(e.source for e in POOL)


def test_the_list_is_big_enough_for_both_genders() -> None:
    assert sum(e.fits('male') for e in POOL) >= 40
    assert sum(e.fits('female') for e in POOL) >= 40


def test_every_rokuganized_form_is_rokugani_and_differs_only_when_it_must() -> None:
    for e in POOL:
        assert m.is_rokugani(e.rokuganized), e
        assert (e.rokuganized == e.name) == m.is_rokugani(e.name), e
    assert {e.name: e.rokuganized for e in POOL}['Amar'] == 'Amari'


def test_no_two_list_names_are_near_duplicates() -> None:
    from chargen.similarity import is_too_similar

    names = [e.name for e in POOL]
    for i, name in enumerate(names):
        assert not is_too_similar(name, names[:i] + names[i + 1 :]), name


def test_missing_pool_file_is_empty(tmp_path: Path) -> None:
    assert m.load_mantis_pool(tmp_path) == ()


def test_pool_skips_blank_lines(tmp_path: Path) -> None:
    row = dict(name='Noru', gender='male', meaning='light', source='s', rokuganized='Noru', gm=True)
    (tmp_path / m.POOL_FILE).write_text(json.dumps(row) + '\n\n')
    assert [e.name for e in m.load_mantis_pool(tmp_path)] == ['Noru']


# --- odds ------------------------------------------------------------------


def test_odds_default_to_the_gm_numbers() -> None:
    gm = {'rokugani': 20, 'alias': 10, 'rokuganized': 10, 'mantis': 60}
    assert m.odds(None) == m.odds({}) == gm


def test_odds_read_the_config_section() -> None:
    got = m.odds({'mantis_names': {'rokugani': '0', 'mantis': 5}})
    assert got == {'rokugani': 0, 'alias': 10, 'rokuganized': 10, 'mantis': 5}


def test_case_rates_match_the_odds_within_two_points() -> None:
    rng = random.Random(232)
    n = 10_000
    counts = Counter(
        m.pick_mantis('female', POOL, rok(), (), (), m.DEFAULT_ODDS, rng).case for _ in range(n)
    )
    for case, weight in m.DEFAULT_ODDS.items():
        assert abs(counts[case] / n - weight / 100) < 0.02, (case, counts)


# --- the four cases --------------------------------------------------------


def only(case: str) -> dict[str, int]:
    return {c: int(c == case) for c in m.CASES}


def test_mantis_case() -> None:
    pick = m.pick_mantis('male', POOL, rok(), (), (), only('mantis'))
    entry = {e.name: e for e in POOL}[pick.goes_by]
    assert entry.fits('male')
    assert pick.mantis_name == entry.name
    assert f'"{entry.meaning}"' in pick.meaning
    assert 'gaijin' in pick.meaning


def test_rokuganized_case_goes_by_a_changed_form() -> None:
    for _ in range(50):
        pick = m.pick_mantis('female', POOL, rok(), (), (), only('rokuganized'))
        assert pick.goes_by != pick.mantis_name
        assert m.is_rokugani(pick.goes_by)
        assert pick.meaning.startswith(f'{pick.goes_by} is the Rokugani form of the Mantis name')


def test_alias_case_names_both() -> None:
    kiku = rok('Kiku', 'Kiku means "chrysanthemum".')
    pick = m.pick_mantis('female', POOL, kiku, (), (), only('alias'))
    assert pick.goes_by == 'Kiku'
    assert pick.case == 'alias'
    assert pick.meaning.startswith('Kiku means "chrysanthemum". Kiku is the name she goes by')
    assert f'her Mantis name is {pick.mantis_name}' in pick.meaning
    male = m.pick_mantis('male', POOL, rok(), (), (), only('alias'))
    assert 'he goes by' in male.meaning
    assert 'his Mantis name' in male.meaning


def test_rokugani_case() -> None:
    pick = m.pick_mantis('male', POOL, rok(), (), (), only('rokugani'))
    assert pick == m.MantisPick('Kenji', 'Kenji means "healthy second son".', 'rokugani', '')


def test_neutral_names_serve_both_genders() -> None:
    amar = [e for e in POOL if e.name == 'Amar']
    for gender in ('male', 'female'):
        assert m.pick_mantis(gender, amar, rok(), (), (), only('mantis')).goes_by == 'Amar'


def test_exclusion_applies_to_the_name_gone_by() -> None:
    amar = [e for e in POOL if e.name == 'Amar']
    assert m.pick_mantis('male', amar, rok(), ['Amari'], (), only('rokuganized')).case == 'rokugani'
    assert m.pick_mantis('male', amar, rok(), (), ['Amari'], only('rokuganized')).case == 'rokugani'
    assert m.pick_mantis('male', amar, rok(), ['Amar'], (), only('mantis')).case == 'rokugani'
    # the alias case's real name is never spoken at the table, so it is not excluded
    assert m.pick_mantis('male', amar, rok(), ['Amar'], (), only('alias')).mantis_name == 'Amar'


@pytest.mark.parametrize('case', ['mantis', 'rokuganized', 'alias'])
def test_empty_pool_falls_back_to_rokugani(case: str) -> None:
    assert m.pick_mantis('male', (), rok(), (), (), only(case)).case == 'rokugani'


def test_default_rng_path() -> None:
    assert m.roll_case(only('alias')) == 'alias'
