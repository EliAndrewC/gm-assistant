"""Feature 217: the void points an NPC spends in a conversation reach the GM-only notes."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import pytest

from l7r.repl import dice, gmrolls
from l7r.repl.rolls import conversation as conv
from l7r.repl.rolls import hidden, npcskills, voidspent
from l7r.repl.rolls.models import Conversation

W = datetime(2026, 10, 17, 1, 0, tzinfo=UTC)
BIO = '[[File:1 | class=media-item-align-none | Otsuki.png]]\r\n\r\nA magistrate.\r\n'
NOTES = 'XP: 65\r\nHonor: 3.0'
TAGS = npcskills.build_tags()
tact, sincerity = TAGS['tact'], TAGS['sincerity']
vp = npcskills.vp


@pytest.fixture(autouse=True)
def clean(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    conv._open = None
    gmrolls.clear()
    monkeypatch.setattr(dice, 'd10', lambda reroll=True: 7)
    monkeypatch.setattr(conv, 'say', lambda text: None)
    yield
    conv._open = None
    gmrolls.clear()


def talking(title: str = 'confrontation on the Imperial road', **numbers: int) -> Conversation:
    c = Conversation(npc={'id': 'o', 'name': 'Otsuki'}, opened_at=W, channels=('c',), title=title)
    c.numbers = dict(numbers)
    c.numbers_written = dict(numbers)
    conv._open = c
    return c


def answers(monkeypatch: pytest.MonkeyPatch, *replies: str) -> None:
    queue = list(replies)
    monkeypatch.setattr(npcskills, '_ask', lambda question: queue.pop(0))


def tick(c: Conversation, record: dict[str, Any]) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    def update(npc_id: str, **fields: Any) -> None:
        calls.append(fields)
        record.update(fields)

    conv._tick(
        c,
        collector=lambda x: x,
        get_body=lambda i: record,
        update=update,
        clock=lambda: 100.0,
        debounce=0.0,
    )
    return calls


class TestEntries:
    def test_the_called_form_logs_its_count_and_skill(self) -> None:
        c = talking(air=3, tact=2, sincerity=3)
        tact(vp)
        sincerity(vp * 2)
        assert voidspent.entries(c) == (
            '- 2026-10-17 1 void point on tact - confrontation on the Imperial road',
            '- 2026-10-17 2 void points on sincerity - confrontation on the Imperial road',
        )

    def test_no_title_no_tail_and_no_spend_no_entry(self) -> None:
        c = talking('', air=3, tact=2)
        tact()
        assert voidspent.entries(c) == ()
        tact(5, 3, vp)
        assert voidspent.entries(c) == ('- 2026-10-17 1 void point on tact',)

    def test_this_roll_spent_one_at_the_disagreement_prompt(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        c = talking(air=3, tact=2)
        answers(monkeypatch, 'v')
        dice.xky(6, 4) - tact
        assert voidspent.entries(c) == (
            '- 2026-10-17 1 void point on tact - confrontation on the Imperial road',
        )

    def test_the_previous_roll_spent_two(self, monkeypatch: pytest.MonkeyPatch) -> None:
        c = talking(air=5, tact=2)
        answers(monkeypatch, 'v')
        dice.xky(5, 3) - tact
        assert voidspent.entries(c) == (
            '- 2026-10-17 2 void points on an earlier tact roll - '
            'confrontation on the Imperial road',
        )

    def test_a_mistaken_roll_spent_nothing_and_its_reroll_did(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        c = talking(air=3, tact=2)
        answers(monkeypatch, 'm')
        wrong = tact(6, 3, vp)  # reads as tact 3: the disagreement, answered "mistake"
        assert wrong is not None
        assert wrong.entry.mistake
        assert voidspent.entries(c) == ()
        tact(5, 3, vp)
        assert len(voidspent.entries(c)) == 1

    def test_a_second_answer_on_one_roll_is_not_a_second_spend(self) -> None:
        c = talking(air=3, tact=2)
        total = tact(vp)
        assert total is not None
        voidspent.note(c, total.entry, 2)
        voidspent.note(c, total.entry, 0)
        assert voidspent.entries(c) == (
            '- 2026-10-17 2 void points on tact - confrontation on the Imperial road',
        )

    def test_nothing_is_logged_without_a_conversation(self) -> None:
        dice.xky(6, 4) - tact
        assert conv._open is None


class TestPersistence:
    def test_a_spend_alone_writes_the_gm_only_notes_and_never_the_bio(self) -> None:
        c = talking(air=3, tact=2)
        tact(vp)
        record: dict[str, Any] = {'bio': BIO, 'game_master_info': NOTES}
        calls = tick(c, record)
        assert [sorted(f) for f in calls] == [['game_master_info']]
        assert record['game_master_info'].endswith(
            'Void points spent:\n'
            '- 2026-10-17 1 void point on tact - confrontation on the Imperial road'
        )
        assert record['bio'] == BIO
        assert tick(c, record) == []

    def test_the_block_is_a_log_across_conversations(self) -> None:
        record: dict[str, Any] = {'bio': BIO, 'game_master_info': NOTES}
        first = talking('', air=3, tact=2)
        tact(vp)
        tick(first, record)
        # The next conversation, the same day and untitled: its line reads the same.
        second = talking('', air=3, tact=2)
        tact(vp)
        tick(second, record)
        tact(vp * 2)
        tick(second, record)
        block = record['game_master_info'].split('Void points spent:\n')[1]
        assert block.split('\n') == [
            '- 2026-10-17 1 void point on tact',
            '- 2026-10-17 1 void point on tact',
            '- 2026-10-17 2 void points on tact',
        ]


class TestRewriteKeepsAnIdenticalOlderLine:
    def test_only_this_conversation_s_copy_is_replaced(self) -> None:
        notes = hidden.rewrite(NOTES, (), ('- same',))
        notes = hidden.rewrite(notes, (), ('- same',))
        assert hidden.rewrite(notes, ('- same',), ('- same', '- new')).endswith(
            'Hidden rolls:\n- same\n- same\n- new'
        )
