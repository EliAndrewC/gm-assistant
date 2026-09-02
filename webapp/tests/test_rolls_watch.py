"""The background watcher: live feedback, debounced writes, and the bot-author join.

The GM asked for this shape directly: *"it would be nice to see something
indicating that the roll was seen, and then maybe we debounce so that within 2
minutes we update with the latest set of rolls"*. Feedback is immediate and local;
the write to Obsidian Portal is coalesced.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

import pytest

from l7r.repl.rolls import conversation as conv
from l7r.repl.rolls.models import Conversation, Roll

OPENED = datetime(2026, 8, 28, 23, 27, tzinfo=UTC)
BIO = '[[File:7569613 | class=media-item-align-none | Hatsu.png]]\r\n\r\nA silk merchant.\r\n'


@pytest.fixture(autouse=True)
def closed() -> Any:
    conv._open = None
    conv.stop_watching(timeout=0.1)
    yield
    conv._open = None
    conv.stop_watching(timeout=0.1)


def conversation() -> Conversation:
    return Conversation(npc={'id': 'hatsu-id', 'name': 'Hatsu'}, opened_at=OPENED, channels=('c1',))


def roll(name: str, skill: str, total: int, rank: int | None = None) -> Roll:
    return Roll(
        character=name,
        skill=skill,
        total=total,
        source='recorded',
        message_id='1',
        at=OPENED,
        rank=rank,
    )


def adder(*rolls: Roll) -> Callable[[Conversation], Conversation]:
    def collector(c: Conversation) -> Conversation:
        c.rolls.extend(rolls)
        return c

    return collector


def recorder() -> tuple[dict[str, Any], Any]:
    seen: dict[str, Any] = {}

    def update(cid: str, **kw: Any) -> None:
        seen.update({'id': cid, **kw})

    return seen, update


class TestTick:
    def test_first_write_is_immediate(self) -> None:
        """Seeing the line appear once confirms the whole path; then it coalesces."""
        c = conversation()
        seen, update = recorder()
        wrote = conv._tick(
            c,
            collector=adder(roll('Roll Tester', 'etiquette', 23, 1)),
            get_body=lambda cid: {'bio': BIO},
            update=update,
            clock=lambda: 100.0,
        )
        assert wrote
        # "Tester", not "Roll Tester": the record carries personal names only, and the
        # rule is the naive last-token one, applied to the sheet app's test character
        # exactly as it is to a Rokugani one.
        assert c.written == ('Tester etiquette: 20',)
        assert 'Tester etiquette: 20' in str(seen['bio'])
        assert 'A silk merchant.' in str(seen['bio'])

    def test_announces_each_new_roll(self, capsys: Any) -> None:
        c = conversation()
        _, update = recorder()
        conv._tick(
            c,
            collector=adder(roll('Roll Tester', 'etiquette', 23, 1)),
            get_body=lambda cid: {'bio': BIO},
            update=update,
            clock=lambda: 1.0,
        )
        out = capsys.readouterr().out
        # The live announcement keeps the FULL name - it is how the GM confirms the
        # roll was attributed to the right character. Only the written line is trimmed.
        assert '+ Roll Tester: etiquette 23 @1' in out
        assert '-> Hatsu: Tester etiquette: 20' in out

    def test_a_roll_with_no_rank_announces_without_one(self, capsys: Any) -> None:
        c = conversation()
        _, update = recorder()
        conv._tick(
            c,
            collector=adder(roll('Jimen', 'law', 44)),
            get_body=lambda cid: {'bio': BIO},
            update=update,
            clock=lambda: 1.0,
        )
        assert '+ Jimen: law 44\n' in capsys.readouterr().out

    def test_silent_when_asked(self, capsys: Any) -> None:
        c = conversation()
        _, update = recorder()
        conv._tick(
            c,
            collector=adder(roll('Jimen', 'law', 44)),
            get_body=lambda cid: {'bio': BIO},
            update=update,
            clock=lambda: 1.0,
            announce=False,
        )
        assert capsys.readouterr().out == ''

    def test_nothing_collected_writes_nothing(self) -> None:
        c = conversation()
        seen, update = recorder()
        assert not conv._tick(
            c,
            collector=adder(),
            get_body=lambda cid: {'bio': BIO},
            update=update,
            clock=lambda: 1.0,
        )
        assert seen == {}

    def test_an_unchanged_line_writes_nothing(self) -> None:
        c = conversation()
        seen, update = recorder()
        conv._tick(
            c,
            collector=adder(roll('A', 'etiquette', 23)),
            get_body=lambda cid: {'bio': BIO},
            update=update,
            clock=lambda: 0.0,
        )
        seen.clear()
        assert not conv._tick(
            c,
            collector=adder(),
            get_body=lambda cid: {'bio': BIO},
            update=update,
            clock=lambda: 9999.0,
        )
        assert seen == {}

    def test_the_debounce_holds_a_second_write_back(self) -> None:
        c = conversation()
        seen, update = recorder()
        conv._tick(
            c,
            collector=adder(roll('A', 'etiquette', 23)),
            get_body=lambda cid: {'bio': BIO},
            update=update,
            clock=lambda: 100.0,
        )
        seen.clear()
        wrote = conv._tick(
            c,
            collector=adder(roll('B', 'etiquette', 31)),
            get_body=lambda cid: {'bio': BIO},
            update=update,
            clock=lambda: 100.0 + conv.WRITE_DEBOUNCE_SECONDS - 1,
        )
        assert not wrote, 'a write inside the debounce window must be held'
        assert seen == {}
        assert c.written == ('A etiquette: 20',)

    def test_the_debounce_releases(self) -> None:
        c = conversation()
        seen, update = recorder()
        conv._tick(
            c,
            collector=adder(roll('A', 'etiquette', 23)),
            get_body=lambda cid: {'bio': BIO},
            update=update,
            clock=lambda: 100.0,
        )
        wrote = conv._tick(
            c,
            collector=adder(roll('B', 'etiquette', 31)),
            get_body=lambda cid: {'bio': BIO},
            update=update,
            clock=lambda: 100.0 + conv.WRITE_DEBOUNCE_SECONDS + 1,
        )
        assert wrote
        assert c.written == ('B / A etiquette: 30 / 20',)
        assert str(seen['bio']).count('etiquette:') == 1, 'the line is REPLACED, not stacked'

    def test_a_zero_debounce_always_writes(self) -> None:
        """end_conversation and the exit hook pass 0.0 meaning "write now".

        A written_at ahead of the clock made the elapsed time negative, and the
        guard then blocked the one write that must never be skipped.
        """
        c = conversation()
        seen, update = recorder()
        c.written = ('A etiquette: 20',)
        c.written_at = 1e9  # ahead of any monotonic reading
        assert conv._tick(
            c,
            collector=adder(roll('B', 'etiquette', 31)),
            get_body=lambda cid: {'bio': BIO},
            update=update,
            clock=lambda: 5.0,
            debounce=0.0,
            announce=False,
        )
        assert seen, 'a forced write must not be blocked by the clock'

    def test_an_unannotated_second_skill_is_HELD_not_written(self) -> None:
        """Feature 202 deliberately changed this: only Etiquette writes unannotated.

        This test previously asserted that a Law roll produced a second line. It does
        not any more - a bare "A law: 40" months later tells the GM nothing, so it
        waits for annotate(). Updated rather than deleted, because the ASSERTION is
        still worth making, just with the opposite expectation.
        """
        c = conversation()
        seen, update = recorder()
        conv._tick(
            c,
            collector=adder(roll('A', 'etiquette', 23)),
            get_body=lambda cid: {'bio': BIO},
            update=update,
            clock=lambda: 0.0,
        )
        conv._tick(
            c,
            collector=adder(roll('A', 'law', 44)),
            get_body=lambda cid: {'bio': str(seen['bio'])},
            update=update,
            clock=lambda: 10_000.0,
        )
        assert c.written == ('A etiquette: 20',), 'the law roll must be held'

    def test_an_ANNOTATED_second_skill_becomes_a_second_line(self) -> None:
        c = conversation()
        seen, update = recorder()
        conv._tick(
            c,
            collector=adder(roll('A', 'etiquette', 23)),
            get_body=lambda cid: {'bio': BIO},
            update=update,
            clock=lambda: 0.0,
        )
        annotated = replace(roll('A', 'law', 44), note='pressing him on the warrant')
        conv._tick(
            c,
            collector=adder(annotated),
            get_body=lambda cid: {'bio': str(seen['bio'])},
            update=update,
            clock=lambda: 10_000.0,
        )
        assert c.written == (
            'A etiquette: 20',
            '40 law: A pressing him on the warrant',
        )
        assert 'A silk merchant.' in str(seen['bio'])

    def test_a_record_with_no_body_still_writes(self) -> None:
        c = conversation()
        seen, update = recorder()
        conv._tick(
            c,
            collector=adder(roll('A', 'etiquette', 23)),
            get_body=lambda cid: None,
            update=update,
            clock=lambda: 1.0,
        )
        assert seen['bio'] == 'A etiquette: 20'

    def test_an_unattributed_roll_produces_no_line(self) -> None:
        c = conversation()
        seen, update = recorder()
        assert not conv._tick(
            c,
            collector=adder(roll('', 'etiquette', 23)),
            get_body=lambda cid: {'bio': BIO},
            update=update,
            clock=lambda: 1.0,
        )
        assert seen == {}


class TestWatcher:
    def test_starts_polls_and_stops(self) -> None:
        c = conversation()
        conv._open = c
        ticks = threading.Event()

        def collector(x: Conversation) -> Conversation:
            ticks.set()
            return x

        conv.start_watching(
            c,
            interval=0.01,
            collector=collector,
            get_body=lambda cid: {'bio': BIO},
            update=lambda cid, **kw: None,
            announce=False,
        )
        assert ticks.wait(timeout=3.0), 'the watcher should have polled'
        conv.stop_watching(timeout=2.0)
        assert conv._watcher is None

    def test_a_failing_poll_is_reported_not_fatal(self, capsys: Any) -> None:
        c = conversation()
        conv._open = c
        rounds = threading.Event()

        def boom(x: Conversation) -> Conversation:
            rounds.set()
            raise RuntimeError('discord fell over')

        conv.start_watching(
            c,
            interval=0.01,
            collector=boom,
            get_body=lambda cid: {'bio': BIO},
            update=lambda cid, **kw: None,
        )
        assert rounds.wait(timeout=3.0)
        conv.stop_watching(timeout=2.0)
        assert 'watching Hatsu' in capsys.readouterr().out

    def test_it_gives_up_when_the_conversation_is_replaced(self) -> None:
        c = conversation()
        conv._open = None  # never the open conversation
        conv.start_watching(
            c,
            interval=0.01,
            collector=adder(),
            get_body=lambda cid: {'bio': BIO},
            update=lambda cid, **kw: None,
        )
        watcher = conv._watcher
        assert watcher is not None
        watcher.join(timeout=3.0)
        assert not watcher.is_alive(), 'the loop should return once it is not the open one'
        conv.stop_watching(timeout=0.5)

    def test_stopping_when_nothing_runs_is_harmless(self) -> None:
        conv.stop_watching(timeout=0.1)
        assert conv._watcher is None


class TestCloseOnExit:
    """Quitting with a conversation open would otherwise discard real work.

    `end_conversation` does two things the watcher never gets to: a final collect,
    and a write with the debounce disabled. A daemon thread just dies with the
    process, so without an exit hook the GM loses up to WRITE_DEBOUNCE_SECONDS of
    rolls plus up to POLL_SECONDS of uncollected ones - held only in memory.
    """

    def test_nothing_open_is_a_no_op(self) -> None:
        conv._open = None
        assert conv.close_open_conversation() == ''

    def test_it_flushes_rolls_the_debounce_was_still_holding(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        c = conversation()
        conv._open = c
        seen, update = recorder()
        # A write happened a moment ago, and a further roll arrived after it - the
        # exact window the debounce holds open and a plain exit would discard.
        c.written = ('A etiquette: 20',)
        c.written_at = time.monotonic()
        c.rolls.extend([roll('A', 'etiquette', 23), roll('B', 'etiquette', 31)])
        written = conv.close_open_conversation(
            get_body=lambda cid: {'bio': BIO},
            update=update,
            collector=lambda c: c,
        )
        assert written == 'B / A etiquette: 30 / 20', 'the later roll must reach the record'
        assert seen, 'the final write must happen despite the debounce'
        assert conv._open is None

    def test_a_failure_on_the_way_out_is_reported_not_raised(
        self, monkeypatch: pytest.MonkeyPatch, capsys: Any
    ) -> None:
        c = conversation()
        conv._open = c
        c.rolls.append(roll('A', 'etiquette', 23))

        def explode(*args: Any, **kwargs: Any) -> Any:
            raise RuntimeError('obsidian portal unreachable')

        monkeypatch.setattr(conv, 'end_conversation', explode)
        assert conv.close_open_conversation() == ''
        out = capsys.readouterr().out
        assert 'could not write the last rolls for Hatsu' in out
        assert 'obsidian portal unreachable' in out


class TestBotAuthoredJoin:
    """A slash-command roll must join by the CHARACTER the bot named, not the author.

    Measured 2026-08-28: a real `/etiquette` post came from author
    1490400739934212116 (the sheet bot) while the recorded roll's actor_discord_id
    was the player's. Joining on the author found nothing at all.
    """

    def _message(self, author: str) -> dict[str, Any]:
        return {
            'id': '5',
            'timestamp': '2026-08-28T23:28:01+00:00',
            'author': {'id': author, 'bot': author == conv.SHEET_BOT_ID},
            'content': '**Roll Tester**: **23** Etiquette@1',
            'attachments': [{'content_type': 'image/png', 'filename': 'l7r-roll.png'}],
        }

    def _recorded(self, character: str) -> tuple[Any, ...]:
        from l7r.repl.rolls.sheet import RecordedRoll

        return (
            RecordedRoll(
                character=character,
                skill='etiquette',
                total=23,
                actor_discord_id='183026066498125825',
                at=datetime(2026, 8, 28, 23, 28, 1, tzinfo=UTC),
                rank=1,
            ),
        )

    def test_joins_on_the_named_character(self) -> None:
        joined = conv._join(
            self._message(conv.SHEET_BOT_ID),
            self._recorded('Roll Tester'),
            datetime(2026, 8, 28, 23, 28, 1, tzinfo=UTC),
        )
        assert joined is not None
        assert joined.character == 'Roll Tester'
        assert joined.total == 23
        assert joined.rank == 1
        assert joined.source == 'recorded'

    def test_a_different_character_does_not_match(self) -> None:
        assert (
            conv._join(
                self._message(conv.SHEET_BOT_ID),
                self._recorded('Someone Else'),
                datetime(2026, 8, 28, 23, 28, 1, tzinfo=UTC),
            )
            is None
        )

    def test_a_human_post_still_joins_on_the_author(self) -> None:
        joined = conv._join(
            self._message('183026066498125825'),
            self._recorded('Roll Tester'),
            datetime(2026, 8, 28, 23, 28, 1, tzinfo=UTC),
        )
        assert joined is not None
        assert joined.character == 'Roll Tester'


class TestBotRollCharacter:
    """A `/etiquette` roll is posted BY THE BOT, so the author is never the player."""

    def test_reads_the_character_the_bot_named(self) -> None:
        message = {
            'author': {'id': conv.SHEET_BOT_ID},
            'content': '**Roll Tester**: **23** Etiquette@1',
        }
        assert conv.bot_roll_character(message) == 'Roll Tester'

    def test_a_human_posting_bold_text_is_not_a_bot_roll(self) -> None:
        message = {
            'author': {'id': '183026066498125825'},
            'content': '**Roll Tester**: **23** Etiquette@1',
        }
        assert conv.bot_roll_character(message) == ''

    def test_the_bot_saying_something_else(self) -> None:
        assert (
            conv.bot_roll_character({'author': {'id': conv.SHEET_BOT_ID}, 'content': 'hello'}) == ''
        )

    def test_a_message_with_no_author(self) -> None:
        assert conv.bot_roll_character({'content': '**A**: **1** Etiquette'}) == ''
