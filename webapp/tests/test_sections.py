"""Tests for l7r.sections — nav registry."""

import pytest

from l7r.sections import SECTIONS, Section, find_section_by_slug


def test_sections_registry_contains_phase_1_entries() -> None:
    slugs = [s.slug for s in SECTIONS]
    assert 'chargen' in slugs
    assert 'relics' in slugs
    assert 'names' in slugs


def test_sections_registry_has_expected_shape() -> None:
    for section in SECTIONS:
        assert isinstance(section, Section)
        assert section.slug
        assert section.label
        assert section.path.startswith('/')


def test_chargen_and_relics_are_enabled() -> None:
    chargen = find_section_by_slug('chargen')
    relics = find_section_by_slug('relics')
    assert chargen is not None
    assert relics is not None
    assert chargen.enabled
    assert relics.enabled


def test_names_is_enabled() -> None:
    names = find_section_by_slug('names')
    assert names is not None
    assert names.enabled is True


def test_find_section_by_slug_returns_none_for_unknown() -> None:
    assert find_section_by_slug('does-not-exist') is None


@pytest.mark.parametrize(
    ('slug', 'expected_path'),
    [
        ('chargen', '/chargen'),
        ('relics', '/relics'),
        ('names', '/names'),
    ],
)
def test_section_paths(slug: str, expected_path: str) -> None:
    section = find_section_by_slug(slug)
    assert section is not None
    assert section.path == expected_path


def test_sections_is_a_tuple_so_callers_cannot_mutate_it() -> None:
    assert isinstance(SECTIONS, tuple)
