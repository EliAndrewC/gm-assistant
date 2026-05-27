"""Tests for l7r.jinja_env — template environment and filters."""

import pytest
from markupsafe import Markup

from l7r.jinja_env import build_environment, description_html, relic_type_short


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
