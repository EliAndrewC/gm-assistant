"""Printing above the prompt, and the short Conversation repr.

The GM's report, verbatim: *"Note that I have to hit the Enter key to get to
another line. Is there a way in a Python REPL to insert text above the current
`>>>` prompt?"* There is - see `console.print_above` for the mechanism.
"""

from __future__ import annotations

import io
import logging
from datetime import UTC, datetime
from typing import Any

import pytest

from l7r.repl import shell
from l7r.repl.rolls import console
from l7r.repl.rolls.models import Conversation, Roll

WHEN = datetime(2026, 8, 29, 0, 23, 26, tzinfo=UTC)

NPC = {
    'id': 'eb7c70a9b7264f509fa22efcb51f04b8',
    'slug': 'hatsu',
    'name': 'Hatsu',
    'character_url': 'https://waspbountyhunters.obsidianportal.com/characters/hatsu',
    'tags': ['peasant', 'Akagane province', 'Reiji domain', 'silk'],
}


class FakeTTY(io.StringIO):
    def isatty(self) -> bool:
        return True


class TestPrintAbove:
    def test_clears_the_line_writes_and_redraws_the_prompt(self) -> None:
        out = FakeTTY()
        assert console.print_above(
            '  + Roll Tester: etiquette 28 @1', stream=out, line_buffer=lambda: 'begin_conv'
        )
        written = out.getvalue()
        assert written.startswith(console.CLEAR_LINE), 'the prompt line must be erased first'
        assert '  + Roll Tester: etiquette 28 @1\n' in written
        assert written.endswith('>>> begin_conv'), 'the prompt and what was typed come back'

    def test_an_empty_buffer_still_redraws_the_prompt(self) -> None:
        out = FakeTTY()
        console.print_above('hello', stream=out, line_buffer=lambda: '')
        assert out.getvalue().endswith('>>> ')

    def test_multi_line_text_is_written_whole(self) -> None:
        out = FakeTTY()
        console.print_above('one\ntwo', stream=out, line_buffer=lambda: '')
        assert 'one\ntwo\n' in out.getvalue()

    def test_a_pipe_gets_a_plain_print_with_no_escapes(self) -> None:
        """Piped output must not carry escape codes - the same rule set_title follows."""
        out = io.StringIO()
        assert not console.print_above('hello', stream=out, line_buffer=lambda: 'typed')
        assert out.getvalue() == 'hello\n'
        assert '\x1b' not in out.getvalue()

    def test_uses_sys_ps1_when_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr('sys.ps1', 'l7r> ', raising=False)
        out = FakeTTY()
        console.print_above('x', stream=out, line_buffer=lambda: '')
        assert out.getvalue().endswith('l7r> ')

    def test_reads_the_real_readline_buffer_by_default(self) -> None:
        # Not at a prompt, so the buffer is empty - the point is that it does not raise.
        assert console._line_buffer() == ''

    def test_defaults_to_stdout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        out = io.StringIO()
        monkeypatch.setattr('sys.stdout', out)
        console.print_above('to stdout', line_buffer=lambda: '')
        assert out.getvalue() == 'to stdout\n'


class TestConversationRepr:
    """The REPL echoes whatever `begin_conversation` returns."""

    def test_is_one_short_line(self) -> None:
        conv = Conversation(npc=NPC, opened_at=WHEN, channels=('a', 'b', 'c'))
        assert repr(conv) == '<talking to Hatsu: 0 rolls, watching 3 channels>'
        assert len(repr(conv)) < 80

    def test_does_not_dump_the_obsidian_portal_record(self) -> None:
        conv = Conversation(npc=NPC, opened_at=WHEN, channels=('a',))
        shown = repr(conv)
        for noise in ('eb7c70a9', 'avatar_url', 'Akagane', 'character_url', 'datetime'):
            assert noise not in shown

    def test_counts_read_naturally(self) -> None:
        conv = Conversation(npc=NPC, opened_at=WHEN, channels=('a',))
        conv.rolls.append(
            Roll(
                character='Roll Tester',
                skill='etiquette',
                total=28,
                source='recorded',
                message_id='1',
                at=WHEN,
            )
        )
        assert repr(conv) == '<talking to Hatsu: 1 roll, watching 1 channel>'


class TestCherryPyRouting:
    def test_routes_a_log_line_above_the_prompt(self, monkeypatch: pytest.MonkeyPatch) -> None:
        out = FakeTTY()
        monkeypatch.setattr('sys.stdout', out)
        assert shell.route_cherrypy_logs()
        import cherrypy

        cherrypy.log("Updated character eb7c70a9: ['bio']")
        assert console.CLEAR_LINE in out.getvalue()
        assert 'Updated character' in out.getvalue()

    def test_is_idempotent(self) -> None:
        import cherrypy

        shell.route_cherrypy_logs()
        shell.route_cherrypy_logs()
        installed = [
            h for h in cherrypy.log.error_log.handlers if isinstance(h, shell.PromptSafeHandler)
        ]
        assert len(installed) == 1, 'calling twice must not stack handlers'

    def test_the_handler_formats_one_line(self, monkeypatch: pytest.MonkeyPatch) -> None:
        out = FakeTTY()
        monkeypatch.setattr('sys.stdout', out)
        record = logging.LogRecord('x', logging.INFO, __file__, 1, 'a message', None, None)
        shell.PromptSafeHandler().emit(record)
        assert '  . a message' in out.getvalue()


class TestSay:
    def test_the_watcher_speaks_through_the_console(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from l7r.repl.rolls import conversation as conv

        spoken: list[str] = []

        def capture(text: str, **kwargs: Any) -> bool:
            spoken.append(text)
            return True

        monkeypatch.setattr(console, 'print_above', capture)
        conv.say('  + something')
        assert spoken == ['  + something']

    def test_it_reaches_stdout_for_real(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from l7r.repl.rolls import conversation as conv

        out = io.StringIO()
        monkeypatch.setattr('sys.stdout', out)
        conv.say('plain')
        assert out.getvalue() == 'plain\n'


def test_the_gms_reported_output_shape(capsys: Any) -> None:
    """A regression pin on the shape the GM complained about.

    Before: the watcher's lines landed after `>>> ` with no prompt afterwards.
    After: every watcher line is preceded by a line-clear and followed by a prompt.
    """
    out = FakeTTY()
    for line in ('  + Roll Tester: etiquette 28 @1', '  -> Hatsu: Roll Tester etiquette: 25'):
        console.print_above(line, stream=out, line_buffer=lambda: '')
    written = out.getvalue()
    assert written.count(console.CLEAR_LINE) == 2
    assert written.count('>>> ') == 2
    assert written.endswith('>>> '), 'the GM must never be left without a prompt'
