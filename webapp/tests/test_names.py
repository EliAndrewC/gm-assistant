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
