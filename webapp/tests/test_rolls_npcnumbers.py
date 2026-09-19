"""Feature 207: an NPC's rings and ranks, read off the GM's rolls and remembered."""

from __future__ import annotations

from pathlib import Path

from l7r.repl.rolls import npcnumbers as nn
from l7r.repl.rolls.skills import load_skills

NOTES = 'XP: 65\r\nHonor: 3.0\r\n\r\nUnconventional'


class TestBlock:
    def test_no_block_parses_to_nothing(self) -> None:
        assert nn.parse(NOTES) == {}

    def test_round_trip(self) -> None:
        text = nn.render(NOTES, {'tact': 2, 'air': 3, 'sincerity': 5})
        assert text.endswith('NPC numbers:\n- Air 3\n- tact 2\n- sincerity 5')
        assert nn.parse(text) == {'air': 3, 'tact': 2, 'sincerity': 5}

    def test_rings_lead_in_rules_order(self) -> None:
        text = nn.render('', {'water': 2, 'tact': 1, 'air': 3})
        assert text == 'NPC numbers:\n- Air 3\n- Water 2\n- tact 1'

    def test_an_existing_block_is_replaced_in_place(self) -> None:
        first = nn.render(NOTES, {'air': 3}) + '\n\nA later paragraph.'
        second = nn.render(first, {'air': 4, 'tact': 2})
        assert second.count('NPC numbers:') == 1
        assert '- Air 4\n- tact 2\n\nA later paragraph.' in second
        assert 'Honor: 3.0' in second

    def test_nothing_to_write_leaves_the_notes_alone(self) -> None:
        assert nn.render(NOTES, {}) == NOTES

    def test_a_hand_edited_line_is_skipped_not_fatal(self) -> None:
        text = 'NPC numbers:\n- Air 3\n- tact: two\n- law 1'
        assert nn.parse(text) == {'air': 3, 'law': 1}

    def test_trailing_blank_lines_are_not_stacked(self) -> None:
        assert nn.render('Honor: 3.0\n\n\n', {'air': 3}) == 'Honor: 3.0\n\nNPC numbers:\n- Air 3'


class TestSchools:
    def test_the_two_sincerity_schools_come_from_the_rules(self) -> None:
        table = nn.school_extra_dice(load_skills())
        assert {s for s, skills in table.items() if 'sincerity' in skills} == {
            'merchant',
            'shosuro actor',
        }

    def test_only_vocabulary_words_survive(self) -> None:
        table = nn.school_extra_dice(load_skills())
        assert table['merchant'] == frozenset({'interrogation', 'sincerity'})
        assert all('wound checks' not in skills for skills in table.values())

    def test_a_non_pc_school_is_read_too(self) -> None:
        assert 'commerce' in nn.school_extra_dice(load_skills())['suzume overseer']

    def test_a_missing_file_and_a_school_with_no_line(self, tmp_path: Path) -> None:
        rules = tmp_path / 'schools.md'
        rules.write_text(
            '## Plain\n\nNothing.\n\n## Chooser\n\nRoll one extra die on any three types of rolls.\n'
            '\n## Talker\n\nRoll one extra die on tact and wound checks.\n'
        )
        table = nn.school_extra_dice(('tact',), (rules, tmp_path / 'absent.md'))
        assert table == {'talker': frozenset({'tact'})}

    def test_a_school_is_found_in_a_tag_or_a_whole_line(self) -> None:
        schools = ('merchant', 'shosuro actor')
        assert nn.find_schools({'tags': ['Wasp Clan', 'Merchant']}, schools) == ('merchant',)
        assert nn.find_schools(
            {'description': 'male\r\n\r\nShosuro Actor School\r\nRank: 3'}, schools
        ) == ('shosuro actor',)
        assert nn.find_schools({'game_master_info': 'XP: 65\nmerchant'}, schools) == ('merchant',)

    def test_a_word_inside_prose_is_not_a_school(self) -> None:
        record = {'description': 'He was once a merchant in Ryoko Owari.', 'tags': None}
        assert nn.find_schools(record, ('merchant',)) == ()


class TestInfer:
    def test_the_gm_s_example(self) -> None:
        reading = nn.infer((5, 3), 'Tact', 'Air')
        assert (reading.skill, reading.ring_name, reading.ring, reading.rank) == ('tact', 'air', 3, 2)

    def test_a_school_die_comes_off_the_rank(self) -> None:
        assert nn.infer((8, 3), 'sincerity', 'air', extra_dice=1).rank == 4
        assert nn.infer((8, 3), 'sincerity', 'air').rank == 5

    def test_a_declared_void_point_comes_off_both(self) -> None:
        reading = nn.infer((6, 4), 'tact', 'air', void_points=1)
        assert (reading.ring, reading.rank) == (3, 2)

    def test_rank_never_goes_negative(self) -> None:
        assert nn.infer((3, 3), 'tact', 'air', extra_dice=1).rank == 0


class TestCompare:
    def test_nothing_recorded_is_no_disagreement(self) -> None:
        assert nn.compare({}, nn.infer((5, 3), 'tact', 'air')) is None

    def test_agreement(self) -> None:
        assert nn.compare({'air': 3, 'tact': 2}, nn.infer((5, 3), 'tact', 'air')) is None

    def test_a_rank_disagreement(self) -> None:
        found = nn.compare({'air': 3, 'tact': 2}, nn.infer((6, 3), 'tact', 'air'))
        assert found is not None
        assert found.describe == 'tact 2 recorded, this roll says 3'
        assert found.void_answer == ''

    def test_one_die_up_in_both_offers_this_roll_s_void_point(self) -> None:
        found = nn.compare({'air': 3, 'tact': 2}, nn.infer((6, 4), 'tact', 'air'))
        assert found is not None
        assert found.describe == 'Air 3 recorded, this roll says 4'
        assert found.void_answer == 'This roll spent a void point'

    def test_two_dice_down_offers_the_previous_roll_s_void_points(self) -> None:
        found = nn.compare({'air': 5, 'tact': 2}, nn.infer((5, 3), 'tact', 'air'))
        assert found is not None
        assert found.void_answer == 'The previous roll spent 2 void points'
        assert found.void_points == -2

    def test_three_dice_is_not_a_void_point(self) -> None:
        found = nn.compare({'air': 3, 'tact': 2}, nn.infer((8, 6), 'tact', 'air'))
        assert found is not None and found.void_answer == ''

    def test_both_differing_is_not_a_void_point(self) -> None:
        found = nn.compare({'air': 3, 'tact': 2}, nn.infer((5, 4), 'tact', 'air'))
        assert found is not None
        assert found.void_answer == ''
        assert found.describe == (
            'Air 3 recorded, this roll says 4; tact 2 recorded, this roll says 1'
        )

    def test_a_ring_alone_on_record_can_still_offer_the_void_point(self) -> None:
        found = nn.compare({'air': 3}, nn.infer((6, 4), 'sincerity', 'air'))
        assert found is not None and found.void_points == 1


class TestRecording:
    def test_fill_adds_only_what_was_missing(self) -> None:
        numbers = {'air': 3}
        assert nn.fill(numbers, nn.infer((5, 3), 'tact', 'air')) == ['tact 2']
        assert numbers == {'air': 3, 'tact': 2}
        assert nn.fill(numbers, nn.infer((5, 3), 'tact', 'air')) == []

    def test_fill_names_a_new_ring_capitalized(self) -> None:
        assert nn.fill({}, nn.infer((5, 3), 'law', 'water')) == ['Water 3', 'law 2']

    def test_accept_overwrites(self) -> None:
        numbers = {'air': 3, 'tact': 2}
        nn.accept(numbers, nn.infer((7, 4), 'tact', 'air'))
        assert numbers == {'air': 4, 'tact': 3}


class TestAutomaticRaises:
    def test_acting_helps_sincerity_and_intimidation_only(self) -> None:
        numbers = {'acting': 2}
        assert nn.automatic_raises('Sincerity', numbers) == [('acting', 2, 10)]
        assert nn.automatic_raises('intimidation', numbers) == [('acting', 2, 10)]
        assert nn.automatic_raises('sneaking', numbers) == []

    def test_history_helps_culture_law_and_strategy_never_heraldry(self) -> None:
        numbers = {'history': 3}
        for skill in ('culture', 'law', 'strategy'):
            assert nn.automatic_raises(skill, numbers) == [('history', 3, 15)], skill
        assert nn.automatic_raises('heraldry', numbers) == []

    def test_no_rank_no_raise(self) -> None:
        assert nn.automatic_raises('sincerity', {'acting': 0}) == []
        assert nn.automatic_raises('sincerity', {}) == []

    def test_the_recorded_only_skills_are_the_ones_that_give_raises(self) -> None:
        assert nn.RECORD_ONLY == ('acting', 'history')
