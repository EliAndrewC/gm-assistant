"""Behavior tests for the full-corpus brief assembly (``chargen.brief``)."""

from __future__ import annotations

from pathlib import Path

import pytest

from chargen import brief

_L7R_SAMPLE = (
    '# Notes\n\n'
    '## The Setting\n\nintro\n\n'
    '### The Great Clans\n\nClans are alike.\n\n'
    '### Hierarchies\n\ntiers\n\n'
    '## Next Chapter\n\nmore\n'
)


def _make_corpus(tmp_path: Path, l7r: str = _L7R_SAMPLE, budgets: str = 'BUDGETS BODY') -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / 'l7r.md').write_text(l7r, encoding='utf-8')
    (tmp_path / 'budgets.md').write_text(budgets, encoding='utf-8')
    return tmp_path


def test_candidate_dirs_lists_env_first_when_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('L7R_SETTING_DIR', '/explicit/dir')
    dirs = brief._candidate_dirs()
    assert dirs[0] == Path('/explicit/dir')
    assert dirs[1:] == [brief._MOUNT_DIR, brief._BUNDLED_DIR]


def test_candidate_dirs_omits_env_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv('L7R_SETTING_DIR', raising=False)
    assert brief._candidate_dirs() == [brief._MOUNT_DIR, brief._BUNDLED_DIR]


def test_resolve_prefers_mount_over_bundle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mount = _make_corpus(tmp_path / 'mount')
    bundle = _make_corpus(tmp_path / 'bundle')
    monkeypatch.delenv('L7R_SETTING_DIR', raising=False)
    monkeypatch.setattr(brief, '_MOUNT_DIR', mount)
    monkeypatch.setattr(brief, '_BUNDLED_DIR', bundle)
    assert brief.resolve_corpus_dir() == mount


def test_resolve_prefers_env_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    corpus = _make_corpus(tmp_path)
    monkeypatch.setenv('L7R_SETTING_DIR', str(corpus))
    assert brief.resolve_corpus_dir() == corpus


def test_resolve_falls_back_to_bundled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    corpus = _make_corpus(tmp_path)
    monkeypatch.delenv('L7R_SETTING_DIR', raising=False)
    monkeypatch.setattr(brief, '_BUNDLED_DIR', corpus)
    monkeypatch.setattr(brief, '_MOUNT_DIR', tmp_path / 'nope')
    assert brief.resolve_corpus_dir() == corpus


def test_resolve_raises_when_no_corpus(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv('L7R_SETTING_DIR', raising=False)
    monkeypatch.setattr(brief, '_BUNDLED_DIR', tmp_path / 'a')
    monkeypatch.setattr(brief, '_MOUNT_DIR', tmp_path / 'b')
    with pytest.raises(brief.CorpusNotFound) as exc:
        brief.resolve_corpus_dir()
    assert 'not found' in str(exc.value)


def test_extract_section_stops_at_next_same_level() -> None:
    out = brief.extract_section(_L7R_SAMPLE, 'The Great Clans')
    assert out == '### The Great Clans\n\nClans are alike.'


def test_extract_section_swallows_lower_levels_until_higher() -> None:
    out = brief.extract_section(_L7R_SAMPLE, 'The Setting')
    assert 'The Great Clans' in out
    assert 'Hierarchies' in out
    assert 'Next Chapter' not in out


def test_extract_section_runs_to_eof_when_no_following_heading() -> None:
    assert brief.extract_section('## Only\n\nbody line\n', 'Only') == '## Only\n\nbody line'


def test_extract_section_raises_when_missing() -> None:
    with pytest.raises(ValueError, match='heading not found'):
        brief.extract_section(_L7R_SAMPLE, 'No Such Heading')


def test_build_full_brief_assembles_in_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    corpus = _make_corpus(tmp_path)
    brief_md = tmp_path / 'brief.md'
    flavor_md = tmp_path / 'flavor.md'
    brief_md.write_text('DESIGN BRIEF\n', encoding='utf-8')
    flavor_md.write_text('FLAVOR SUMMARY\n', encoding='utf-8')
    monkeypatch.setattr(brief, '_BRIEF_PATH', brief_md)
    monkeypatch.setattr(brief, '_FLAVOR_PATH', flavor_md)

    out = brief.build_full_brief(corpus)

    expected = '\n\n'.join(
        [
            'DESIGN BRIEF',
            '### The Great Clans\n\nClans are alike.',
            'FLAVOR SUMMARY',
            '# FULL CANONICAL NOTES\n\n'
            + _L7R_SAMPLE.strip()
            + '\n\n# BUDGETS AND ECONOMIC MODEL (budgets.md)\n\nBUDGETS BODY',
        ]
    )
    assert out == expected


def test_build_full_brief_resolves_when_no_corpus_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    corpus = _make_corpus(tmp_path)
    brief_md = tmp_path / 'brief.md'
    flavor_md = tmp_path / 'flavor.md'
    brief_md.write_text('B', encoding='utf-8')
    flavor_md.write_text('F', encoding='utf-8')
    monkeypatch.setattr(brief, '_BRIEF_PATH', brief_md)
    monkeypatch.setattr(brief, '_FLAVOR_PATH', flavor_md)
    monkeypatch.delenv('L7R_SETTING_DIR', raising=False)
    monkeypatch.setattr(brief, '_BUNDLED_DIR', corpus)
    monkeypatch.setattr(brief, '_MOUNT_DIR', tmp_path / 'nope')

    out = brief.build_full_brief()
    assert out.startswith('B\n\n### The Great Clans')
    assert out.endswith('BUDGETS BODY')


def test_build_full_brief_raises_when_corpus_dir_incomplete(tmp_path: Path) -> None:
    (tmp_path / 'l7r.md').write_text('## The Great Clans\n\nx\n', encoding='utf-8')
    with pytest.raises(brief.CorpusNotFound):
        brief.build_full_brief(tmp_path)
