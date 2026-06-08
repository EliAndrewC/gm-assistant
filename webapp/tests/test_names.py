"""Tests for l7r.names - JSONL pool loading."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from l7r.names import GeneratedName, load_names


@pytest.fixture(scope='session')
def sample_names_dir() -> Path:
    return Path(__file__).parent / 'fixtures' / 'names_sample'


def test_load_names_returns_all_entries(sample_names_dir: Path) -> None:
    names = load_names(sample_names_dir)
    assert len(names) == 5
    # Sorted by gender, then name
    assert [n.name for n in names] == ['Akiko', 'Hanae', 'Goro', 'Hiroshi', 'Toshiro']


def test_load_names_preserves_fields(sample_names_dir: Path) -> None:
    names = load_names(sample_names_dir)
    hiroshi = next(n for n in names if n.name == 'Hiroshi')
    assert hiroshi.gender == 'male'
    assert hiroshi.format == 1
    assert 'generous prosperity' in hiroshi.explanation
    assert hiroshi.peasant is False
    assert hiroshi.notes == 'Real Japanese name.'


def test_load_names_marks_peasant(sample_names_dir: Path) -> None:
    names = load_names(sample_names_dir)
    goro = next(n for n in names if n.name == 'Goro')
    assert goro.peasant is True


def test_load_names_with_nonexistent_directory_returns_empty(tmp_path: Path) -> None:
    assert load_names(tmp_path / 'nope') == []


def test_load_names_with_empty_directory_returns_empty(tmp_path: Path) -> None:
    assert load_names(tmp_path) == []


def test_load_names_skips_blank_lines_and_logs_bad_json(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.WARNING)
    (tmp_path / 'pool-male.jsonl').write_text(
        '\n{"name": "Good", "gender": "male", "format": 1, "explanation": "ok"}\n\nnot-json\n'
    )
    names = load_names(tmp_path)
    assert len(names) == 1
    assert names[0].name == 'Good'
    assert any('JSON parse error' in r.getMessage() for r in caplog.records)


def test_load_names_skips_entries_missing_required_fields(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.WARNING)
    (tmp_path / 'pool-female.jsonl').write_text(
        '{"name": "Akemi"}\n'  # missing gender, format, explanation
        '{"name": "Sayuri", "gender": "female", "format": 1, "explanation": "ok"}\n'
    )
    names = load_names(tmp_path)
    assert len(names) == 1
    assert names[0].name == 'Sayuri'
    assert any('missing' in r.getMessage() for r in caplog.records)


def test_load_names_logs_when_file_unreadable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.WARNING)
    target = tmp_path / 'pool-male.jsonl'
    target.write_text('{"name": "X", "gender": "male", "format": 1, "explanation": "ok"}\n')

    original_read_text = Path.read_text

    def boom(self: Path, *args: object, **kwargs: object) -> str:
        if self == target:
            raise OSError('denied')
        return original_read_text(self, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(Path, 'read_text', boom)
    names = load_names(tmp_path)
    assert names == []
    assert any('could not read file' in r.getMessage() for r in caplog.records)


def test_generated_name_is_immutable() -> None:
    name = GeneratedName(
        name='X', gender='male', format=1, explanation='ok', peasant=False, notes=''
    )
    with pytest.raises((AttributeError, TypeError)):
        name.name = 'Y'  # type: ignore[misc]


# ---------------------- slug, random, lookup ----------------------


def test_slug_combines_gender_and_slugified_name() -> None:
    n = GeneratedName(
        name='Hiroshi', gender='male', format=1, explanation='', peasant=False, notes=''
    )
    assert n.slug == 'male-hiroshi'


def test_slug_handles_punctuation_in_name() -> None:
    n = GeneratedName(
        name="O'Hana", gender='female', format=1, explanation='', peasant=False, notes=''
    )
    assert n.slug == 'female-o-hana'


def test_find_name_by_slug_returns_match(sample_names_dir: Path) -> None:
    import random as r

    from l7r.names import find_name_by_slug

    names = load_names(sample_names_dir)
    found = find_name_by_slug(names, 'male-hiroshi')
    assert found is not None
    assert found.name == 'Hiroshi'
    _ = r  # keep import alive for the next test in the same file


def test_find_name_by_slug_returns_none_for_miss(sample_names_dir: Path) -> None:
    from l7r.names import find_name_by_slug

    names = load_names(sample_names_dir)
    assert find_name_by_slug(names, 'nope') is None


def test_random_name_picks_from_list(sample_names_dir: Path) -> None:
    import random as r

    from l7r.names import random_name

    names = load_names(sample_names_dir)
    picked = random_name(names, rng=r.Random(0))
    assert picked is not None
    assert picked in names


def test_random_name_uses_module_random_when_none(sample_names_dir: Path) -> None:
    # Verify the unseeded branch runs without crashing and returns a valid entry.
    from l7r.names import random_name

    names = load_names(sample_names_dir)
    picked = random_name(names)
    assert picked is not None
    assert picked in names


def test_random_name_returns_none_for_empty() -> None:
    from l7r.names import random_name

    assert random_name([]) is None
