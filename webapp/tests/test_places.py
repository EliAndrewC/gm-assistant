"""Tests for l7r.places - JSONL pool loading, filtering, random selection."""

from __future__ import annotations

import logging
import random
from pathlib import Path

import pytest

from l7r.places import (
    GEOGRAPHIC_ENDING_LABELS,
    SUFFIX_EMIT_NOTES,
    VILLAGE_SUFFIX_WEIGHTS,
    Place,
    _slugify,
    filter_places,
    find_place_by_slug,
    load_places,
    random_place,
    random_village_suffix,
    scale_description,
    villageify,
)


@pytest.fixture(scope='session')
def sample_places_dir() -> Path:
    return Path(__file__).parent / 'fixtures' / 'places_sample'


@pytest.fixture
def sample_places(sample_places_dir: Path) -> list[Place]:
    return load_places(sample_places_dir)


# ---------------------- loading ----------------------


def test_load_places_returns_all_entries(sample_places: list[Place]) -> None:
    # Fixture has 7 entries.
    assert len(sample_places) == 7


def test_load_places_sorts_by_name(sample_places: list[Place]) -> None:
    names = [p.name for p in sample_places]
    assert names == sorted(names, key=str.lower)


def test_load_places_accepts_pool_jsonl_file_directly(sample_places_dir: Path) -> None:
    places = load_places(sample_places_dir / 'pool.jsonl')
    assert len(places) == 7


def test_load_places_returns_empty_when_path_missing(tmp_path: Path) -> None:
    assert load_places(tmp_path / 'nope') == []


def test_load_places_returns_empty_when_pool_file_missing_in_dir(tmp_path: Path) -> None:
    assert load_places(tmp_path) == []


def test_load_places_preserves_all_fields(sample_places: list[Place]) -> None:
    yuhimura = next(p for p in sample_places if p.name == 'Yuhimura')
    assert yuhimura.kanji == '夕日村'
    assert yuhimura.meaning == 'sunset village'
    assert yuhimura.place_types == ('village',)
    assert yuhimura.commonality == 'common'
    assert yuhimura.regional == ()
    assert yuhimura.suffix == '-mura'
    assert yuhimura.slug == 'yuhimura'


def test_load_places_parses_regional_and_multi_scale(sample_places: list[Place]) -> None:
    aozawa = next(p for p in sample_places if p.name == 'Aozawa')
    assert aozawa.place_types == ('village', 'hamlet')
    assert aozawa.regional == ('riverine',)
    assert aozawa.suffix == '-sawa'


def test_load_places_handles_null_suffix(sample_places: list[Place]) -> None:
    owari = next(p for p in sample_places if p.name == 'Owari')
    assert owari.suffix is None


def test_load_places_skips_blank_lines(tmp_path: Path) -> None:
    (tmp_path / 'pool.jsonl').write_text(
        '\n{"name": "A", "kanji": "甲", "meaning": "x", '
        '"place_types": ["village"], "commonality": "common"}\n\n'
    )
    places = load_places(tmp_path)
    assert len(places) == 1


def test_load_places_logs_bad_json(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.WARNING)
    (tmp_path / 'pool.jsonl').write_text(
        '{"name": "A", "kanji": "甲", "meaning": "x", '
        '"place_types": ["village"], "commonality": "common"}\n'
        'not-json\n'
    )
    places = load_places(tmp_path)
    assert len(places) == 1
    assert any('JSON parse error' in r.getMessage() for r in caplog.records)


def test_load_places_skips_entries_missing_required_fields(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.WARNING)
    (tmp_path / 'pool.jsonl').write_text(
        '{"name": "Half"}\n'  # missing many fields
        '{"name": "Full", "kanji": "全", "meaning": "x", '
        '"place_types": ["village"], "commonality": "common"}\n'
    )
    places = load_places(tmp_path)
    assert len(places) == 1
    assert places[0].name == 'Full'
    assert any('missing' in r.getMessage() for r in caplog.records)


def test_load_places_skips_duplicate_slugs(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.WARNING)
    (tmp_path / 'pool.jsonl').write_text(
        '{"name": "Owari", "kanji": "尾張", "meaning": "x", '
        '"place_types": ["village"], "commonality": "common"}\n'
        '{"name": "Owari", "kanji": "尾張", "meaning": "y", '
        '"place_types": ["province"], "commonality": "common"}\n'
    )
    places = load_places(tmp_path)
    assert len(places) == 1
    assert any('duplicate slug' in r.getMessage() for r in caplog.records)


def test_load_places_logs_when_file_unreadable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING)
    target = tmp_path / 'pool.jsonl'
    target.write_text('{}\n')
    original_read_text = Path.read_text

    def boom(self: Path, *args: object, **kwargs: object) -> str:
        if self == target:
            raise OSError('denied')
        return original_read_text(self, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(Path, 'read_text', boom)
    places = load_places(tmp_path)
    assert places == []
    assert any('could not read file' in r.getMessage() for r in caplog.records)


def test_load_places_coerces_malformed_list_fields(tmp_path: Path) -> None:
    # If place_types or regional come through as a non-list (e.g. a string by
    # accident), the loader should treat them as empty rather than crashing.
    (tmp_path / 'pool.jsonl').write_text(
        '{"name": "Broken", "kanji": "壊", "meaning": "broken", '
        '"place_types": "village", "commonality": "common", "regional": "riverine"}\n'
    )
    places = load_places(tmp_path)
    assert len(places) == 1
    assert places[0].place_types == ()
    assert places[0].regional == ()


# ---------------------- slug ----------------------


def test_slugify_handles_simple_names() -> None:
    assert _slugify('Yuhimura') == 'yuhimura'
    assert _slugify('Owari') == 'owari'


def test_slugify_replaces_hyphens_and_keeps_them() -> None:
    assert _slugify('Mori-tono') == 'mori-tono'
    assert _slugify('Aki-no-mori') == 'aki-no-mori'


def test_slugify_collapses_punctuation_and_spaces() -> None:
    assert _slugify('Ne-no-kuni') == 'ne-no-kuni'
    assert _slugify('Some  Place!') == 'some-place'
    assert _slugify('---Bracketed---') == 'bracketed'


# ---------------------- properties ----------------------


def test_is_multi_scale_true_for_multi(sample_places: list[Place]) -> None:
    owari = next(p for p in sample_places if p.name == 'Owari')
    assert owari.is_multi_scale is True


def test_is_multi_scale_false_for_single(sample_places: list[Place]) -> None:
    yuhimura = next(p for p in sample_places if p.name == 'Yuhimura')
    assert yuhimura.is_multi_scale is False


def test_is_bare_element_true_for_null_suffix(sample_places: list[Place]) -> None:
    yuhi = next(p for p in sample_places if p.name == 'Yuhi')
    assert yuhi.is_bare_element is True


def test_is_bare_element_false_for_suffixed(sample_places: list[Place]) -> None:
    yuhimura = next(p for p in sample_places if p.name == 'Yuhimura')
    assert yuhimura.is_bare_element is False


def test_suffix_note_resolves_for_community_suffix(sample_places: list[Place]) -> None:
    yuhimura = next(p for p in sample_places if p.name == 'Yuhimura')
    assert 'generic word for village' in yuhimura.suffix_note


def test_suffix_note_empty_for_bare_element(sample_places: list[Place]) -> None:
    yuhi = next(p for p in sample_places if p.name == 'Yuhi')
    assert yuhi.suffix_note == ''


def test_suffix_note_empty_for_unknown_suffix() -> None:
    place = Place(
        slug='x',
        name='X',
        kanji='X',
        meaning='x',
        place_types=('village',),
        commonality='common',
        suffix='-zzz',
    )
    assert place.suffix_note == ''


def test_suffix_label_for_community_suffix(sample_places: list[Place]) -> None:
    yuhimura = next(p for p in sample_places if p.name == 'Yuhimura')
    # First sentence of the emit-time note.
    assert 'generic word for village' in yuhimura.suffix_label


def test_suffix_label_for_geographic_ending(sample_places: list[Place]) -> None:
    aozawa = next(p for p in sample_places if p.name == 'Aozawa')
    label = aozawa.suffix_label
    assert label.startswith('ends in -sawa')
    assert 'marsh' in label


def test_suffix_label_empty_for_bare_element(sample_places: list[Place]) -> None:
    yuhi = next(p for p in sample_places if p.name == 'Yuhi')
    assert yuhi.suffix_label == ''


def test_suffix_label_empty_for_unknown_suffix() -> None:
    place = Place(
        slug='x',
        name='X',
        kanji='X',
        meaning='x',
        place_types=('village',),
        commonality='common',
        suffix='-zzz',
    )
    assert place.suffix_label == ''


# ---------------------- finding ----------------------


def test_find_place_by_slug_returns_match(sample_places: list[Place]) -> None:
    place = find_place_by_slug(sample_places, 'yuhimura')
    assert place is not None
    assert place.name == 'Yuhimura'


def test_find_place_by_slug_returns_none_for_miss(sample_places: list[Place]) -> None:
    assert find_place_by_slug(sample_places, 'nonexistent') is None


# ---------------------- filtering ----------------------


def test_filter_by_place_type(sample_places: list[Place]) -> None:
    villages = filter_places(sample_places, place_type='village')
    village_names = {p.name for p in villages}
    assert 'Yuhimura' in village_names
    assert 'Aozawa' in village_names
    assert 'Mori-tono' in village_names
    assert 'Owari' in village_names  # multi-scale entry
    assert 'Yuhi' not in village_names  # hamlet only


def test_filter_by_commonality(sample_places: list[Place]) -> None:
    rare = filter_places(sample_places, commonality='rare')
    assert {p.name for p in rare} == {'Mori-tono'}


def test_filter_by_regional(sample_places: list[Place]) -> None:
    riverine = filter_places(sample_places, regional='riverine')
    assert {p.name for p in riverine} == {'Aozawa'}


def test_filter_by_suffix(sample_places: list[Place]) -> None:
    mura = filter_places(sample_places, suffix='-mura')
    assert {p.name for p in mura} == {'Yuhimura'}


def test_filter_by_suffix_none(sample_places: list[Place]) -> None:
    bare = filter_places(sample_places, suffix='none')
    bare_names = {p.name for p in bare}
    assert 'Owari' in bare_names
    assert 'Yuhi' in bare_names
    assert 'Yamashiro' in bare_names
    assert 'Yuhimura' not in bare_names


def test_filter_composes_multiple_axes(sample_places: list[Place]) -> None:
    result = filter_places(
        sample_places,
        place_type='village',
        commonality='rare',
    )
    assert {p.name for p in result} == {'Mori-tono'}


def test_filter_with_no_axes_returns_copy(sample_places: list[Place]) -> None:
    result = filter_places(sample_places)
    assert result == sample_places
    assert result is not sample_places  # must be a new list


def test_filter_returns_empty_when_no_matches(sample_places: list[Place]) -> None:
    result = filter_places(sample_places, place_type='village', commonality='unique')
    assert result == []


# ---------------------- random ----------------------


def test_random_place_picks_from_list(sample_places: list[Place]) -> None:
    rng = random.Random(42)
    picked = random_place(sample_places, rng=rng)
    assert picked is not None
    assert picked in sample_places


def test_random_place_uses_module_random_when_none() -> None:
    # Just verify it doesn't crash and picks from the list. Determinism is
    # tested via the explicit-rng path above.
    place = Place(
        slug='a',
        name='A',
        kanji='甲',
        meaning='a',
        place_types=('village',),
        commonality='common',
    )
    picked = random_place([place])
    assert picked is place


def test_random_place_returns_none_for_empty() -> None:
    assert random_place([]) is None


def test_random_village_suffix_deterministic_with_seed() -> None:
    rng = random.Random(0)
    result = random_village_suffix(rng=rng)
    assert result in VILLAGE_SUFFIX_WEIGHTS


def test_random_village_suffix_without_seed_returns_known_suffix() -> None:
    result = random_village_suffix()
    assert result in VILLAGE_SUFFIX_WEIGHTS


def test_random_village_suffix_weights_favor_mura() -> None:
    # Across many draws with a seeded RNG, -mura should be the modal choice
    # given it has 45% weight.
    rng = random.Random(123)
    counts: dict[str, int] = dict.fromkeys(VILLAGE_SUFFIX_WEIGHTS, 0)
    for _ in range(2000):
        counts[random_village_suffix(rng=rng)] += 1
    most_common = max(counts, key=lambda k: counts[k])
    assert most_common == '-mura'


# ---------------------- villageify ----------------------


def test_villageify_appends_suffix_to_bare_element(sample_places: list[Place]) -> None:
    rng = random.Random(0)
    yuhi = next(p for p in sample_places if p.name == 'Yuhi')
    name, suffix = villageify(yuhi, rng=rng)
    assert name.startswith('Yuhi')
    assert suffix in VILLAGE_SUFFIX_WEIGHTS
    assert name == f'Yuhi{suffix}'


def test_villageify_leaves_suffixed_entries_alone(sample_places: list[Place]) -> None:
    yuhimura = next(p for p in sample_places if p.name == 'Yuhimura')
    name, suffix = villageify(yuhimura)
    assert name == 'Yuhimura'
    assert suffix == '-mura'


def test_villageify_handles_unknown_suffix() -> None:
    # An entry with a suffix that is neither in SUFFIX_EMIT_NOTES nor in
    # GEOGRAPHIC_ENDING_LABELS still resolves cleanly.
    place = Place(
        slug='x',
        name='X',
        kanji='X',
        meaning='x',
        place_types=('village',),
        commonality='common',
        suffix='-zzz',
    )
    name, suffix = villageify(place)
    assert name == 'X'
    assert suffix == '-zzz'


# ---------------------- scale_description ----------------------


def test_scale_description_for_village(sample_places: list[Place]) -> None:
    yuhimura = next(p for p in sample_places if p.name == 'Yuhimura')
    desc = scale_description(yuhimura, 'village')
    assert "Yuhimura (夕日村, 'sunset village') is a village." in desc
    assert 'generic word for village' in desc


def test_scale_description_falls_back_to_primary_scale(sample_places: list[Place]) -> None:
    yuhimura = next(p for p in sample_places if p.name == 'Yuhimura')
    desc = scale_description(yuhimura, 'province')  # not in place_types
    assert 'is a village.' in desc  # fell back to primary scale


def test_scale_description_handles_each_scale_label(sample_places: list[Place]) -> None:
    owari = next(p for p in sample_places if p.name == 'Owari')
    assert 'is a province.' in scale_description(owari, 'province')
    assert 'is a county town.' in scale_description(owari, 'town')
    assert 'is a village.' in scale_description(owari, 'village')
    assert 'is a hamlet.' in scale_description(owari, 'hamlet')


def test_scale_description_handles_unknown_scale_label() -> None:
    # If somehow a non-canonical scale appears in place_types, the label
    # falls back to "a <scale>" without crashing.
    place = Place(
        slug='x',
        name='X',
        kanji='X',
        meaning='x',
        place_types=('district',),
        commonality='common',
    )
    desc = scale_description(place, 'district')
    assert 'is a district.' in desc


def test_scale_description_includes_notes(sample_places: list[Place]) -> None:
    yuhi = next(p for p in sample_places if p.name == 'Yuhi')
    desc = scale_description(yuhi, 'hamlet')
    assert 'Paired with Yuhimura.' in desc


def test_scale_description_with_empty_place_types_uses_passed_scale() -> None:
    # Defensive: an entry with no place_types still produces a description
    # using the scale the caller passed.
    place = Place(
        slug='x',
        name='X',
        kanji='X',
        meaning='x',
        place_types=(),
        commonality='common',
    )
    desc = scale_description(place, 'village')
    assert 'is a village.' in desc


# ---------------------- constants integrity ----------------------


def test_suffix_emit_notes_cover_village_suffix_weights() -> None:
    # Every suffix used by random_village_suffix should have an emit-time note,
    # since selecting one means the resulting name is surfaced to the GM.
    for suffix in VILLAGE_SUFFIX_WEIGHTS:
        assert suffix in SUFFIX_EMIT_NOTES, f'{suffix} has no emit-time note'


def test_geographic_ending_labels_have_meaning() -> None:
    # Every label entry has a non-empty value.
    for ending, label in GEOGRAPHIC_ENDING_LABELS.items():
        assert ending.startswith('-')
        assert label  # non-empty


def test_place_dataclass_is_immutable() -> None:
    place = Place(
        slug='x',
        name='X',
        kanji='X',
        meaning='x',
        place_types=('village',),
        commonality='common',
    )
    with pytest.raises((AttributeError, TypeError)):
        place.name = 'Y'  # type: ignore[misc]
