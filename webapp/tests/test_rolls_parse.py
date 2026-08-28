"""The typed-roll parser, tested against the forms that actually appear in the GM's channels.

Every string in `TestObservedForms` is a real message from the corpus (research.md
R3), and every string in `TestAdversarialNegatives` is a real message that must NOT
produce a roll (R5).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from l7r.repl.rolls.parse import MIN_TOTAL, parse_message
from l7r.repl.rolls.skills import load_skills

WHEN = datetime(2026, 8, 12, 1, 54, tzinfo=UTC)


@pytest.fixture(scope='module')
def vocabulary() -> tuple[str, ...]:
    return load_skills()


def parse(text: str, vocabulary: tuple[str, ...]) -> list[tuple[str, int, int | None]]:
    rolls, _ = parse_message(text, vocabulary, character='Jimen', message_id='1', at=WHEN)
    return [(r.skill, r.total, r.rank) for r in rolls]


class TestObservedForms:
    @pytest.mark.parametrize(
        ('text', 'expected'),
        [
            ('38 Etiquette @3', [('etiquette', 38, 3)]),
            ('23 Investigation@2', [('investigation', 23, 2)]),
            ('35 Interrogation', [('interrogation', 35, None)]),
            ('24 eti', [('etiquette', 24, None)]),
            ('20 Underworld at 2', [('underworld', 20, 2)]),
            ('26@3 Etiquette', [('etiquette', 26, 3)]),
            ('@27 Tact to drop comments', [('tact', 27, None)]),
            ('52 law@3 to argue that it was clear', [('law', 52, 3)]),
            ('43 Interrogation@3 (38 + 5 Discerning)', [('interrogation', 43, 3)]),
            ('15 etiquette (24, limited by Withdrawn)', [('etiquette', 15, None)]),
            ('10->9 8 +5 Streetwise = 32 Law@2', [('law', 32, 2)]),
            ('10->10->10->4  10->8 5 4=61+5=66 Sincerity@1', [('sincerity', 66, 1)]),
            ('10->7 10->7 8 8 +15 65@4 Intimidation', [('intimidation', 65, 4)]),
            ('47 Etiquette@3 assuming streetwise counts', [('etiquette', 47, 3)]),
            ('18 Commerce@0', [('commerce', 18, 0)]),
        ],
    )
    def test_form(
        self, text: str, expected: list[tuple[str, int, int | None]], vocabulary: tuple[str, ...]
    ) -> None:
        assert parse(text, vocabulary) == expected

    def test_two_rolls_on_one_line(self, vocabulary: tuple[str, ...]) -> None:
        found = parse('30 investigation@3, 36 Interrogation@3: where is Kyoma?', vocabulary)
        assert found == [('investigation', 30, 3), ('interrogation', 36, 3)]

    def test_two_rolls_on_two_lines(self, vocabulary: tuple[str, ...]) -> None:
        found = parse('45 sneaking@3 to follow the PCs.\n35 investigation@3 to check', vocabulary)
        assert found == [('sneaking', 45, 3), ('investigation', 35, 3)]

    def test_a_header_line_does_not_disturb_the_roll(self, vocabulary: tuple[str, ...]) -> None:
        found = parse('Meeting Inspector Fumitake:\n15 etiquette (35 + 5)', vocabulary)
        assert found == [('etiquette', 15, None)]


class TestFalsePositivesFoundByMeasurement:
    """Each of these was parsed WRONGLY by the first implementation.

    Kept as tests rather than as a note, because the fix for each one is a rule
    that a later change could silently undo.
    """

    def test_a_bonus_term_is_not_a_total(self, vocabulary: tuple[str, ...]) -> None:
        # Read as "acting 15" on the first run. The 15 is an addend and `acting`
        # names the source of the bonus, not the skill rolled.
        assert parse('31+15acting+10 for two free raises', vocabulary) == []

    def test_a_cluster_does_not_span_a_newline(self, vocabulary: tuple[str, ...]) -> None:
        # Read as "interrogation 15" on the first run, pairing the 15 ending the
        # first line with the skill opening the second.
        assert parse('Intimidation 8k4 +15\nInterrogation 7k4 +5', vocabulary) == []

    def test_a_parenthesized_breakdown_is_not_a_second_roll(
        self, vocabulary: tuple[str, ...]
    ) -> None:
        # Read as sincerity 50 AND acting 15 on the first run.
        found = parse('50 sincerity@5 (30 + 5 Second Dan + 15 Acting) for the act', vocabulary)
        assert found == [('sincerity', 50, 5)]


class TestAdversarialNegatives:
    """Real messages carrying numbers that are not rolls (research.md R5)."""

    @pytest.mark.parametrize(
        'text',
        [
            'We started this one on 06/20/2023',
            'Looks like the Hidden Way Campaign ended on 22 December 2022',
            "There were 85 sessions in the Tuesday group's Karmic Inquisitors Campaign.",
            'Wakku rn is Fire 5, Air 4, Water 6, Void 5, and 8 Earth (15 serious)',
            "It doesn't look like the Unkept disadvantage is tracking the -10 to Culture",
            'Two people have 1 Interrogation each',
            '6 9 6 9',
            '1, 1, 2, 5.  Sigh',
            'brb bathroom',
            '',
            'On the size of the bounty (200 koku)',
        ],
    )
    def test_produces_no_roll(self, text: str, vocabulary: tuple[str, ...]) -> None:
        assert parse(text, vocabulary) == []

    def test_discord_markup_digits_are_stripped(self, vocabulary: tuple[str, ...]) -> None:
        assert parse('<@316306960855072769> Etiquette', vocabulary) == []
        assert parse('Yep never met him! <:AJLie:1009245958724386887> Tact', vocabulary) == []

    def test_a_url_is_not_a_roll(self, vocabulary: tuple[str, ...]) -> None:
        assert parse('https://example.com/characters/33 Acting', vocabulary) == []

    def test_a_total_below_the_floor_is_not_a_roll(self, vocabulary: tuple[str, ...]) -> None:
        assert parse(f'{MIN_TOTAL - 1} Interrogation', vocabulary) == []
        assert parse(f'{MIN_TOTAL} Interrogation', vocabulary) == [
            ('interrogation', MIN_TOTAL, None)
        ]


class TestReportedRatherThanGuessed:
    def test_the_ambiguous_at_band_is_reported(self, vocabulary: tuple[str, ...]) -> None:
        rolls, problems = parse_message('@7 Tact', vocabulary)
        assert rolls == []
        assert any('could be a rank or a total' in p for p in problems)

    def test_a_leading_at_that_is_clearly_a_rank_is_silent(
        self, vocabulary: tuple[str, ...]
    ) -> None:
        rolls, problems = parse_message('@3 Etiquette', vocabulary)
        assert rolls == []
        assert problems == []

    def test_an_impossible_rank_is_reported(self, vocabulary: tuple[str, ...]) -> None:
        rolls, problems = parse_message('38 Etiquette @9', vocabulary)
        assert rolls == []
        assert any('above the maximum' in p for p in problems)

    def test_an_ambiguous_abbreviation_is_reported(self, vocabulary: tuple[str, ...]) -> None:
        # `int` prefixes both intimidation and interrogation. Two letters would
        # not reach the matcher at all - the pattern requires three.
        rolls, problems = parse_message('24 int', vocabulary)
        assert rolls == []
        assert any('could be any of' in p for p in problems)

    def test_the_leading_at_form_with_a_non_skill_is_silent(
        self, vocabulary: tuple[str, ...]
    ) -> None:
        # `@27 Bushido` has the shape of the `@27 Tact` form but names no skill.
        rolls, problems = parse_message('@27 Bushido', vocabulary)
        assert rolls == []
        assert problems == []

    def test_an_unknown_word_is_silent(self, vocabulary: tuple[str, ...]) -> None:
        # Most words in a sentence are not skills; reporting each would bury the
        # problems that matter.
        _, problems = parse_message('22 December 2022', vocabulary)
        assert problems == []


class TestRollFields:
    def test_carries_provenance(self, vocabulary: tuple[str, ...]) -> None:
        rolls, _ = parse_message(
            '38 Etiquette @3', vocabulary, character='Jimen', message_id='42', at=WHEN
        )
        assert rolls[0].source == 'typed'
        assert rolls[0].message_id == '42'
        assert rolls[0].at == WHEN
        assert rolls[0].character == 'Jimen'

    def test_defaults_the_timestamp_when_none_given(self, vocabulary: tuple[str, ...]) -> None:
        rolls, _ = parse_message('38 Etiquette @3', vocabulary)
        assert rolls[0].at.tzinfo is not None
