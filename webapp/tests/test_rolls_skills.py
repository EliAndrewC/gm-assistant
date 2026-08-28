"""The skill vocabulary, read from the real rules file rather than a copy."""

from __future__ import annotations

from pathlib import Path

import pytest

from l7r.repl.rolls.skills import (
    COMBAT_SKILLS,
    AmbiguousSkill,
    UnknownSkill,
    is_skill,
    load_skills,
    match_skill,
)


@pytest.fixture(scope='module')
def vocabulary() -> tuple[str, ...]:
    return load_skills()


class TestLoadFromTheRules:
    def test_reads_the_real_rules_file(self, vocabulary: tuple[str, ...]) -> None:
        # The point of the module: if this list is ever copied into the code, a
        # rename in the rules stops reaching us and nothing fails.
        for skill in (
            'bragging',
            'etiquette',
            'intimidation',
            'sincerity',
            'sneaking',
            'tact',
            'acting',
            'interrogation',
            'manipulation',
            'culture',
            'heraldry',
            'investigation',
            'law',
            'precepts',
            'strategy',
            'commerce',
            'history',
            'underworld',
        ):
            assert skill in vocabulary

    def test_includes_the_combat_skills(self, vocabulary: tuple[str, ...]) -> None:
        for skill in COMBAT_SKILLS:
            assert skill in vocabulary

    def test_everything_is_lowercased(self, vocabulary: tuple[str, ...]) -> None:
        assert all(s == s.lower() for s in vocabulary)

    def test_a_file_without_the_section_fails_loud(self, tmp_path: Path) -> None:
        broken = tmp_path / 'no-section.md'
        broken.write_text('# Skills\n\nSome prose.\n')
        with pytest.raises(UnknownSkill, match='no "## Skill List" section'):
            load_skills(broken)

    def test_an_empty_section_fails_loud(self, tmp_path: Path) -> None:
        broken = tmp_path / 'empty-section.md'
        broken.write_text('## Skill List\n\nnothing here\n\n## Detailed Skill Rules\n')
        with pytest.raises(UnknownSkill, match='lists no skills'):
            load_skills(broken)


class TestMatching:
    def test_exact(self, vocabulary: tuple[str, ...]) -> None:
        assert match_skill('etiquette', vocabulary) == 'etiquette'

    def test_case_insensitive(self, vocabulary: tuple[str, ...]) -> None:
        assert match_skill('Etiquette', vocabulary) == 'etiquette'
        assert match_skill('  INTERROGATION  ', vocabulary) == 'interrogation'

    def test_unambiguous_prefix(self, vocabulary: tuple[str, ...]) -> None:
        # Real messages: `24 eti`, `22 eti`.
        assert match_skill('eti', vocabulary) == 'etiquette'
        assert match_skill('manip', vocabulary) == 'manipulation'

    def test_ambiguous_prefix_raises_with_candidates(self, vocabulary: tuple[str, ...]) -> None:
        with pytest.raises(AmbiguousSkill) as caught:
            match_skill('int', vocabulary)
        assert set(caught.value.candidates) == {'intimidation', 'interrogation'}
        assert 'Name it in full' in str(caught.value)

    def test_unknown_raises(self, vocabulary: tuple[str, ...]) -> None:
        with pytest.raises(UnknownSkill, match='is not a skill'):
            match_skill('streetwise', vocabulary)

    def test_empty_raises(self, vocabulary: tuple[str, ...]) -> None:
        with pytest.raises(UnknownSkill, match='empty skill name'):
            match_skill('   ', vocabulary)

    def test_exact_match_beats_being_a_prefix_of_another(self) -> None:
        # No such pair exists in the rules today, but one could be added.
        assert match_skill('law', ('law', 'lawyering')) == 'law'


class TestIsSkill:
    def test_true_for_a_real_skill(self, vocabulary: tuple[str, ...]) -> None:
        assert is_skill('etiquette', vocabulary)
        assert is_skill('eti', vocabulary)

    def test_false_for_unknown_and_ambiguous(self, vocabulary: tuple[str, ...]) -> None:
        assert not is_skill('streetwise', vocabulary)
        assert not is_skill('int', vocabulary)
