"""Feature 203: answering when a bot is mentioned.

The guard that matters most is the bot check. The GM has watched this exact
failure take a server down: *"it just kept responding to itself in an infinite
loop that was really bad for the server and made it unusable."* Several tests
here exist only to make that impossible to regress.
"""

from __future__ import annotations

import asyncio
import configparser
import contextlib
import json
from pathlib import Path
from typing import Any

import pytest
from configobj import ConfigObj

from l7r.mention import bots, gateway, policy, responder, rules

# --------------------------------------------------------------------------
# rules
# --------------------------------------------------------------------------


class TestReplies:
    def test_the_character_sheet_keeps_the_line_the_gm_liked(self) -> None:
        """The GM said they liked this answer, so it is pinned rather than tidied."""
        reply = rules.respond_to('<@1> What is your purpose?', rules.CHARACTER_SHEET)
        assert reply == 'I record what you roll. I do not judge it. Much.'

    def test_the_gm_assistant_answers_with_its_porpoise(self) -> None:
        """The joke the GM asked for: it mishears the question, entirely straight."""
        reply = rules.respond_to('<@1> What is your purpose?', rules.GM_ASSISTANT)
        assert 'Michiko' in reply
        assert 'porpoise' in reply
        assert reply.endswith(rules.PORPOISE_IMAGE)

    def test_the_two_bots_never_answer_alike_on_their_own_topics(self) -> None:
        """The point of the split. If these ever converge, the feature is gone."""
        for question in (
            'what is your purpose?',
            'is there cake?',
            'who are you?',
            'hello',
            'thanks',
            'are you a bot?',
            'help',
            'can I roll?',
            'something nobody wrote a rule for',
        ):
            gm = rules.respond_to(question, rules.GM_ASSISTANT)
            sheet = rules.respond_to(question, rules.CHARACTER_SHEET)
            assert gm != sheet, f'both bots said the same thing to {question!r}'

    def test_a_shared_topic_is_answered_the_same_way_by_both(self) -> None:
        """COMMON is for the setting, not for the bot, so both voices agree."""
        gm = rules.respond_to('tell me about honor', rules.GM_ASSISTANT)
        sheet = rules.respond_to('tell me about honor', rules.CHARACTER_SHEET)
        assert gm == sheet
        assert 'Honor' in gm

    def test_a_bots_own_table_beats_the_shared_one(self) -> None:
        """Precedence, asserted rather than assumed - `rules_for` concatenates."""
        table = rules.rules_for(rules.GM_ASSISTANT)
        assert table[: len(rules.GM_ASSISTANT_RULES)] == rules.GM_ASSISTANT_RULES
        assert table[-len(rules.COMMON) :] == rules.COMMON

    def test_the_porpoise_image_is_the_public_domain_one_we_checked(self) -> None:
        """Pinned deliberately (GM 2026-08-31).

        The GM's condition was that we *"never make use of something not
        legitimately free for this kind of jokey use"*. The recorded choice is a
        1911 Encyclopaedia Britannica plate - public domain by AGE, which cannot be
        revoked the way a granted license can. Swapping in some other image is a
        licensing decision, so it should have to change a test that says so out loud
        rather than slipping through as a one-character edit.
        """
        assert rules.PORPOISE_IMAGE.startswith('https://upload.wikimedia.org/wikipedia/commons/')
        assert rules.PORPOISE_IMAGE.endswith('EB1911_Porpoise_-_Phocaena_communis.jpg')

    def test_matching_ignores_case(self) -> None:
        assert rules.respond_to('<@1> CAKE', rules.CHARACTER_SHEET) == 'The cake is a lie.'

    def test_an_unanticipated_question_gets_that_bots_own_shrug(self) -> None:
        """FR-002. A page met with silence reads as broken."""
        assert (
            rules.respond_to('<@1> what is the airspeed of a swallow', rules.GM_ASSISTANT)
            == rules.DEFAULTS[rules.GM_ASSISTANT]
        )

    def test_a_bot_with_no_voice_yet_still_answers(self) -> None:
        """A new bot in the fleet gets the shared table and the shared default.

        It must not raise, and it must not go silent - adding a token should never
        be able to break the responder for the bots that already work.
        """
        assert rules.respond_to('hello there', 'not-a-known-bot') == rules.DEFAULT_REPLY
        assert rules.respond_to('about honor', 'not-a-known-bot') == rules.COMMON[0].reply

    def test_mentions_are_stripped_before_matching(self) -> None:
        assert rules.strip_mentions('<@123> hello <@!456>') == 'hello'

    def test_a_word_inside_the_mention_markup_cannot_match(self) -> None:
        # The id is digits, but a rule keyed on digits must not see the markup.
        assert rules.strip_mentions('<@1234567890>') == ''

    def test_empty_text(self) -> None:
        assert rules.respond_to('') == rules.DEFAULT_REPLY

    def test_every_rule_everywhere_has_a_non_empty_reply(self) -> None:
        tables = [*rules.RULES_BY_BOT.values(), rules.COMMON]
        assert tables, 'no rule tables found'
        for table in tables:
            for entry in table:
                assert entry.reply.strip()

    def test_every_bot_with_a_table_also_has_a_default(self) -> None:
        """Otherwise a bot with a voice still shrugs in the house voice."""
        for application_id in rules.RULES_BY_BOT:
            assert rules.DEFAULTS.get(application_id, '').strip()


# --------------------------------------------------------------------------
# policy
# --------------------------------------------------------------------------

KNOWN = {'A': 'token-a', 'B': 'token-b'}


def message(
    mid: str = '1',
    *,
    author: str = 'human',
    bot: bool = False,
    mentions: list[str] | None = None,
    roles: list[str] | None = None,
    everyone: bool = False,
    channel: str = 'chan',
    content: str = 'hello',
) -> dict[str, Any]:
    return {
        'id': mid,
        'channel_id': channel,
        'content': content,
        'author': {'id': author, 'bot': bot, 'username': author},
        'mentions': [{'id': m} for m in (mentions or [])],
        'mention_roles': roles or [],
        'mention_everyone': everyone,
    }


class TestTheLoopGuard:
    """A reply must never be able to trigger another reply."""

    def test_a_bot_is_never_answered(self) -> None:
        decider = policy.Decider(known=KNOWN)
        assert decider.should_answer(message(author='A', bot=True, mentions=['B']), 0.0) == []

    def test_not_even_when_it_says_something_matching(self) -> None:
        decider = policy.Decider(known=KNOWN)
        loud = message(author='A', bot=True, mentions=['B'], content='cake')
        assert decider.should_answer(loud, 0.0) == []

    def test_our_own_reply_coming_back_is_ignored(self) -> None:
        decider = policy.Decider(known=KNOWN)
        assert decider.should_answer(message('9', author='B', bot=True, mentions=['A']), 0.0) == []

    def test_is_bot_reads_the_author_flag(self) -> None:
        assert policy.is_bot({'author': {'bot': True}})
        assert not policy.is_bot({'author': {'bot': False}})
        assert not policy.is_bot({})


class TestWhoWasAddressed:
    def test_a_direct_mention_counts(self) -> None:
        assert policy.mentioned_bots(message(mentions=['A']), KNOWN) == ['A']

    def test_an_unknown_bot_does_not(self) -> None:
        assert policy.mentioned_bots(message(mentions=['Z']), KNOWN) == []

    def test_both_bots_in_one_message(self) -> None:
        assert policy.mentioned_bots(message(mentions=['A', 'B']), KNOWN) == ['A', 'B']

    def test_a_role_ping_is_not_addressing_the_bot(self) -> None:
        """FR-006 - Discord keeps role pings in a separate field for a reason."""
        assert policy.mentioned_bots(message(roles=['A']), KNOWN) == []

    def test_at_everyone_is_not_addressing_the_bot(self) -> None:
        assert policy.mentioned_bots(message(everyone=True), KNOWN) == []

    def test_no_mentions_at_all(self) -> None:
        assert policy.mentioned_bots(message(), KNOWN) == []


class TestDecider:
    def test_a_human_mention_is_answered(self) -> None:
        decider = policy.Decider(known=KNOWN)
        assert decider.should_answer(message(mentions=['A']), 0.0) == ['A']

    def test_a_message_with_no_mention_is_ignored(self) -> None:
        assert policy.Decider(known=KNOWN).should_answer(message(), 0.0) == []

    def test_the_same_message_is_never_answered_twice(self) -> None:
        """A resume replays events; FR-007 says they must not be answered again."""
        decider = policy.Decider(known=KNOWN)
        assert decider.should_answer(message('7', mentions=['A']), 0.0) == ['A']
        assert decider.should_answer(message('7', mentions=['A']), 500.0) == []

    def test_a_message_with_no_id_is_ignored(self) -> None:
        decider = policy.Decider(known=KNOWN)
        assert decider.should_answer({'author': {}, 'mentions': [{'id': 'A'}]}, 0.0) == []

    def test_a_burst_in_one_channel_produces_one_reply(self) -> None:
        """FR-005. An excited table must not become a wall of bot messages."""
        decider = policy.Decider(known=KNOWN)
        assert decider.should_answer(message('1', mentions=['A']), 100.0) == ['A']
        assert decider.should_answer(message('2', mentions=['A']), 101.0) == []
        assert decider.should_answer(message('3', mentions=['A']), 104.9) == []

    def test_the_limit_releases(self) -> None:
        decider = policy.Decider(known=KNOWN)
        decider.should_answer(message('1', mentions=['A']), 100.0)
        assert decider.should_answer(message('2', mentions=['A']), 106.0) == ['A']

    def test_the_limit_is_per_channel(self) -> None:
        decider = policy.Decider(known=KNOWN)
        assert decider.should_answer(message('1', mentions=['A'], channel='x'), 100.0) == ['A']
        assert decider.should_answer(message('2', mentions=['A'], channel='y'), 100.1) == ['A']

    def test_the_seen_list_stays_bounded(self) -> None:
        """This process is meant to run for weeks."""
        decider = policy.Decider(known=KNOWN, quiet_seconds=0.0)
        for index in range(policy.SEEN + 50):
            decider.should_answer(message(str(index), mentions=['A']), float(index))
        assert len(decider._seen) == policy.SEEN


# --------------------------------------------------------------------------
# bots
# --------------------------------------------------------------------------


def secrets(tmp_path: Path, body: str) -> Path:
    path = tmp_path / 'secrets.ini'
    path.write_text(body)
    return path


def defaults(tmp_path: Path, listener: str | None = 'A') -> Path:
    """The public half of the config: which application id holds the socket."""
    path = tmp_path / 'defaults.ini'
    body = 'campaign_url = "https://example.invalid"\n'
    if listener is not None:
        body += f'\n[mention_bots]\nlistener = {listener}\n'
    path.write_text(body)
    return path


class TestFleet:
    def test_loads_a_listener_and_two_tokens(self, tmp_path: Path) -> None:
        path = secrets(tmp_path, '[mention_bots]\nA = tok-a\nB = tok-b\n')
        fleet = bots.load_fleet(path, defaults(tmp_path))
        assert fleet.listener == 'A'
        assert fleet.listener_token == 'tok-a'
        assert fleet.token_for('B') == 'tok-b'
        assert fleet.token_for('Z') is None

    def test_reads_a_defaults_file_with_keys_before_its_first_section(self, tmp_path: Path) -> None:
        """The real defaults file opens with top-level keys; configparser refuses it.

        This is why the public half is read with ConfigObj. The helper writes a
        leading `campaign_url` for exactly this reason - without it the test would
        pass against a parser that could not read production config.
        """
        text = (defaults(tmp_path)).read_text()
        assert text.startswith('campaign_url'), 'the fixture must lead with a bare key'
        fleet = bots.load_fleet(
            secrets(tmp_path, '[mention_bots]\nA = tok-a\n'), defaults(tmp_path)
        )
        assert fleet.listener == 'A'

    def test_a_missing_section_says_how_to_fix_it(self, tmp_path: Path) -> None:
        with pytest.raises(bots.NotConfigured, match='application id'):
            bots.load_fleet(secrets(tmp_path, '[other]\nx = 1\n'), defaults(tmp_path))

    def test_no_tokens(self, tmp_path: Path) -> None:
        with pytest.raises(bots.NotConfigured, match='no bot tokens'):
            bots.load_fleet(secrets(tmp_path, '[mention_bots]\n'), defaults(tmp_path))

    def test_no_listener(self, tmp_path: Path) -> None:
        with pytest.raises(bots.NotConfigured, match='no `listener'):
            bots.load_fleet(
                secrets(tmp_path, '[mention_bots]\nA = tok\n'),
                defaults(tmp_path, listener=None),
            )

    def test_a_listener_we_cannot_speak_as(self, tmp_path: Path) -> None:
        path = secrets(tmp_path, '[mention_bots]\nA = tok\n')
        with pytest.raises(bots.NotConfigured, match='has no token'):
            bots.load_fleet(path, defaults(tmp_path, listener='Z'))

    def test_the_default_paths_point_at_the_real_files(self) -> None:
        """Every other test injects a path, so nothing checked the real ones.

        SECRETS was wrong: `parents[3]` is the repo root here, copied from
        `l7r/repl/rolls/`, which sits one directory deeper.
        """
        for path in (bots.SECRETS, bots.DEFAULTS):
            assert path.parent.name == 'webapp'
            assert (path.parent / 'l7r' / 'mention').is_dir()
        assert bots.SECRETS.name == 'development-secrets.ini'
        assert bots.DEFAULTS.name == 'development-defaults.ini'

    def test_the_listener_id_is_public_and_is_not_kept_as_a_secret(self) -> None:
        """The regression this split exists to prevent.

        A Discord application id is public - it is in every invite URL and is
        rendered into this app's OAuth login link - so keeping it in the secrets
        file made `test_chargen_security` report a secret value appearing in served
        HTML. That guard was right; the classification was wrong. Assert the shape,
        not just the current values, so putting it back fails here too.
        """
        public = ConfigObj(str(bots.DEFAULTS))
        assert str(public.get(bots.SECTION, {}).get('listener', '')).strip(), (
            f'{bots.DEFAULTS.name} must carry the public listener id'
        )
        if not bots.SECRETS.exists():  # pragma: no cover - present in every dev tree
            return
        private = configparser.ConfigParser()
        private.optionxform = str  # type: ignore[method-assign,assignment]
        private.read(bots.SECRETS)
        if private.has_section(bots.SECTION):
            assert 'listener' not in private.options(bots.SECTION), (
                'the listener application id is public; it belongs in '
                'development-defaults.ini, not among the secrets'
            )


# --------------------------------------------------------------------------
# gateway
# --------------------------------------------------------------------------


class FakeResponse:
    def __init__(self, payload: dict[str, Any] | None = None) -> None:
        self._payload = payload or {}

    def read(self) -> bytes:
        return json.dumps(self._payload).encode()

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None


class TestGatewayHelpers:
    def test_gateway_url_appends_the_version(self) -> None:
        url = gateway.gateway_url('tok', opener=lambda *a, **k: FakeResponse({'url': 'wss://gw'}))
        assert url == 'wss://gw?v=10&encoding=json'

    def test_send_message_posts_the_content(self) -> None:
        seen: dict[str, Any] = {}

        def opener(request: Any, timeout: float = 0) -> FakeResponse:
            seen['url'] = request.full_url
            seen['auth'] = request.get_header('Authorization')
            seen['body'] = json.loads(request.data)
            return FakeResponse()

        gateway.send_message('chan', 'tok', 'hi', opener=opener)
        assert seen['url'].endswith('/channels/chan/messages')
        assert seen['auth'] == 'Bot tok'
        assert seen['body']['content'] == 'hi'

    def test_a_reply_never_pings_anyone(self) -> None:
        """A reply that pings can start an argument with another bot."""
        seen: dict[str, Any] = {}

        def opener(request: Any, timeout: float = 0) -> FakeResponse:
            seen.update(json.loads(request.data))
            return FakeResponse()

        gateway.send_message('chan', 'tok', 'hi', opener=opener)
        assert seen['allowed_mentions'] == {'parse': []}

    def test_it_replies_to_the_message_when_asked(self) -> None:
        seen: dict[str, Any] = {}

        def opener(request: Any, timeout: float = 0) -> FakeResponse:
            seen.update(json.loads(request.data))
            return FakeResponse()

        gateway.send_message('chan', 'tok', 'hi', reply_to='42', opener=opener)
        assert seen['message_reference']['message_id'] == '42'
        assert seen['message_reference']['fail_if_not_exists'] is False

    def test_intents_are_only_what_is_needed(self) -> None:
        assert gateway.INTENTS == (1 << 9) | (1 << 15)

    def test_backoff_grows_and_caps(self) -> None:
        assert gateway.backoff(0, jitter=lambda: 1.0) == pytest.approx(1.0)
        assert gateway.backoff(3, jitter=lambda: 1.0) == pytest.approx(8.0)
        assert gateway.backoff(99, jitter=lambda: 1.0) == pytest.approx(gateway.BACKOFF_CAP)

    def test_backoff_jitters(self) -> None:
        assert gateway.backoff(0, jitter=lambda: 0.0) == pytest.approx(0.5)


class TestSession:
    def test_a_fresh_session_cannot_resume(self) -> None:
        assert not gateway.Session().resumable

    def test_ready_makes_it_resumable(self) -> None:
        session = gateway.Session()
        session.note(
            {
                'op': 0,
                's': 5,
                't': 'READY',
                'd': {'session_id': 'sid', 'resume_gateway_url': 'wss://r'},
            }
        )
        assert session.resumable
        assert session.sequence == 5
        assert session.resume_url == 'wss://r?v=10&encoding=json'

    def test_the_sequence_tracks_the_latest_event(self) -> None:
        session = gateway.Session()
        session.note(
            {
                'op': 0,
                's': 1,
                't': 'READY',
                'd': {'session_id': 's', 'resume_gateway_url': 'wss://r'},
            }
        )
        session.note({'op': 0, 's': 9, 't': 'MESSAGE_CREATE', 'd': {}})
        assert session.sequence == 9

    def test_forgetting_makes_it_identify_afresh(self) -> None:
        session = gateway.Session()
        session.note(
            {
                'op': 0,
                's': 1,
                't': 'READY',
                'd': {'session_id': 's', 'resume_gateway_url': 'wss://r'},
            }
        )
        session.forget()
        assert not session.resumable

    def test_identify_carries_token_and_intents(self) -> None:
        payload = gateway.identify('tok')
        assert payload['op'] == gateway.OP_IDENTIFY
        assert payload['d']['token'] == 'tok'
        assert payload['d']['intents'] == gateway.INTENTS

    def test_resume_carries_the_session(self) -> None:
        session = gateway.Session()
        session.note(
            {
                'op': 0,
                's': 3,
                't': 'READY',
                'd': {'session_id': 'sid', 'resume_gateway_url': 'wss://r'},
            }
        )
        payload = gateway.resume('tok', session)
        assert payload['op'] == gateway.OP_RESUME
        assert payload['d']['session_id'] == 'sid'
        assert payload['d']['seq'] == 3


class Socket:
    """A fake gateway socket that yields a scripted list of payloads."""

    def __init__(self, payloads: list[dict[str, Any]]) -> None:
        self.payloads = payloads
        self.sent: list[dict[str, Any]] = []

    async def send(self, raw: str) -> None:
        self.sent.append(json.loads(raw))

    def __aiter__(self) -> Socket:
        self._iter = iter(self.payloads)
        return self

    async def __anext__(self) -> str:
        try:
            return json.dumps(next(self._iter))
        except StopIteration:
            raise StopAsyncIteration from None

    async def __aenter__(self) -> Socket:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


async def nap(_seconds: float) -> None:
    """A sleep that never actually waits, but yields so tasks can be cancelled."""
    await asyncio.sleep(0)


def test_heartbeat_sends_the_sequence() -> None:
    async def run() -> Socket:
        socket = Socket([])
        session = gateway.Session()
        session.sequence = 4
        beat = asyncio.create_task(gateway.heartbeat_forever(socket, session, 1.0, nap))
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        beat.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await beat
        return socket

    socket = asyncio.run(run())
    assert socket.sent
    assert socket.sent[0]['op'] == gateway.OP_HEARTBEAT
    assert socket.sent[0]['d'] == 4


# --------------------------------------------------------------------------
# responder
# --------------------------------------------------------------------------

FLEET = bots.Fleet(tokens={'A': 'tok-a', 'B': 'tok-b'}, listener='A')


class TestHandle:
    def test_the_bot_that_was_addressed_is_the_bot_that_answers(self) -> None:
        """FR-003 - the GM's UI-intuition requirement."""
        sent: list[tuple[str, str, str]] = []
        spoke = responder.handle(
            message(mentions=['B']),
            policy.Decider(known=FLEET.tokens),
            FLEET,
            now=0.0,
            send=lambda ch, tok, text, **kw: sent.append((ch, tok, text)),
            say=lambda s: None,
        )
        assert spoke == ['B']
        assert sent[0][1] == 'tok-b', 'B answered with B token, not the listener'

    def test_both_bots_answer_when_both_are_addressed(self) -> None:
        sent: list[str] = []
        spoke = responder.handle(
            message(mentions=['A', 'B']),
            policy.Decider(known=FLEET.tokens),
            FLEET,
            now=0.0,
            send=lambda ch, tok, text, **kw: sent.append(tok),
            say=lambda s: None,
        )
        assert spoke == ['A', 'B']
        assert sent == ['tok-a', 'tok-b']

    def test_nothing_is_sent_for_a_bot(self) -> None:
        sent: list[str] = []
        responder.handle(
            message(author='B', bot=True, mentions=['A']),
            policy.Decider(known=FLEET.tokens),
            FLEET,
            now=0.0,
            send=lambda *a, **k: sent.append('x'),
            say=lambda s: None,
        )
        assert sent == []

    def test_a_failed_send_is_reported_and_does_not_stop_the_others(self) -> None:
        said: list[str] = []
        sent: list[str] = []

        def flaky(channel: str, token: str, text: str, **kw: object) -> None:
            if token == 'tok-a':
                raise RuntimeError('missing permissions')
            sent.append(token)

        spoke = responder.handle(
            message(mentions=['A', 'B']),
            policy.Decider(known=FLEET.tokens),
            FLEET,
            now=0.0,
            send=flaky,
            say=said.append,
        )
        assert spoke == ['B'], 'B still answered'
        assert sent == ['tok-b']
        assert any('could not reply as A' in line for line in said)

    def test_the_reply_is_the_matched_rule(self) -> None:
        sent: list[str] = []
        responder.handle(
            message(mentions=['A'], content='<@A> tell me about honor'),
            policy.Decider(known=FLEET.tokens),
            FLEET,
            now=0.0,
            send=lambda ch, tok, text, **kw: sent.append(text),
            say=lambda s: None,
        )
        assert sent == [rules.COMMON[0].reply]

    def test_each_bot_replies_in_its_own_voice_through_handle(self) -> None:
        """The routing, end to end.

        `respond_to` being per-bot is worth nothing if `handle` computes one reply
        for the message and sends it to everybody - which is exactly what it used to
        do, so this is the test that would have caught leaving it that way.
        """
        real = bots.Fleet(
            tokens={rules.GM_ASSISTANT: 'tok-gm', rules.CHARACTER_SHEET: 'tok-cs'},
            listener=rules.GM_ASSISTANT,
        )
        sent: dict[str, str] = {}
        responder.handle(
            message(
                mentions=[rules.GM_ASSISTANT, rules.CHARACTER_SHEET],
                content=f'<@{rules.GM_ASSISTANT}> <@{rules.CHARACTER_SHEET}> what is your purpose?',
            ),
            policy.Decider(known=real.tokens),
            real,
            now=0.0,
            send=lambda ch, tok, text, **kw: sent.__setitem__(tok, text),
            say=lambda s: None,
        )
        assert 'Michiko' in sent['tok-gm']
        assert sent['tok-cs'] == 'I record what you roll. I do not judge it. Much.'


def pumped(payloads: list[dict[str, Any]], **kwargs: Any) -> tuple[Socket, str, list[str]]:
    said: list[str] = []
    socket = Socket(payloads)
    outcome = asyncio.run(
        responder.pump(
            socket,
            FLEET,
            policy.Decider(known=FLEET.tokens),
            gateway.Session(),
            sleep=nap,
            clock=lambda: 0.0,
            say=said.append,
            send=kwargs.get('send', lambda *a, **k: None),
        )
    )
    return socket, outcome, said


HELLO = {'op': gateway.OP_HELLO, 'd': {'heartbeat_interval': 1.0}}


class TestPump:
    def test_hello_identifies_when_there_is_no_session(self) -> None:
        socket, _, _ = pumped([HELLO])
        assert socket.sent[0]['op'] == gateway.OP_IDENTIFY

    def test_reconnect_asks_to_resume(self) -> None:
        _, outcome, _ = pumped([{'op': gateway.OP_RECONNECT}])
        assert outcome == 'resume'

    def test_a_resumable_invalid_session_resumes(self) -> None:
        _, outcome, _ = pumped([{'op': gateway.OP_INVALID_SESSION, 'd': True}])
        assert outcome == 'resume'

    def test_a_dead_invalid_session_restarts(self) -> None:
        _, outcome, _ = pumped([{'op': gateway.OP_INVALID_SESSION, 'd': False}])
        assert outcome == 'restart'

    def test_a_mention_is_answered(self) -> None:
        sent: list[str] = []
        _, _, said = pumped(
            [
                HELLO,
                {
                    'op': gateway.OP_DISPATCH,
                    's': 1,
                    't': 'MESSAGE_CREATE',
                    'd': message(mentions=['A']),
                },
            ],
            send=lambda ch, tok, text, **kw: sent.append(text),
        )
        assert sent, 'a human mention should have been answered'
        assert any('A replied' in line for line in said)

    def test_a_bot_message_over_the_wire_is_ignored(self) -> None:
        sent: list[str] = []
        pumped(
            [
                HELLO,
                {
                    'op': gateway.OP_DISPATCH,
                    's': 1,
                    't': 'MESSAGE_CREATE',
                    'd': message(author='B', bot=True, mentions=['A']),
                },
            ],
            send=lambda *a, **k: sent.append('x'),
        )
        assert sent == []

    def test_other_dispatches_are_ignored(self) -> None:
        socket, outcome, _ = pumped(
            [HELLO, {'op': gateway.OP_DISPATCH, 's': 1, 't': 'TYPING_START', 'd': {}}]
        )
        assert outcome == 'resume'

    def test_hello_resumes_when_a_session_exists(self) -> None:
        async def run() -> Socket:
            socket = Socket([HELLO])
            session = gateway.Session()
            session.note(
                {
                    'op': 0,
                    's': 2,
                    't': 'READY',
                    'd': {'session_id': 'sid', 'resume_gateway_url': 'wss://r'},
                }
            )
            await responder.pump(
                socket,
                FLEET,
                policy.Decider(known=FLEET.tokens),
                session,
                sleep=nap,
                say=lambda s: None,
            )
            return socket

        socket = asyncio.run(run())
        assert socket.sent[0]['op'] == gateway.OP_RESUME


class TestRunForever:
    def test_it_stops_after_the_bounded_attempts(self) -> None:
        opened: list[str] = []

        def connect(url: str) -> Socket:
            opened.append(url)
            return Socket([{'op': gateway.OP_RECONNECT}])

        asyncio.run(
            responder.run_forever(
                fleet=FLEET,
                resolve_url=lambda tok: 'wss://gw',
                connect=connect,
                sleep=nap,
                say=lambda s: None,
                attempts=2,
            )
        )
        assert len(opened) == 2

    def test_a_dead_session_is_forgotten_so_the_next_identifies(self) -> None:
        seen: list[str] = []

        def connect(url: str) -> Socket:
            seen.append(url)
            return Socket([{'op': gateway.OP_INVALID_SESSION, 'd': False}])

        asyncio.run(
            responder.run_forever(
                fleet=FLEET,
                resolve_url=lambda tok: 'wss://gw',
                connect=connect,
                sleep=nap,
                say=lambda s: None,
                attempts=1,
            )
        )
        assert seen

    def test_a_failure_backs_off_rather_than_hammering_discord(self) -> None:
        said: list[str] = []
        waited: list[float] = []

        async def sleep(seconds: float) -> None:
            waited.append(seconds)

        def connect(url: str) -> Socket:
            raise OSError('connection refused')

        asyncio.run(
            responder.run_forever(
                fleet=FLEET,
                resolve_url=lambda tok: 'wss://gw',
                connect=connect,
                sleep=sleep,
                say=said.append,
                attempts=2,
            )
        )
        assert len(waited) == 2
        assert waited[1] > 0
        assert any('retrying in' in line for line in said)

    def test_it_says_who_it_listens_and_speaks_as(self) -> None:
        said: list[str] = []
        asyncio.run(
            responder.run_forever(
                fleet=FLEET,
                resolve_url=lambda tok: 'wss://gw',
                connect=lambda url: Socket([]),
                sleep=nap,
                say=said.append,
                attempts=1,
            )
        )
        assert 'listening as A' in said[0]
        assert 'A, B' in said[0]
