"""The GM's recording rules. These tests encode the GM's own words as assertions."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from l7r.repl.rolls.models import RecordingRule, Roll
from l7r.repl.rolls.rules import (
    CONTESTED_PAIRS,
    OPPOSING_SKILL,
    contest,
    contested_winner,
    margin_text,
    opposing_skill,
    personal_name,
    record,
    render_contest,
    render_open,
    round_down,
    skills_text,
)
from l7r.repl.rolls.skills import RULES_PATH, load_skills

WHEN = datetime(2026, 8, 12, 1, 54, tzinfo=UTC)


def roll(name: str, total: int, skill: str = 'etiquette', rank: int | None = None) -> Roll:
    return Roll(
        character=name,
        skill=skill,
        total=total,
        source='typed',
        message_id='1',
        at=WHEN,
        rank=rank,
    )


class TestRoundDown:
    """*"I do not distinguish between, for example, a twenty five and a twenty eight."*"""

    @pytest.mark.parametrize(
        ('total', 'expected'),
        [(25, 25), (26, 25), (28, 25), (29, 25), (30, 30), (24, 20), (19, 15), (10, 10)],
    )
    def test_rounds_down_to_five(self, total: int, expected: int) -> None:
        assert round_down(total) == expected

    def test_zero_and_negative_clamp_to_zero(self) -> None:
        # A negative total cannot come from dice; it would come from a mis-parse,
        # and floor division would turn -3 into -5 and make the error look real.
        assert round_down(0) == 0
        assert round_down(-3) == 0

    def test_other_increments(self) -> None:
        assert round_down(28, 10) == 20
        assert round_down(28, 1) == 28

    def test_increment_must_be_positive(self) -> None:
        with pytest.raises(ValueError, match='increment must be positive'):
            round_down(10, 0)


class TestEtiquetteCap:
    """*"open etiquette rolls are capped at forty ... if someone rolled a sixty
    eight, I would simply write down forty."*"""

    def test_the_gms_own_example(self) -> None:
        assert record(68, 'etiquette') == 40

    def test_not_merely_rounded(self) -> None:
        assert record(68, 'etiquette') != 65

    def test_case_insensitive(self) -> None:
        assert record(68, 'Etiquette') == 40

    def test_below_the_cap_is_only_rounded(self) -> None:
        assert record(38, 'etiquette') == 35

    def test_other_skills_are_uncapped(self) -> None:
        # *"A gift can be so exceptional that someone will talk about it for their
        # whole life. Therefore, recording higher roles for gift giving makes sense."*
        assert record(68, 'commerce') == 65

    def test_a_new_capped_skill_is_one_dict_entry(self) -> None:
        """SC-006: adding a rule is a data change, not a restructuring."""
        stricter = RecordingRule(caps={'etiquette': 40, 'bragging': 20})
        assert record(68, 'bragging', stricter) == 20
        assert record(68, 'commerce', stricter) == 65

    def test_cap_applies_before_rounding(self) -> None:
        # Invisible at 40 because it is already a multiple of 5, but the order is
        # the GM's and a cap that is not a multiple would expose it.
        odd = RecordingRule(caps={'etiquette': 38})
        assert record(68, 'etiquette', odd) == 35


class TestContest:
    """*"show each of the two roles ... the difference between them and who won.
    The amount that the winner won by should be rounded down."*"""

    def test_scores_and_keeps_the_raw_margin(self) -> None:
        scored = contest(roll('Jimen', 41, 'sincerity'), roll('Otsuki', 28, 'sincerity'))
        assert scored.winner == 'Jimen'
        assert scored.margin == 13, 'raw; the banding is applied when it is written'
        assert scored.left.total == 41  # *"the rolls themselves are not rounded"*
        assert scored.right.total == 28

    def test_right_side_can_win(self) -> None:
        scored = contest(roll('Jimen', 20, 'sincerity'), roll('Otsuki', 44, 'sincerity'))
        assert scored.winner == 'Otsuki'
        assert scored.margin == 24

    def test_a_tie_has_no_winner(self) -> None:
        scored = contest(roll('Jimen', 30, 'sincerity'), roll('Otsuki', 30, 'sincerity'))
        assert scored.tied
        assert scored.winner is None
        assert scored.margin == 0


class TestRenderOpen:
    def test_reproduces_the_gms_own_example(self) -> None:
        line = render_open(
            [
                roll('Sadakichi', 38),
                roll('Moriko', 28),
                roll('Jimen', 25),
                roll('Tetsuro', 24),
                roll('Toshihiro', 19),
            ]
        )
        assert line == (
            'Sadakichi / Moriko / Jimen / Tetsuro / Toshihiro etiquette: 35 / 25 / 25 / 20 / 15'
        )

    def test_orders_highest_first(self) -> None:
        line = render_open([roll('Low', 15), roll('High', 40, 'commerce')][:1] + [roll('High', 38)])
        assert line.startswith('High / Low')

    def test_unattributed_rolls_are_left_out(self) -> None:
        line = render_open([roll('Jimen', 38), roll('', 25)])
        assert line == 'Jimen etiquette: 35'

    def test_nothing_to_render_is_an_error(self) -> None:
        with pytest.raises(ValueError, match='no attributed rolls'):
            render_open([roll('', 25)])

    def test_one_line_holds_one_skill(self) -> None:
        with pytest.raises(ValueError, match='one line holds one skill'):
            render_open([roll('Jimen', 38), roll('Tetsuro', 25, 'sincerity')])


class TestPersonalName:
    """*"use personal names without the family names"*, GM 2026-09-02."""

    @pytest.mark.parametrize(
        ('full', 'written'),
        [
            ('Tsuruchi Tetsuro', 'Tetsuro'),
            ('Kitsune Moriko', 'Moriko'),
            # The compound form: family, the particle, the domain, then the name.
            ('Hida no Reiji Kazuma', 'Kazuma'),
            # Already one word - a monk, a peasant, an NPC the GM entered short.
            ('Otsuki', 'Otsuki'),
            ('  Tsuruchi   Jimen  ', 'Jimen'),
            ('', ''),
        ],
    )
    def test_the_last_token_is_what_gets_written(self, full: str, written: str) -> None:
        assert personal_name(full) == written


class TestFamilyNamesAreNotWrittenDown:
    """The GM's own before/after (2026-09-02): a party out of one family repeats it
    until the names it is meant to distinguish are the shortest part of the line."""

    def test_the_gms_own_line_loses_four_tsuruchis(self) -> None:
        line = render_open(
            [
                roll('Tsuruchi Tetsuro', 30),
                roll('Tsuruchi Toshihiro', 24),
                roll('Tsuruchi Sadakichi', 20),
                roll('Tsuruchi Jimen', 19),
                roll('Kitsune Moriko', 15),
            ]
        )
        assert line == (
            'Tetsuro / Toshihiro / Sadakichi / Jimen / Moriko etiquette: 30 / 20 / 20 / 15 / 15'
        )

    def test_a_contest_strips_both_sides_and_the_winner(self) -> None:
        scored = contest(
            roll('Tsuruchi Jimen', 41, 'sincerity'), roll('Bayushi Otsuki', 28, 'sincerity')
        )
        assert render_contest(scored) == 'Jimen vs Otsuki sincerity: 41 vs 28, Jimen wins by >=10'


class TestContestedPairs:
    """GM 2026-09-02: six skills never contest themselves, and one side takes a tie."""

    @pytest.mark.parametrize(
        ('skill', 'opposed'),
        [
            ('interrogation', 'sincerity'),
            ('sincerity', 'interrogation'),
            ('manipulation', 'tact'),
            ('tact', 'manipulation'),
            ('investigation', 'sneaking'),
            ('sneaking', 'investigation'),
        ],
    )
    def test_the_six_are_paired_both_ways(self, skill: str, opposed: str) -> None:
        assert opposing_skill(skill) == opposed

    def test_every_other_skill_contests_itself(self) -> None:
        """*"you may always assume that the NPC rolled the same skill that the
        player character did"* - the default, and much the commoner case."""
        for skill in ('precepts', 'law', 'etiquette', 'commerce', 'bragging', 'strategy'):
            assert opposing_skill(skill) == skill, skill

    def test_the_lookup_is_case_insensitive(self) -> None:
        assert opposing_skill('Sincerity') == 'interrogation'
        assert opposing_skill('Precepts') == 'precepts'

    def test_the_pairing_table_is_derived_not_hand_mirrored(self) -> None:
        """A fourth pairing must be ONE row in CONTESTED_PAIRS and nothing else."""
        for winner, loser in CONTESTED_PAIRS:
            assert OPPOSING_SKILL[winner] == loser
            assert OPPOSING_SKILL[loser] == winner
        assert len(OPPOSING_SKILL) == 2 * len(CONTESTED_PAIRS)

    def test_all_six_are_real_skills_in_the_rules(self) -> None:
        """Guard against a typo, or a rename in the rules leaving us pointing at air."""
        vocabulary = load_skills()
        for pair in CONTESTED_PAIRS:
            for skill in pair:
                assert skill in vocabulary, f'{skill} is not a skill in {RULES_PATH}'


class TestTieBreaks:
    @pytest.mark.parametrize(
        ('mine', 'theirs', 'side'),
        [
            # *"an interrogation roll succeeds when it ties the sincerity roll"*
            ('interrogation', 'sincerity', 'mine'),
            ('sincerity', 'interrogation', 'theirs'),
            # Corroborated by the rules: manipulation's result table opens at a
            # delta of `0 - 9` (rules/02-skills.md:247), so nothing-between-them is
            # already a manipulator success.
            ('manipulation', 'tact', 'mine'),
            ('tact', 'manipulation', 'theirs'),
            # *"both investigation and sneaking are basic skills, in the case of a
            # tie, investigation wins rather than sneaking winning"*
            ('investigation', 'sneaking', 'mine'),
            ('sneaking', 'investigation', 'theirs'),
        ],
    )
    def test_the_named_side_takes_the_tie(self, mine: str, theirs: str, side: str) -> None:
        assert contested_winner(mine, theirs, 30, 30) == side

    def test_a_skill_against_itself_is_a_real_tie(self) -> None:
        """*"when the same skill contests itself, as in the case of two different
        people rolling precepts, then it is a tie."*"""
        assert contested_winner('precepts', 'precepts', 30, 30) is None

    def test_the_tie_rule_only_applies_to_ties(self) -> None:
        assert contested_winner('sincerity', 'interrogation', 31, 30) == 'mine'
        assert contested_winner('interrogation', 'sincerity', 30, 31) == 'theirs'

    def test_a_mismatched_pair_falls_back_to_a_tie(self) -> None:
        """The pairing rule says this cannot happen; if it does, do not award a win
        to whichever side the half-matching rule happens to name first."""
        assert contested_winner('sincerity', 'law', 30, 30) is None

    def test_a_tie_break_is_scored_as_a_win_in_the_smallest_band(self) -> None:
        scored = contest(roll('Jimen', 30, 'interrogation'), roll('Otsuki', 30, 'sincerity'))
        assert not scored.tied
        assert scored.winner == 'Jimen'
        assert scored.margin == 0
        assert render_contest(scored) == (
            'Jimen vs Otsuki interrogation vs sincerity: 30 vs 30, Jimen wins by <5'
        )

    def test_the_same_skill_still_ties_through_contest(self) -> None:
        scored = contest(roll('Jimen', 30, 'precepts'), roll('Otsuki', 30, 'precepts'))
        assert scored.tied
        assert render_contest(scored) == 'Jimen vs Otsuki precepts: 30 vs 30, tied'


class TestSkillsText:
    def test_one_name_when_both_sides_rolled_the_same_skill(self) -> None:
        assert skills_text('precepts', 'precepts') == 'precepts'

    def test_both_names_when_they_differ(self) -> None:
        """A tie-break is a bare contradiction unless the reader can see the skills:
        `30 vs 30, Otsuki wins` only makes sense beside `sincerity vs interrogation`."""
        assert skills_text('sincerity', 'interrogation') == 'sincerity vs interrogation'


class TestRenderContest:
    def test_names_both_totals_the_winner_and_the_margin(self) -> None:
        scored = contest(roll('Jimen', 41, 'sincerity'), roll('Otsuki', 28, 'sincerity'))
        assert render_contest(scored) == 'Jimen vs Otsuki sincerity: 41 vs 28, Jimen wins by >=10'

    def test_a_tie_says_so(self) -> None:
        scored = contest(roll('Jimen', 30, 'sincerity'), roll('Otsuki', 30, 'sincerity'))
        assert render_contest(scored) == 'Jimen vs Otsuki sincerity: 30 vs 30, tied'


class TestMarginBands:
    """The GM's break points (2026-08-29), replacing "round the margin down to 5".

    A win by 2 used to record as "by 0", which reads as no victory at all. The GM:
    "we round to five for low numbers, but then when it comes to higher amounts, we
    start doing increments of ten... you beat him by at least ten, or at least
    twenty."
    """

    @pytest.mark.parametrize(
        ('margin', 'expected'),
        [
            (0, '<5'),
            (1, '<5'),
            (4, '<5'),
            (5, '<10'),
            (9, '<10'),
            (10, '>=10'),
            (19, '>=10'),
            (20, '>=20'),
            (29, '>=20'),
            (30, '>=30'),
            (45, '>=40'),
        ],
    )
    def test_bands(self, margin: int, expected: str) -> None:
        assert margin_text(margin) == expected

    def test_a_narrow_win_is_still_a_win(self) -> None:
        assert margin_text(2) == '<5', 'never "by 0" - that reads as no victory'
