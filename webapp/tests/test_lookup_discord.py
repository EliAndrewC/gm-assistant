"""Feature 218: `/look-up` over the gateway - acknowledged privately, answered, never twice."""

from __future__ import annotations

import asyncio
import collections
import io
import json
from typing import Any

import pytest

from l7r.mention import bots, gateway, responder
from l7r.mention.policy import Decider


class Response(io.BytesIO):
    def __enter__(self) -> Response:
        return self

    def __exit__(self, *exc: object) -> None:
        return None


def recording(sent: list[Any]) -> Any:
    def opener(request: Any, timeout: float) -> Response:
        sent.append(request)
        return Response(b'{}')

    return opener


class TestGatewayCalls:
    def test_defer_is_private_and_needs_no_bot_token(self) -> None:
        sent: list[Any] = []
        gateway.defer_ephemeral('42', 'tok', opener=recording(sent))
        request = sent[0]
        assert request.full_url == f'{gateway.API}/interactions/42/tok/callback'
        assert request.get_method() == 'POST'
        assert json.loads(request.data) == {'type': 5, 'data': {'flags': 64}}
        assert request.get_header('Authorization') is None

    def test_edit_suppresses_previews_and_pings(self) -> None:
        sent: list[Any] = []
        gateway.edit_original('app', 'tok', 'hi', opener=recording(sent))
        request = sent[0]
        assert request.full_url == f'{gateway.API}/webhooks/app/tok/messages/@original'
        assert request.get_method() == 'PATCH'
        assert json.loads(request.data) == {
            'content': 'hi',
            'flags': gateway.SUPPRESS_EMBEDS,
            'allowed_mentions': {'parse': []},
        }

    def test_register_is_a_guild_put_with_the_bot_token(self) -> None:
        sent: list[Any] = []
        gateway.register_commands('app', 'guild', 'BOT', [gateway.LOOKUP_COMMAND], recording(sent))
        request = sent[0]
        assert request.full_url == f'{gateway.API}/applications/app/guilds/guild/commands'
        assert request.get_method() == 'PUT'
        assert request.get_header('Authorization') == 'Bot BOT'
        assert json.loads(request.data)[0]['name'] == 'look-up'


def interaction(**kw: Any) -> dict[str, Any]:
    raw: dict[str, Any] = {
        'id': '900',
        'token': 'itok',
        'type': 2,
        'application_id': 'app',
        'member': {'user': {'id': '832', 'username': 'alex'}},
        'data': {'name': 'look-up', 'options': [{'name': 'question', 'value': 'who is our boss?'}]},
    }
    raw.update(kw)
    return raw


class FakeLookup:
    def __init__(self) -> None:
        self.asked: list[tuple[str, str, str]] = []

    def answer(self, question: str, discord_id: str = '', asker: str = '') -> Any:
        self.asked.append((question, discord_id, asker))
        return type('A', (), {'text': f'answer to {question}'})()


class TestAnswerInteraction:
    def run(self, raw: dict[str, Any], lookup: Any = None, **kw: Any) -> tuple[Any, list[Any]]:
        calls: list[Any] = []
        said: list[str] = []
        out = responder.answer_interaction(
            raw,
            lookup,
            kw.pop('seen', collections.deque(maxlen=5)),
            defer=kw.pop('defer', lambda *a: calls.append(('defer', *a))),
            edit=kw.pop('edit', lambda *a: calls.append(('edit', *a))),
            say=said.append,
        )
        return out, calls + said

    def test_acknowledges_then_answers_as_the_asker(self) -> None:
        lookup = FakeLookup()
        out, calls = self.run(interaction(), lookup)
        assert out == 'answer to who is our boss?'
        assert calls[0] == ('defer', '900', 'itok')
        assert calls[1] == ('edit', 'app', 'itok', 'answer to who is our boss?')
        assert lookup.asked == [('who is our boss?', '832', 'alex')]

    def test_a_dm_interaction_carries_user_not_member(self) -> None:
        lookup = FakeLookup()
        raw = interaction(member=None, user={'id': '9', 'username': 'x'})
        self.run(raw, lookup)
        assert lookup.asked[0][1] == '9'

    @pytest.mark.parametrize(
        'raw',
        [
            interaction(type=3),
            interaction(data={'name': 'other'}),
            interaction(member={'user': {'id': '1', 'bot': True}}),
            interaction(id=''),
        ],
    )
    def test_ignores_what_is_not_a_players_look_up(self, raw: dict[str, Any]) -> None:
        out, calls = self.run(raw, FakeLookup())
        assert out is None
        assert calls == []

    def test_a_replay_is_not_answered_twice(self) -> None:
        seen: collections.deque[str] = collections.deque(maxlen=5)
        lookup = FakeLookup()
        self.run(interaction(), lookup, seen=seen)
        out, calls = self.run(interaction(), lookup, seen=seen)
        assert out is None
        assert calls == []
        assert len(lookup.asked) == 1

    def test_an_expired_token_costs_a_log_line_not_the_loop(self) -> None:
        def boom(*a: Any) -> None:
            raise OSError('HTTP Error 404: Unknown interaction')

        lookup = FakeLookup()
        out, calls = self.run(interaction(), lookup, defer=boom)
        assert out is None
        assert 'could not acknowledge' in calls[-1]
        assert lookup.asked == []
        out, calls = self.run(interaction(id='901'), lookup, edit=boom)
        assert out is None
        assert 'could not deliver' in calls[-1]

    def test_no_lookup_says_so(self) -> None:
        out, _ = self.run(interaction(data={'name': 'look-up'}), None)
        assert out == responder.LOOKUP_UNAVAILABLE


class TestLoadLookup:
    def test_reports_the_model_and_key(self) -> None:
        said: list[str] = []
        assert responder.load_lookup(said.append) is not None
        assert said[0].startswith('/look-up ready: ')

    def test_a_broken_lookup_does_not_stop_the_responder(self, monkeypatch: Any) -> None:
        from l7r.lookup import service

        def broken() -> None:
            raise KeyError('lookup')

        monkeypatch.setattr(service, 'build', broken)
        said: list[str] = []
        assert responder.load_lookup(said.append) is None
        assert 'unavailable' in said[0]


class Socket:
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
    await asyncio.sleep(0)


FLEET = bots.Fleet(tokens={'A': 'tok-a'}, listener='A')


def test_pump_answers_an_interaction_in_a_worker_thread() -> None:
    calls: list[Any] = []
    socket = Socket(
        [
            {'op': gateway.OP_HELLO, 'd': {'heartbeat_interval': 1000}},
            {'op': gateway.OP_DISPATCH, 't': 'INTERACTION_CREATE', 's': 1, 'd': interaction()},
        ]
    )
    lookup = FakeLookup()
    outcome = asyncio.run(
        responder.pump(
            socket,
            FLEET,
            Decider(known=FLEET.tokens),
            gateway.Session(),
            sleep=nap,
            say=lambda s: None,
            lookup=lookup,
            defer=lambda *a: calls.append(('defer', *a)),
            edit=lambda *a: calls.append(('edit', *a)),
        )
    )
    assert outcome == 'resume'
    assert [c[0] for c in calls] == ['defer', 'edit']
    assert lookup.asked == [('who is our boss?', '832', 'alex')]


def test_run_forever_builds_the_lookup_once() -> None:
    made: list[int] = []

    def make(say: Any) -> None:
        made.append(1)

    asyncio.run(
        responder.run_forever(
            fleet=FLEET,
            resolve_url=lambda tok: 'wss://gw',
            connect=lambda url: Socket([{'op': gateway.OP_RECONNECT}]),
            sleep=nap,
            say=lambda s: None,
            attempts=2,
            make_lookup=make,
        )
    )
    assert made == [1]
