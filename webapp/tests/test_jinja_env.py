"""Tests for l7r.jinja_env — template environment and filters."""

from pathlib import Path

import pytest
from markupsafe import Markup

from l7r.jinja_env import (
    build_environment,
    description_html,
    relic_type_short,
    static_url,
    static_version,
)


def test_description_html_wraps_paragraphs_in_p_tags() -> None:
    out = description_html('First paragraph.\n\nSecond paragraph.')
    assert isinstance(out, Markup)
    assert '<p>First paragraph.</p>' in out
    assert '<p>Second paragraph.</p>' in out


def test_description_html_renders_asterisk_italics_as_em() -> None:
    out = description_html('The *Honest Masu* is held.')
    assert '<em>Honest Masu</em>' in out


def test_description_html_escapes_html_in_source() -> None:
    out = description_html('A <script>alert("x")</script> entry.')
    assert '<script>' not in out
    assert '&lt;script&gt;' in out


def test_description_html_strips_empty_paragraphs() -> None:
    out = description_html('\n\nA\n\n\n\nB\n\n')
    assert out.count('<p>') == 2


def test_description_html_with_no_italics() -> None:
    out = description_html('Plain text only.')
    assert '<em>' not in out
    assert '<p>Plain text only.</p>' in out


@pytest.mark.parametrize(
    ('input_str', 'expected'),
    [
        ('implement (rice-measure)', 'implement'),
        ('vessel (rice-bowl)', 'vessel'),
        ('pair', 'pair'),
        ('  spaced (parenthetical)  ', 'spaced'),
    ],
)
def test_relic_type_short(input_str: str, expected: str) -> None:
    assert relic_type_short(input_str) == expected


def test_environment_has_filters_registered() -> None:
    env = build_environment()
    assert 'description_html' in env.filters
    assert 'relic_type_short' in env.filters
    assert 'clan_label' in env.filters


def test_environment_has_globals_registered() -> None:
    env = build_environment()
    assert 'SECTIONS' in env.globals
    assert 'FORTUNES' in env.globals
    assert 'CLANS' in env.globals
    assert 'STATIC_VERSION' in env.globals
    assert 'static_url' in env.globals


def test_static_version_returns_dev_when_dir_missing(tmp_path: Path) -> None:
    # When the static directory doesn't exist, the helper degrades to 'dev'.
    assert static_version(tmp_path / 'nope') == 'dev'


def test_static_version_hashes_real_dir_contents(tmp_path: Path) -> None:
    static_dir = tmp_path / 'static'
    static_dir.mkdir()
    (static_dir / 'a.css').write_text('body { color: red; }')
    (static_dir / 'b.js').write_text('console.log("hi");')
    v1 = static_version(static_dir)
    assert v1 != 'dev'
    assert len(v1) == 12  # truncated SHA1
    # Same content → same hash.
    assert v1 == static_version(static_dir)
    # Changed content → different hash.
    (static_dir / 'a.css').write_text('body { color: blue; }')
    v2 = static_version(static_dir)
    assert v2 != v1


def test_static_url_appends_version_query() -> None:
    assert static_url('css/l7r.css', 'abc123') == '/static/css/l7r.css?v=abc123'
    # Tolerate either a leading slash or not on input.
    assert static_url('/css/l7r.css', 'abc123') == '/static/css/l7r.css?v=abc123'
