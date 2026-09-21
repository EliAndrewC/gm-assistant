"""Feature 212: `/discern-honor` - decided at open, served by lookup, recorded on use.

Nothing here touches the character-sheet app or Obsidian Portal: `FakeSheet` is the
sheet app's conversation store as its status block describes it (a re-sent open id
keeps every existing entry), and `FakeOP` is one NPC's GM-only notes.
"""

from __future__ import annotations

import io
import json
import urllib.error
import urllib.request
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from l7r.repl import honor
from l7r.repl.honor import Record
from l7r.repl.rolls import conversation as conv
from l7r.repl.rolls import discern, sheet

OPENED = datetime(2026, 9, 21, 23, 10, tzinfo=UTC)
CAST: list[dict[str, object]] = [
    {'id': 'otsuki-id', 'name': 'Otsuki', 'character_url': 'https://op/otsuki'},
    {'id': 'sakura-id', 'name': 'Hida no Reiji Sakura', 'character_url': 'https://op/sakura'},
]
NOTES = 'XP: 65\nHonor: 3.0\n'
HOLDERS = (
    sheet.KnackHolder(3, 'Tsuruchi Jimen', 2, 4),
    sheet.KnackHolder(18, 'Tsuruchi Tetsuro', 2, 4),
    sheet.KnackHolder(16, 'Tsuruchi Makoto 鶴知誠', 1, 4),
)


@pytest.fixture(autouse=True)
def closed() -> Any:
    conv._open = None
    yield
    conv.stop_watching()
    conv._open = None


class FakeOP:
    def __init__(self, gm_info: str = NOTES, reachable: bool = True) -> None:
        self.gm_info = gm_info
        self.reachable = reachable
        self.writes = 0

    def get_body(self, cid: str) -> Mapping[str, object] | None:
        return {'game_master_info': self.gm_info, 'bio': ''} if self.reachable else None

    def update(self, cid: str, **fields: Any) -> None:
        self.writes += 1
        self.gm_info = fields['game_master_info']


class FakeSheet:
    """One open conversation per group; a re-`PUT` of the open id freezes entries."""

    def __init__(self) -> None:
        self.open: dict[int, dict[str, Any]] = {}
        self.puts: list[dict[str, Any]] = []
        self.deleted: list[str] = []
        self.fail_get = ''
        self.fail_put = ''
        self.fail_delete = ''

    def get(self, group: int) -> sheet.ConversationResult:
        if self.fail_get:
            return sheet.ConversationResult(reason=self.fail_get)
        return sheet.ConversationResult(conversation=self.open.get(group))

    def put(self, body: Mapping[str, Any]) -> sheet.ConversationResult:
        self.puts.append(json.loads(json.dumps(body)))
        if self.fail_put:
            return sheet.ConversationResult(reason=self.fail_put)
        group = int(body['group'])
        old = self.open.get(group)
        entries = [dict(e, asked_at=None) for e in body['discern_honor']]
        if old is not None and old['conversation_id'] == body['conversation_id']:
            kept = {e['character_id']: e for e in old['discern_honor']}
            entries = [kept.get(e['character_id'], e) for e in entries]
        self.open[group] = {**body, 'discern_honor': entries}
        return sheet.ConversationResult(conversation=self.open[group])

    def delete(self, conversation_id: str) -> sheet.ConversationResult:
        self.deleted.append(conversation_id)
        if self.fail_delete:
            return sheet.ConversationResult(reason=self.fail_delete)
        self.open = {g: c for g, c in self.open.items() if c['conversation_id'] != conversation_id}
        return sheet.ConversationResult()

    def ask(self, character_id: int) -> float:
        """What `/discern-honor` does: a lookup that stamps `asked_at` ONCE."""
        for body in self.open.values():
            for entry in body['discern_honor']:
                if entry['character_id'] == character_id:
                    entry['asked_at'] = entry['asked_at'] or '2026-09-21T23:20:00Z'
                    return float(entry['told'])
        raise AssertionError('no conversation serves that character')


def begin(
    op: FakeOP,
    app: FakeSheet,
    *,
    dice: tuple[int, ...] = (8, 3, 5),
    new: bool = False,
    holders: sheet.HoldersResult | None = None,
    nonce: str = '7f3a',
) -> Any:
    rolls = iter(dice)

    def opener(opened: Any, **kwargs: Any) -> None:
        discern.open_(
            opened,
            holders=lambda: holders or sheet.HoldersResult(holders=HOLDERS),
            get_conversation=app.get,
            put=app.put,
            roll=lambda: next(rolls),
            mint=lambda now: discern.mint_id(now, lambda: nonce),
            **kwargs,
        )

    return conv.begin_conversation(
        'Otsuki',
        characters=lambda: CAST,
        now=lambda: OPENED,
        watch=False,
        get_body=op.get_body,
        new=new,
        discern_open=opener,
    )


def tick(opened: Any, op: FakeOP, app: FakeSheet) -> bool:
    return conv._tick(
        opened,
        collector=lambda c: c,
        get_body=op.get_body,
        update=op.update,
        get_conversation=app.get,
        announce=False,
    )


class TestRecordLine:
    def test_every_written_line_parses(self) -> None:
        """FR-006: `parse_records` silently drops what `_LINE_RE` cannot match, so
        every shape the writer can produce is checked against the pattern."""
        shapes = [
            Record('Jimen', 2, 4.5, 1),
            Record('Jimen', 2, 3.0, 4, locked=True),
            Record('Jimen', 2, 4.5, 1, last='c-20260921-7f3a'),
            Record('Jimen', 2, 4.3, 2, last='c-20260921-7f3a', was=4.5),
            Record('Jimen', 2, 3.0, 4, locked=True, last='c-20260921-7f3a', was=3.2),
            Record('Jimen', 2, -0.5, 1, last='c-20260921-7f3a', was=-1.0),
        ]
        for record in shapes:
            text = honor.render('', {'jimen': record})
            assert honor.parse_records(text) == {'jimen': record}, record.line()

    def test_the_pinned_format(self) -> None:
        line = Record('Jimen', 2, 4.3, 2, last='c-20260921-7f3a', was=4.5).line()
        assert line == '- Jimen (rank 2): told 4.3 after 2 conversations [c-20260921-7f3a, was 4.5]'
        first = Record('Jimen', 2, 4.5, 1, last='c-20260921-7f3a').line()
        assert first.endswith('after 1 conversation [c-20260921-7f3a, first]')

    def test_a_line_from_before_the_feature_still_reads(self) -> None:
        old = f'{honor.HEADING}\n- Jimen (rank 2): told 4.5 after 1 conversation\n'
        assert honor.parse_records(old) == {'jimen': Record('Jimen', 2, 4.5, 1)}


class TestAdvanceWithMarker:
    def test_the_same_conversation_advances_once(self) -> None:
        first = honor.advance(None, 'Jimen', 3.0, 2, 8, marker='c-1')
        assert first == Record('Jimen', 2, 4.5, 1, last='c-1')
        assert honor.advance(first, 'Jimen', 3.0, 2, 1, marker='c-1') is first

    def test_a_new_conversation_advances_again_and_remembers_what_was(self) -> None:
        first = Record('Jimen', 2, 4.5, 1, last='c-1')
        second = honor.advance(first, 'Jimen', 3.0, None, 1, marker='c-2')
        assert second == Record('Jimen', 2, 4.3, 2, last='c-2', was=4.5)

    def test_outside_a_conversation_nothing_is_marked_and_nothing_is_idempotent(self) -> None:
        marked = Record('Jimen', 2, 4.3, 2, last='c-2', was=4.5)
        once = honor.advance(marked, 'Jimen', 3.0, None, 1)
        assert once == Record('Jimen', 2, 4.1, 3)
        assert honor.advance(once, 'Jimen', 3.0, None, 1) == Record('Jimen', 2, 3.9, 4)

    def test_rollback(self) -> None:
        records = {
            'jimen': Record('Jimen', 2, 4.5, 1, last='c-2'),
            'tetsuro': Record('Tetsuro', 4, 3.0, 3, locked=True, last='c-2', was=3.2),
            'makoto': Record('Makoto', 4, 3.8, 1, last='c-1'),
            'kaede': Record('Kaede', 1, 3.0, 5, locked=True, last='c-2', was=3.0),
        }
        assert honor.rollback(records, 'c-2', 3.0) == {
            'tetsuro': Record('Tetsuro', 4, 3.2, 2),
            'makoto': records['makoto'],
            'kaede': Record('Kaede', 1, 3.0, 4, locked=True),
        }
        assert honor.rollback(records, '', 3.0) == records

    def test_the_die_does_not_reroll(self) -> None:
        assert all(1 <= honor.d10_flat() <= 10 for _ in range(200))


class TestNames:
    def test_ids(self) -> None:
        assert discern.mint_id(OPENED, lambda: '7f3a') == 'c-20260921-7f3a'
        assert discern.mint_id(OPENED).startswith('c-20260921-')
        assert discern.sheet_id('c-20260921-7f3a', 2) == 'c-20260921-7f3a-g2'
        assert discern.base_id('c-20260921-7f3a-g12') == 'c-20260921-7f3a'

    def test_given_name(self) -> None:
        assert discern.given_name('Tsuruchi Jimen') == 'Jimen'
        assert discern.given_name('Tsuruchi Makoto 鶴知誠') == 'Makoto'
        assert discern.given_name('Bayushi Kaede 鶴') == 'Kaede'
        assert discern.given_name(' 鶴知誠 ') == '鶴知誠'


class TestOpen:
    def test_decides_every_holder_and_writes_nothing(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        op, app = FakeOP(), FakeSheet()
        opened = begin(op, app)
        assert opened.conversation_id == 'c-20260921-7f3a'
        assert {e.pc: e.record.told for e in opened.discern.values()} == {
            'Jimen': 4.5,
            'Tetsuro': 2.0,
            'Makoto': 3.0,
        }
        assert op.writes == 0  # FR-002: opening is a preview
        assert opened.discern_groups == (1, 2)
        assert 'would tell Jimen 4.5, Tetsuro 2.0, Makoto 3.0' in capsys.readouterr().out

    def test_only_told_values_leave(self) -> None:
        """SC-003 / FR-003, over the SERIALIZED payload: nothing that could be a true
        Honor, a die, a count, a lock or a name crosses to the sheet app."""
        op, app = FakeOP('Honor: 3.7\n'), FakeSheet()
        begin(op, app, dice=(8, 3, 9))  # nobody's die is the 5 that reads true
        assert len(app.puts) == 2
        for body in app.puts:
            assert sorted(body) == [
                'conversation_id',
                'discern_honor',
                'group',
                'npc_ref',
                'opened_at',
            ]
            for entry in body['discern_honor']:
                assert sorted(entry) == ['character_id', 'told']
            wire = json.dumps(body)
            assert '3.7' not in wire
            assert 'Otsuki' not in wire
        assert app.puts[1] == {
            'conversation_id': 'c-20260921-7f3a-g2',
            'group': 2,
            'npc_ref': 'otsuki-id',
            'opened_at': '2026-09-21T23:10:00+00:00',
            'discern_honor': [{'character_id': 3, 'told': 5.2}, {'character_id': 18, 'told': 2.7}],
        }

    def test_a_later_conversation_refines_and_needs_no_die(self) -> None:
        op = FakeOP(NOTES + f'\n{honor.HEADING}\n- Jimen (rank 2): told 4.5 after 1 conversation\n')
        opened = begin(op, FakeSheet(), dice=(1, 1))
        jimen = opened.discern[3].record
        assert jimen == Record('Jimen', 4, 4.1, 2, last='c-20260921-7f3a', was=4.5)

    @pytest.mark.parametrize(
        ('op', 'holders', 'expected'),
        [
            (FakeOP(reachable=False), None, ''),
            (FakeOP('no honor here'), None, 'has no "Honor: X.Y" line'),
            (FakeOP(), sheet.HoldersResult(reason='the sheet is down'), 'the sheet is down'),
            (FakeOP(), sheet.HoldersResult(), ''),
        ],
    )
    def test_nothing_to_serve_still_opens(
        self,
        op: FakeOP,
        holders: sheet.HoldersResult | None,
        expected: str,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        app = FakeSheet()
        opened = begin(op, app, holders=holders)
        assert id(conv.current()) == id(opened)
        assert opened.discern == {}
        assert app.puts == []
        out = capsys.readouterr().out
        assert expected in out
        if not expected:
            assert 'Discern Honor' not in out

    def test_an_unreadable_sheet_conversation_still_opens(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        app = FakeSheet()
        app.fail_get = 'GM_WRITE_TOKEN is not set'
        opened = begin(FakeOP(), app)
        assert opened.discern == {}
        assert app.puts == []
        assert 'GM_WRITE_TOKEN is not set - /discern-honor will not answer' in (
            capsys.readouterr().out
        )

    def test_a_failed_push_keeps_the_manual_call_consistent(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        app = FakeSheet()
        app.fail_put = 'the app returned 500'
        opened = begin(FakeOP(), app)
        assert opened.discern_groups == ()
        assert opened.planned('jimen') is not None
        assert 'the app returned 500' in capsys.readouterr().out


class TestAskingTwice:
    def test_one_conversation_is_one_advance_however_often_it_is_asked(self) -> None:
        """The GM's semantic, end to end (SC-002)."""
        op, app = FakeOP(), FakeSheet()
        opened = begin(op, app)
        assert [app.ask(3) for _ in range(20)] == [4.5] * 20
        tick(opened, op, app)
        tick(opened, op, app)
        conv.end_conversation(
            get_body=op.get_body,
            update=op.update,
            collector=lambda c: c,
            get_conversation=app.get,
            close_sheet=app.delete,
        )
        assert honor.parse_records(op.gm_info) == {
            'jimen': Record('Jimen', 4, 4.5, 1, last='c-20260921-7f3a')
        }
        assert op.writes == 1
        assert app.open == {}
        assert len(app.deleted) == 2

    def test_nobody_asked_means_nothing_is_recorded(self) -> None:
        op, app = FakeOP(), FakeSheet()
        opened = begin(op, app)
        assert tick(opened, op, app) is False
        assert op.writes == 0
        assert op.gm_info == NOTES

    def test_the_next_conversation_moves_closer(self) -> None:
        op, app = FakeOP(), FakeSheet()
        first = begin(op, app)
        app.ask(3)
        tick(first, op, app)
        conv.end_conversation(
            get_body=op.get_body,
            update=op.update,
            collector=lambda c: c,
            get_conversation=app.get,
            close_sheet=app.delete,
        )
        second = begin(op, app, nonce='9c01')
        assert app.ask(3) == 4.1
        tick(second, op, app)
        assert honor.parse_records(op.gm_info)['jimen'] == Record(
            'Jimen', 4, 4.1, 2, last='c-20260921-9c01', was=4.5
        )

    def test_commit_survives_an_unreadable_record_and_tries_again(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        op, app = FakeOP(), FakeSheet()
        opened = begin(op, app)
        app.ask(3)
        op.reachable = False
        tick(opened, op, app)
        assert 'could not read Otsuki' in capsys.readouterr().out
        op.reachable = True
        tick(opened, op, app)
        assert 'jimen' in honor.parse_records(op.gm_info)

    def test_an_unreachable_app_complains_once(self, capsys: pytest.CaptureFixture[str]) -> None:
        op, app = FakeOP(), FakeSheet()
        opened = begin(op, app)
        capsys.readouterr()
        app.fail_get = 'could not reach the app'
        tick(opened, op, app)
        tick(opened, op, app)
        assert capsys.readouterr().out.count('could not reach the app') == 1
        app.fail_get = ''
        tick(opened, op, app)
        assert opened.discern_complained is False

    def test_a_conversation_somebody_else_replaced_is_ignored(self) -> None:
        op, app = FakeOP(), FakeSheet()
        opened = begin(op, app)
        app.open[2] = {
            'conversation_id': 'c-other-g2',
            'discern_honor': [
                {'character_id': 3, 'told': 1.0, 'asked_at': 'x'},
                {'character_id': 99, 'told': 1.0, 'asked_at': 'x'},
            ],
        }
        tick(opened, op, app)
        assert op.writes == 0
        app.open[2]['conversation_id'] = 'c-20260921-7f3a-g2'
        tick(opened, op, app)  # character 99 is nobody this side planned for
        assert list(honor.parse_records(op.gm_info)) == ['jimen']


class TestManualCall:
    def run(self, op: FakeOP, npc: str = 'Otsuki', pc: str = 'Jimen', **kw: Any) -> Record:
        return honor.discern_honor(
            npc,
            pc,
            characters=lambda: CAST,
            get_body=op.get_body,
            update=op.update,
            roll=lambda: 1,
            rank_lookup=lambda pc: 4,
            **kw,
        )

    def test_the_gm_sees_what_the_player_is_told_and_it_counts_once(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        op, app = FakeOP(), FakeSheet()
        opened = begin(op, app)
        assert self.run(op).told == 4.5  # the PLANNED value, not a fresh die of 1
        assert self.run(op).told == 4.5
        assert 'already been answered in this conversation: tell them 4.5 again' in (
            capsys.readouterr().out
        )
        assert app.ask(3) == 4.5
        tick(opened, op, app)
        assert op.writes == 1
        assert honor.parse_records(op.gm_info)['jimen'].conversations == 1

    def test_after_the_player_asked_it_is_still_the_same_answer(self) -> None:
        op, app = FakeOP(), FakeSheet()
        opened = begin(op, app)
        app.ask(3)
        tick(opened, op, app)
        assert self.run(op).told == 4.5
        assert op.writes == 1

    def test_a_pc_the_sheet_does_not_know_is_still_idempotent(self) -> None:
        op, app = FakeOP(), FakeSheet()
        begin(op, app)
        first = self.run(op, pc='Kaede', rank=2)
        assert first == Record('Kaede', 2, 1.0, 1, last='c-20260921-7f3a')
        assert self.run(op, pc='Kaede') is not None
        assert op.writes == 1

    def test_another_npc_behaves_as_it_always_has(self) -> None:
        """FR-007: a conversation open with Otsuki says nothing about Sakura."""
        op, app = FakeOP(), FakeSheet()
        begin(op, app)
        assert self.run(op, npc='Sakura') == Record('Jimen', 4, 1.0, 1)
        assert self.run(op, npc='Sakura') == Record('Jimen', 4, 1.4, 2)

    def test_with_nothing_open_one_call_is_one_conversation(self) -> None:
        op = FakeOP()
        assert self.run(op) == Record('Jimen', 4, 1.0, 1)
        assert self.run(op) == Record('Jimen', 4, 1.4, 2)


class TestAbandon:
    def abandon(self, op: FakeOP, app: FakeSheet) -> None:
        conv.abandon_conversation(
            get_body=op.get_body, update=op.update, get_conversation=app.get, close_sheet=app.delete
        )

    def test_the_record_goes_back_to_how_it_was(self, capsys: pytest.CaptureFixture[str]) -> None:
        before = NOTES + f'\n{honor.HEADING}\n- Jimen (rank 4): told 4.5 after 1 conversation'
        op, app = FakeOP(before), FakeSheet()
        opened = begin(op, app, dice=(3, 5))
        app.ask(3)
        tick(opened, op, app)
        assert 'told 4.1 after 2 conversations' in op.gm_info
        app.ask(18)  # asked after the last tick: only the final poll can know
        self.abandon(op, app)
        assert op.gm_info == before
        out = capsys.readouterr().out
        assert "Took this conversation's Discern Honor back off Otsuki's record." in out
        assert 'Jimen had already been told 4.1' in out
        assert 'Tetsuro had already been told 2.0' in out
        assert app.open == {}

    def test_nothing_asked_nothing_touched(self) -> None:
        op, app = FakeOP(), FakeSheet()
        begin(op, app)
        self.abandon(op, app)
        assert op.writes == 0
        assert app.open == {}

    def test_no_honor_line_means_nothing_to_undo(self) -> None:
        op, app = FakeOP('nothing'), FakeSheet()
        begin(op, app)
        self.abandon(op, app)
        assert op.writes == 0

    def test_an_unreadable_record_is_reported(self, capsys: pytest.CaptureFixture[str]) -> None:
        op, app = FakeOP(), FakeSheet()
        begin(op, app)
        app.ask(3)
        op.reachable = False
        self.abandon(op, app)
        assert 'could not read Otsuki to take Discern Honor back' in capsys.readouterr().out

    def test_a_failed_close_is_reported(self, capsys: pytest.CaptureFixture[str]) -> None:
        op, app = FakeOP(), FakeSheet()
        begin(op, app)
        app.fail_delete = 'the app returned 500'
        self.abandon(op, app)
        out = capsys.readouterr().out
        assert 'could not close the sheet conversation (the app returned 500)' in out
        assert 'will offer to resume it' in out


class TestResume:
    def test_a_restart_is_the_same_conversation(self, capsys: pytest.CaptureFixture[str]) -> None:
        """FR-011: the REPL dies after Jimen asked; nobody is counted twice and
        nobody's answer changes - including a first read that was never recorded."""
        op, app = FakeOP(), FakeSheet()
        first = begin(op, app, dice=(8, 3, 5))
        app.ask(3)
        tick(first, op, app)
        app.ask(18)  # told 2.0, and the REPL dies before the next poll
        conv._open = None
        capsys.readouterr()

        again = begin(op, app, dice=(10, 10), nonce='ffff')
        assert 'RESUMING the conversation opened at 23:10 UTC' in capsys.readouterr().out
        assert again.conversation_id == 'c-20260921-7f3a'
        assert again.discern[3].committed is True
        assert again.discern[18].record.told == 2.0  # the served value beat a die of 10
        assert app.ask(3) == 4.5
        assert app.ask(18) == 2.0
        tick(again, op, app)
        records = honor.parse_records(op.gm_info)
        assert records['jimen'].conversations == 1
        assert records['tetsuro'] == Record('Tetsuro', 4, 2.0, 1, last='c-20260921-7f3a')

    def test_new_forces_a_fresh_conversation(self, capsys: pytest.CaptureFixture[str]) -> None:
        op, app = FakeOP(), FakeSheet()
        first = begin(op, app)
        app.ask(3)
        tick(first, op, app)
        conv._open = None
        capsys.readouterr()
        again = begin(op, app, new=True, nonce='9c01')
        out = capsys.readouterr().out
        assert 'RESUMING' not in out
        assert 'replacing an unclosed conversation in which sheet character(s) 3 had asked' in out
        assert again.conversation_id == 'c-20260921-9c01'
        assert app.ask(3) == 4.1

    def test_an_unclosed_conversation_with_somebody_else_is_replaced(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        op, app = FakeOP(), FakeSheet()
        app.open[2] = {'conversation_id': 'c-old-g2', 'npc_ref': 'sakura-id', 'discern_honor': []}
        again = begin(op, app)
        assert again.conversation_id == 'c-20260921-7f3a'
        assert 'Discern Honor: re' not in capsys.readouterr().out.replace('RESUMING', '')


class TestSheetClient:
    PAYLOAD = {
        'characters': [
            {
                'id': 3,
                'name': 'Tsuruchi Jimen',
                'gaming_group_id': 2,
                'knacks': {'discern_honor': 4},
            },
            {
                'id': 4,
                'name': 'Tsuruchi Yabane',
                'gaming_group_id': None,
                'knacks': {'discern_honor': 4},
            },
            {'id': 5, 'name': 'Bayushi Kaede', 'gaming_group_id': 1, 'knacks': {'iaijutsu': 2}},
            {'id': 6, 'name': 'Nobody', 'gaming_group_id': 1},
        ]
    }

    def test_knack_holders_are_grouped_characters_with_the_knack(self) -> None:
        found = sheet.knack_holders(token='t', get=lambda url, token, timeout: self.PAYLOAD)
        assert found == sheet.HoldersResult(holders=(sheet.KnackHolder(3, 'Tsuruchi Jimen', 2, 4),))

    def test_knack_holders_degrade(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        def boom(url: str, token: str, timeout: float) -> Any:
            raise OSError('down')

        assert 'could not reach' in sheet.knack_holders(token='t', get=boom).reason
        empty = tmp_path / 'secrets.ini'
        empty.write_text('[x]\ny = 1\n')
        monkeypatch.setattr(sheet, 'SECRETS', empty)
        assert 'roll_query_token' in sheet.knack_holders().reason
        assert 'gm_write_token' in sheet.get_conversation(2).reason
        assert 'gm_write_token' in sheet.open_conversation({}).reason
        assert 'gm_write_token' in sheet.close_conversation('c-1').reason

    def test_tokens(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        secrets = tmp_path / 'secrets.ini'
        secrets.write_text('[character_sheet]\nroll_query_token = r\ngm_write_token = w\n')
        monkeypatch.setattr(sheet, 'SECRETS', secrets)
        assert sheet.write_token() == 'w'
        seen: list[tuple[str, str]] = []

        def get(url: str, token: str, timeout: float) -> Any:
            seen.append((url, token))
            return {'conversation': None}

        assert sheet.get_conversation(2, get=get) == sheet.ConversationResult()
        assert seen == [(f'{sheet.BASE_URL}/api/conversation?group=2', 'w')]

    def test_open_and_close(self) -> None:
        sent: list[tuple[str, str, Any]] = []

        def send(method: str, url: str, token: str, body: Any, timeout: float) -> Any:
            sent.append((method, url, body))
            return {'conversation': body}

        opened = sheet.open_conversation({'conversation_id': 'c-1'}, token='w', send=send)
        assert opened.conversation == {'conversation_id': 'c-1'}
        assert sheet.close_conversation('c 1/x', token='w', send=send) == (
            sheet.ConversationResult()
        )
        assert sent[0][:2] == ('PUT', f'{sheet.BASE_URL}/api/conversation')
        assert sent[1][:2] == ('DELETE', f'{sheet.BASE_URL}/api/conversation/c%201%2Fx')

    @pytest.mark.parametrize(
        ('code', 'expected'),
        [
            (404, 'no /api/conversation route'),
            (503, 'GM_WRITE_TOKEN is not set'),
            (401, 'refused the [character_sheet] gm_write_token'),
            (500, 'returned 500'),
        ],
    )
    def test_failures_say_what_to_fix(self, code: int, expected: str) -> None:
        def fail(*args: Any) -> Any:
            raise urllib.error.HTTPError('u', code, 'x', {}, None)  # type: ignore[arg-type]

        assert expected in sheet.open_conversation({}, token='w', send=fail).reason
        assert expected in sheet.get_conversation(2, token='w', get=fail).reason
        closed = sheet.close_conversation('c-1', token='w', send=fail)
        assert closed.reason == '' if code == 404 else expected in closed.reason

    def test_close_degrades_on_a_dead_connection(self) -> None:
        def dead(*args: Any) -> Any:
            raise OSError('down')

        assert 'could not reach' in sheet.close_conversation('c-1', token='w', send=dead).reason

    def test_send_is_a_json_request_with_a_bearer_token(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        seen: dict[str, Any] = {}

        def fake_urlopen(request: Any, timeout: float = 0) -> Any:
            seen.update(
                method=request.get_method(),
                auth=request.get_header('Authorization'),
                data=request.data,
            )
            return io.BytesIO(b'{"conversation": null}')

        monkeypatch.setattr(urllib.request, 'urlopen', fake_urlopen)
        assert sheet._send('PUT', 'https://x/api', 'w', {'a': 1}, 1.0) == {'conversation': None}
        assert seen == {'method': 'PUT', 'auth': 'Bearer w', 'data': b'{"a": 1}'}
        sheet._send('DELETE', 'https://x/api', 'w', None, 1.0)
        assert seen['data'] is None
