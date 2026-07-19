"""Tests for l7r.dreams - dream-scene pool loading and the spoiler boundary."""

import logging
from pathlib import Path

import pytest

from l7r.dreams import (
    DreamScene,
    _first_sentence,
    find_scene_by_slug,
    load_dream_scenes,
    render_markdown,
)


def test_load_returns_well_formed_scenes(sample_dream_pool_dir: Path) -> None:
    scenes = load_dream_scenes(sample_dream_pool_dir)
    # Two well-formed files; one malformed (missing sender) is skipped.
    assert {s.slug for s in scenes} == {'sample-daikoku-scene', 'sample-ebisu-scene'}


def test_load_skips_malformed_with_warning(
    sample_dream_pool_dir: Path, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.WARNING)
    scenes = load_dream_scenes(sample_dream_pool_dir)
    assert all(s.slug != 'malformed-missing-sender' for s in scenes)
    assert any('malformed-missing-sender' in r.getMessage() for r in caplog.records)


def test_scene_carries_frontmatter_and_rendered_body(sample_dream_pool_dir: Path) -> None:
    scenes = load_dream_scenes(sample_dream_pool_dir)
    daikoku = find_scene_by_slug(scenes, 'sample-daikoku-scene')
    assert daikoku is not None
    assert daikoku.title == 'Sample Daikoku Scene'
    assert daikoku.sender == 'Daikoku, the Fortune of Wealth'
    assert daikoku.sender_type == 'fortune'
    # Body is rendered from markdown to HTML.
    assert '<h2>A section</h2>' in daikoku.body_html
    assert '<blockquote>' in daikoku.body_html
    assert '<li>A fragment.</li>' in daikoku.body_html
    # The leading H1 (duplicate of the title) is stripped from the body.
    assert '<h1>' not in daikoku.body_html


def test_explicit_summary_is_used_for_the_card(sample_dream_pool_dir: Path) -> None:
    scenes = load_dream_scenes(sample_dream_pool_dir)
    daikoku = find_scene_by_slug(scenes, 'sample-daikoku-scene')
    assert daikoku is not None
    assert daikoku.summary == 'A short explicit descriptor used by the gallery card.'


def test_summary_falls_back_to_first_body_sentence(sample_dream_pool_dir: Path) -> None:
    scenes = load_dream_scenes(sample_dream_pool_dir)
    ebisu = find_scene_by_slug(scenes, 'sample-ebisu-scene')
    assert ebisu is not None
    # No `summary` in frontmatter; the H1 is skipped and the first prose
    # sentence is used.
    expected = 'No explicit summary here, so the card falls back to this first sentence.'
    assert ebisu.summary == expected


def test_default_sender_type_when_absent(sample_dream_pool_dir: Path) -> None:
    scenes = load_dream_scenes(sample_dream_pool_dir)
    ebisu = find_scene_by_slug(scenes, 'sample-ebisu-scene')
    assert ebisu is not None
    assert ebisu.sender_type == 'fortune'


def test_scenes_are_sorted_by_title(sample_dream_pool_dir: Path) -> None:
    scenes = load_dream_scenes(sample_dream_pool_dir)
    titles = [s.title for s in scenes]
    assert titles == sorted(titles)


def test_find_scene_by_slug_returns_none_for_unknown(sample_dream_pool_dir: Path) -> None:
    scenes = load_dream_scenes(sample_dream_pool_dir)
    assert find_scene_by_slug(scenes, 'does-not-exist') is None


# --- The spoiler boundary (FR-007), the load-bearing invariant --------------


def test_loader_never_reads_sibling_pool_local(sample_dream_pool_dir: Path) -> None:
    """The decoy scene lives in the sibling pool-local/ tier and must never load."""
    # Sanity: the decoy really exists on disk next to the public pool.
    decoy = sample_dream_pool_dir.parent / 'pool-local' / 'decoy-spoiler-scene.md'
    assert decoy.exists()

    scenes = load_dream_scenes(sample_dream_pool_dir)
    assert all(s.slug != 'decoy-spoiler-scene' for s in scenes)
    assert find_scene_by_slug(scenes, 'decoy-spoiler-scene') is None


# --- Edge cases -------------------------------------------------------------


def test_missing_directory_returns_empty_list(tmp_path: Path) -> None:
    assert load_dream_scenes(tmp_path / 'nope') == []


def test_path_that_is_a_file_returns_empty_list(tmp_path: Path) -> None:
    not_a_dir = tmp_path / 'a-file'
    not_a_dir.write_text('not a directory')
    assert load_dream_scenes(not_a_dir) == []


def _scene_file(name: str, title: str, sender: str) -> str:
    return f'---\nname: {name}\ntitle: {title}\nsender: {sender}\n---\n\n# {title}\n\nBody.\n'


def test_new_scene_file_appears_without_code_change(tmp_path: Path) -> None:
    """FR-006 / SC-003: dropping a valid file into the pool makes it appear."""
    (tmp_path / 'zzz-new.md').write_text(_scene_file('zzz-new', 'Zzz A New Scene', 'Hotei'))
    (tmp_path / 'aaa-first.md').write_text(_scene_file('aaa-first', 'Aaa First Scene', 'Jurojin'))
    scenes = load_dream_scenes(tmp_path)
    assert [s.slug for s in scenes] == ['aaa-first', 'zzz-new']  # deterministic title sort


def test_readme_in_pool_is_silently_ignored(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.WARNING)
    (tmp_path / 'README.md').write_text('# Pool docs\n\nNot a scene.\n')
    (tmp_path / 'real.md').write_text(_scene_file('real', 'Real Scene', 'Daikoku'))
    scenes = load_dream_scenes(tmp_path)
    assert [s.slug for s in scenes] == ['real']
    assert not any('README' in r.getMessage() for r in caplog.records)


def test_logs_warning_for_missing_frontmatter(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.WARNING)
    (tmp_path / 'no-fm.md').write_text('Just prose, no frontmatter.')
    assert load_dream_scenes(tmp_path) == []
    assert any('no frontmatter' in r.getMessage() for r in caplog.records)


def test_logs_warning_for_yaml_error(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.WARNING)
    (tmp_path / 'bad.md').write_text("---\nname: '\n---\nbody\n")  # unclosed quote
    assert load_dream_scenes(tmp_path) == []
    assert any('YAML parse error' in r.getMessage() for r in caplog.records)


def test_logs_warning_for_empty_body(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.WARNING)
    (tmp_path / 'empty.md').write_text('---\nname: e\ntitle: Empty\nsender: Benten\n---\n\n   \n')
    assert load_dream_scenes(tmp_path) == []
    assert any('empty body' in r.getMessage() for r in caplog.records)


def test_logs_warning_when_file_unreadable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.WARNING)
    target = tmp_path / 'unreadable.md'
    target.write_text('---\nname: x\ntitle: X\nsender: Daikoku\n---\nbody\n')

    original_read_text = Path.read_text

    def boom(self: Path, *args: object, **kwargs: object) -> str:
        if self == target:
            raise OSError('permission denied')
        return original_read_text(self, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(Path, 'read_text', boom)
    assert load_dream_scenes(tmp_path) == []
    assert any('could not read file' in r.getMessage() for r in caplog.records)


def test_scenes_are_immutable() -> None:
    scene = DreamScene(
        slug='x',
        name='X',
        title='X',
        sender='Daikoku',
        sender_type='fortune',
        summary='s',
        body_html='<p>b</p>',
    )
    with pytest.raises((AttributeError, TypeError)):
        scene.title = 'Y'  # type: ignore[misc]


# --- _first_sentence unit coverage ------------------------------------------


def test_first_sentence_skips_headings_and_takes_first_sentence() -> None:
    assert _first_sentence('# Heading\n\nOne. Two.') == 'One.'


def test_first_sentence_returns_whole_paragraph_without_period() -> None:
    assert _first_sentence('# Heading\n\nA fragment with no terminator') == (
        'A fragment with no terminator'
    )


def test_first_sentence_returns_empty_when_only_headings() -> None:
    assert _first_sentence('# Only A Heading') == ''


def test_render_markdown_escapes_raw_html() -> None:
    # Raw HTML in the source must be escaped, not passed through.
    assert '<script>' not in render_markdown('a <script>alert(1)</script> b')
