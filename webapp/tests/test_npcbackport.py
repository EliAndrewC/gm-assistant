"""Feature 226: a character-sheet NPC's built stats, written back to Obsidian Portal."""

from __future__ import annotations

from typing import Any

import pytest

from l7r import npcbackport as bp
from l7r.repl.rolls import npcnumbers

# A real record's GM-only notes, trimmed (Bayushi no Daika Koharu, OP cache 2026-10-25):
# prose before, the block, a hidden-rolls block after, CRLF line ends as OP sends them.
KOHARU_NOTES = (
    'The two monks are his spiritual team in case an accusation is made in the wood.\r\n'
    '\r\n'
    'NPC numbers:\r\n'
    '- Air 4\r\n'
    '- Water 3\r\n'
    '- sincerity 1\r\n'
    '- heraldry 3\r\n'
    '- tact 2\r\n'
    '\r\n'
    'Hidden rolls:\r\n'
    '- 2026-09-22 sincerity 25 - bringing more monks along: Shizukanaken 49@3 +10 DETECTED'
)

ROSTER = [
    {'id': '1', 'name': 'Bayushi no Daika Koharu', 'character_url': 'https://op/koharu'},
    {'id': '2', 'name': 'Bayushi no Daika Fukushin', 'character_url': 'https://op/fukushin'},
    {'id': '3', 'name': 'Tsuruchi Kyoma', 'character_url': 'https://op/kyoma'},
]


class Portal:
    def __init__(self, notes: str = KOHARU_NOTES, *, reachable: bool = True) -> None:
        self.notes = notes
        self.reachable = reachable
        self.writes: list[dict[str, Any]] = []

    def get_body(self, char_id: str) -> dict[str, Any] | None:
        return {'game_master_info': self.notes} if self.reachable else None

    def update(self, char_id: str, **fields: Any) -> None:
        self.writes.append({'id': char_id, **fields})
        self.notes = fields['game_master_info']

    def backport(
        self, name: str, stats: dict[str, object], roster: list[Any] = ROSTER
    ) -> dict[str, Any]:
        return bp.backport(
            name, stats, characters=lambda: roster, get_body=self.get_body, update=self.update
        )


KOHARU_BUILD: dict[str, object] = {
    'Air': 4,
    'Earth': 3,
    'Fire': 2,
    'Water': 3,
    'Void': 3,
    'attack': 2,
    'parry': 3,
    'sincerity': 1,
    'tact': 2,
    'double_attack': 1,
}


class TestNormalize:
    def test_ids_become_block_names(self) -> None:
        assert bp.normalize({'Air': 3, 'double_attack': 2, ' Tact ': 1}) == (
            {'air': 3, 'double attack': 2, 'tact': 1},
            [],
        )

    def test_a_name_the_block_cannot_hold_is_refused_by_name(self) -> None:
        assert bp.normalize({'air': 3, "kakita's 5th": 1, '2nd dan': 1}) == (
            {'air': 3},
            ["kakita's 5th", '2nd dan'],
        )

    @pytest.mark.parametrize('value', [-1, 7, 2.5, '3', True, None])
    def test_a_bad_value_is_a_broken_request(self, value: object) -> None:
        with pytest.raises(ValueError, match='Air must be a whole number from 0 to 6'):
            bp.normalize({'Air': value})


class TestMerge:
    def test_sent_wins_both_ways_and_unsent_lines_stay(self) -> None:
        m = bp.merge({'air': 4, 'heraldry': 3, 'tact': 2}, {'air': 3, 'tact': 2, 'earth': 4})
        assert m.numbers == {'air': 3, 'heraldry': 3, 'tact': 2, 'earth': 4}
        assert (m.added, m.changed, m.unchanged) == (['earth'], {'air': (4, 3)}, ['tact'])


class TestBackport:
    def test_a_new_npcs_build_lands_in_the_block(self) -> None:
        op = Portal()
        answer = op.backport('Bayushi no Daika Koharu', KOHARU_BUILD)
        assert answer['status'] == 'written'
        assert answer['record'] == {'name': 'Bayushi no Daika Koharu', 'url': 'https://op/koharu'}
        assert answer['added'] == {
            'earth': 3,
            'fire': 2,
            'void': 3,
            'attack': 2,
            'parry': 3,
            'double attack': 1,
        }
        assert answer['changed'] == {}
        assert sorted(answer['unchanged']) == ['air', 'sincerity', 'tact', 'water']
        assert answer['message'] == (
            'Bayushi no Daika Koharu: added Earth 3, Fire 2, Void 3, attack 2, parry 3, '
            'double attack 1; 4 unchanged'
        )
        assert len(op.writes) == 1
        assert npcnumbers.parse(op.notes) == {
            'air': 4,
            'water': 3,
            'sincerity': 1,
            'heraldry': 3,
            'tact': 2,
            'earth': 3,
            'fire': 2,
            'void': 3,
            'attack': 2,
            'parry': 3,
            'double attack': 1,
        }

    def test_nothing_outside_the_block_moves(self) -> None:
        op = Portal()
        op.backport('Koharu', KOHARU_BUILD)
        before, _, _ = KOHARU_NOTES.replace('\r\n', '\n').partition('NPC numbers:')
        after_block = KOHARU_NOTES.replace('\r\n', '\n').partition('\n\nHidden rolls:')[2]
        assert op.notes.startswith(before + 'NPC numbers:\n- Air 4\n- Earth 3\n- Fire 2\n')
        assert op.notes.endswith('\n- double attack 1\n\nHidden rolls:' + after_block)

    def test_a_record_with_no_block_gets_one_at_the_end(self) -> None:
        op = Portal('Honor: 3.0\r\n\r\nLikes plum wine.')
        op.backport('Kyoma', {'Air': 4, 'sincerity': 3})
        assert op.notes == 'Honor: 3.0\n\nLikes plum wine.\n\nNPC numbers:\n- Air 4\n- sincerity 3'

    def test_the_same_numbers_again_write_nothing(self) -> None:
        op = Portal()
        answer = op.backport('Koharu', {'Air': 4, 'tact': 2})
        assert answer['status'] == 'unchanged'
        assert (
            answer['message']
            == 'Bayushi no Daika Koharu: Obsidian Portal already has these numbers'
        )
        assert op.writes == []

    def test_a_raise_and_a_lowering_are_both_written(self) -> None:
        op = Portal()
        answer = op.backport('Koharu', {'Air': 5, 'Water': 2})
        assert answer['changed'] == {'air': [4, 5], 'water': [3, 2]}
        assert answer['message'] == 'Bayushi no Daika Koharu: Air 4 -> 5, Water 3 -> 2'
        assert npcnumbers.parse(op.notes)['air'] == 5
        assert npcnumbers.parse(op.notes)['water'] == 2

    def test_a_hand_written_line_the_sheet_did_not_send_stays(self) -> None:
        op = Portal()
        op.backport('Koharu', KOHARU_BUILD)
        assert '- heraldry 3' in op.notes

    def test_a_refused_name_is_reported_and_the_rest_written(self) -> None:
        op = Portal()
        answer = op.backport('Koharu', {'Earth': 3, '5th dan': 1})
        assert answer['refused'] == ['5th dan']
        assert answer['added'] == {'earth': 3}

    def test_no_record_writes_nothing(self) -> None:
        op = Portal()
        answer = op.backport('Bandit Leader', {'Air': 3})
        assert answer['status'] == 'no_record'
        assert answer['message'] == 'no Obsidian Portal record for Bandit Leader; nothing written'
        assert len(answer['nearest']) == 3
        assert op.writes == []

    def test_an_ambiguous_name_writes_nothing(self) -> None:
        op = Portal()
        answer = op.backport('Bayushi no Daika', {'Air': 3})
        assert answer['status'] == 'ambiguous'
        assert answer['candidates'] == ['Bayushi no Daika Koharu', 'Bayushi no Daika Fukushin']
        assert op.writes == []

    def test_an_unreachable_roster_is_a_failure_not_no_record(self) -> None:
        answer = Portal().backport('Koharu', {'Air': 3}, roster=[])
        assert answer['status'] == 'failed'
        assert 'nothing written' in answer['message']

    def test_an_unreadable_record_is_a_failure(self) -> None:
        op = Portal(reachable=False)
        answer = op.backport('Koharu', {'Air': 3})
        assert answer['status'] == 'failed'
        assert (
            answer['message']
            == 'Bayushi no Daika Koharu: could not read the record; nothing written'
        )

    def test_a_rejected_write_is_a_failure(self) -> None:
        op = Portal()

        def refuse(char_id: str, **fields: Any) -> None:
            raise RuntimeError('422 from Obsidian Portal')

        answer = bp.backport(
            'Koharu', {'Earth': 3}, characters=lambda: ROSTER, get_body=op.get_body, update=refuse
        )
        assert answer['status'] == 'failed'
        assert (
            answer['message']
            == 'Bayushi no Daika Koharu: 422 from Obsidian Portal; nothing written'
        )
