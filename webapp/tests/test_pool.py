"""Tests for l7r.pool — frontmatter parsing and relic loading."""

from pathlib import Path

import pytest

from l7r.pool import Relic, load_relics


def test_load_relics_returns_all_well_formed_fixtures(sample_pool_dir: Path) -> None:
    relics = load_relics(sample_pool_dir)
    # The fixture pool has 4 well-formed files; one malformed file that should be skipped.
    assert len(relics) == 4
    slugs = {r.slug for r in relics}
    assert slugs == {
        'sample-benten-stone',
        'sample-benten-cup',
        'sample-bishamon-sword',
        'sample-ebisu-hammer',
    }


def test_load_relics_skips_files_missing_required_fields(
    sample_pool_dir: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    import logging

    caplog.set_level(logging.WARNING)
    relics = load_relics(sample_pool_dir)
    # The malformed file (missing `fortune`) must be skipped.
    assert all(r.slug != 'malformed' for r in relics)
    # A warning must have been logged about the skipped file.
    assert any('malformed' in record.getMessage() for record in caplog.records)


def test_relic_carries_all_frontmatter_fields(sample_pool_dir: Path) -> None:
    relics = load_relics(sample_pool_dir)
    stone = next(r for r in relics if r.slug == 'sample-benten-stone')
    assert stone.name == 'The Sample Stone of Test'
    assert stone.japanese_romaji == 'Tameshi-no-Ishi'
    assert stone.japanese_kanji == '試の石'
    assert stone.fortune == 'benten'
    assert stone.clan == 'fox'
    assert stone.temple == 'a temple of Benten in Fox lands'
    assert stone.named_entity == 'A fictional figure used as a test fixture'
    assert stone.relic_type == 'implement (test stone)'
    assert 'first paragraph is short' in stone.description
    assert '*emphasis*' in stone.description  # raw markdown; emphasis is rendered by a filter


def test_relic_summary_extracts_first_sentence(sample_pool_dir: Path) -> None:
    relics = load_relics(sample_pool_dir)
    stone = next(r for r in relics if r.slug == 'sample-benten-stone')
    # Sample description starts "A small stone used in tests. Its first
    # paragraph is short."
    assert stone.summary == 'A small stone used in tests.'


def test_relic_summary_strips_markdown_italic_markers() -> None:
    relic = Relic(
        slug='x',
        name='X',
        japanese_romaji='X',
        japanese_kanji='x',
        fortune='benten',
        clan='any',
        temple='somewhere',
        named_entity='someone',
        relic_type='thing',
        description='A bowl of *unusually* warm water. Next sentence.',
    )
    assert relic.summary == 'A bowl of unusually warm water.'


def test_relic_summary_handles_description_with_no_period() -> None:
    relic = Relic(
        slug='x',
        name='X',
        japanese_romaji='X',
        japanese_kanji='x',
        fortune='benten',
        clan='any',
        temple='somewhere',
        named_entity='someone',
        relic_type='thing',
        description='A single fragment with no terminating period',
    )
    # Falls back to the full body when no sentence terminator is found.
    assert relic.summary == 'A single fragment with no terminating period'


def test_relics_are_immutable() -> None:
    relic = Relic(
        slug='x',
        name='X',
        japanese_romaji='X',
        japanese_kanji='x',
        fortune='benten',
        clan='any',
        temple='somewhere',
        named_entity='someone',
        relic_type='thing',
        description='body',
    )
    with pytest.raises((AttributeError, TypeError)):
        relic.name = 'Y'  # type: ignore[misc]


def test_load_relics_with_nonexistent_directory_returns_empty_list(tmp_path: Path) -> None:
    empty = tmp_path / 'nope'
    relics = load_relics(empty)
    assert relics == []


def test_load_relics_with_empty_directory_returns_empty_list(tmp_path: Path) -> None:
    (tmp_path / 'benten').mkdir()
    relics = load_relics(tmp_path)
    assert relics == []


def test_load_relics_sorts_stably_by_slug(sample_pool_dir: Path) -> None:
    relics = load_relics(sample_pool_dir)
    slugs = [r.slug for r in relics]
    assert slugs == sorted(slugs)


def test_load_relics_ignores_files_at_pool_root(tmp_path: Path) -> None:
    # Files directly under pool_dir (not in a fortune subdirectory) are ignored.
    (tmp_path / 'stray.md').write_text('---\nname: x\n---\n')
    (tmp_path / 'benten').mkdir()
    relics = load_relics(tmp_path)
    assert relics == []


def test_load_relics_logs_warning_for_missing_frontmatter(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    import logging

    caplog.set_level(logging.WARNING)
    (tmp_path / 'benten').mkdir()
    (tmp_path / 'benten' / 'no-fm.md').write_text('Just prose, no frontmatter.')
    relics = load_relics(tmp_path)
    assert relics == []
    assert any('no frontmatter' in r.getMessage() for r in caplog.records)


def test_load_relics_logs_warning_for_yaml_error(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    import logging

    caplog.set_level(logging.WARNING)
    (tmp_path / 'benten').mkdir()
    bad = (
        '---\n'
        "name: '\n"  # unclosed quote → YAMLError
        '---\n'
        'body\n'
    )
    (tmp_path / 'benten' / 'bad-yaml.md').write_text(bad)
    relics = load_relics(tmp_path)
    assert relics == []
    assert any('YAML parse error' in r.getMessage() for r in caplog.records)


def test_load_relics_logs_warning_when_file_unreadable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    import logging

    caplog.set_level(logging.WARNING)
    (tmp_path / 'benten').mkdir()
    target = tmp_path / 'benten' / 'unreadable.md'
    target.write_text('---\nname: x\n---\nbody\n')

    original_read_text = Path.read_text

    def boom(self: Path, *args: object, **kwargs: object) -> str:
        if self == target:
            raise OSError('permission denied')
        return original_read_text(self, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(Path, 'read_text', boom)
    relics = load_relics(tmp_path)
    assert relics == []
    assert any('could not read file' in r.getMessage() for r in caplog.records)
