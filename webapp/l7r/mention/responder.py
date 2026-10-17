"""Tie the pieces together: listen, decide, reply, and survive the night.

`run_forever` is the process. Everything it decides comes from `policy` and
`rules`; everything it touches comes from `gateway`. The loop itself is small on
purpose, because the parts worth trusting are the ones that can be tested
synchronously.
"""

from __future__ import annotations

import asyncio
import collections
import contextlib
import json
import time
from collections.abc import Awaitable, Callable
from typing import Any

from l7r.mention import gateway, rules
from l7r.mention.bots import Fleet, load_fleet
from l7r.mention.memory import Memory
from l7r.mention.policy import Decider


def handle(
    message: dict[str, Any],
    decider: Decider,
    fleet: Fleet,
    *,
    now: float,
    memory: Memory | None = None,
    send: Callable[..., None] = gateway.send_message,
    say: Callable[[str], None] = print,
) -> list[str]:
    """Answer one message if it should be answered. Returns the bots that spoke.

    Synchronous and injectable, so every rule that matters - the bot guard, the
    rate limit, who replies - is testable without a socket.
    """
    targets = decider.should_answer(message, now)
    if not targets:
        return []
    channel = str(message.get('channel_id') or '')
    content = str(message.get('content') or '')
    spoke: list[str] = []
    for application_id in targets:
        token = fleet.token_for(application_id)
        if token is None:  # pragma: no cover - should_answer only returns known ids
            continue
        # Per bot, not per message: two bots addressed in one line each answer in
        # their own voice, and each one's memory of this channel is its own.
        reply = rules.respond_to(content, application_id, channel=channel, memory=memory)
        try:
            send(channel, token, reply, reply_to=str(message.get('id') or ''))
        except Exception as exc:  # noqa: BLE001 - a failed reply must not kill the loop
            say(f'  ! could not reply as {application_id} in {channel}: {exc}')
            continue
        spoke.append(application_id)
    return spoke


#: What a player sees if the lookup could not be loaded at all on this box.
LOOKUP_UNAVAILABLE = 'The lookup is not available right now. The GM knows how to fix it.'

#: Interaction ids already answered. A gateway RESUME replays events, and a
#: replayed interaction must not be answered twice (its token has usually
#: expired anyway, which is the other half of the guard - see answer_interaction).
Seen = collections.deque[str]


def load_lookup(say: Callable[[str], None] = print) -> Any:
    """The `/look-up` service, or None if it cannot be built on this box.

    Imported lazily so the mention responder never depends on the lookup
    package to start: a broken glossary must not silence the jokes."""
    try:
        from l7r.lookup import service

        lookup = service.build()
    except Exception as exc:  # noqa: BLE001 - report and carry on without /look-up
        say(f'  ! /look-up unavailable ({type(exc).__name__}: {exc}); it will say so')
        return None
    state = 'key present' if lookup.settings.key else 'NO KEY - it will say it is not set up'
    say(f'/look-up ready: {lookup.settings.model}, {state}')
    return lookup


def answer_interaction(
    interaction: dict[str, Any],
    lookup: Any,
    seen: Seen,
    *,
    defer: Callable[..., None] = gateway.defer_ephemeral,
    edit: Callable[..., None] = gateway.edit_original,
    say: Callable[[str], None] = print,
) -> str | None:
    """Answer one `/look-up`, privately. Returns the reply sent, or None.

    Runs in a worker thread (pump uses asyncio.to_thread) because the model call
    takes a second or more, and a blocked event loop stops the heartbeat. Every
    Discord call is wrapped: a replayed interaction's token has expired and its
    acknowledgement fails, which must cost one log line, never the loop."""
    data = interaction.get('data') or {}
    if interaction.get('type') != 2 or data.get('name') != gateway.LOOKUP:
        return None
    user = (interaction.get('member') or {}).get('user') or interaction.get('user') or {}
    if user.get('bot'):
        return None  # the same guard as the mention path: never answer a bot
    interaction_id = str(interaction.get('id') or '')
    token = str(interaction.get('token') or '')
    if not interaction_id or interaction_id in seen:
        return None
    seen.append(interaction_id)
    try:
        defer(interaction_id, token)
    except Exception as exc:  # noqa: BLE001 - see the docstring
        say(f'  ! could not acknowledge /look-up {interaction_id}: {exc}')
        return None
    question = next(
        (str(o.get('value', '')) for o in data.get('options') or [] if o.get('name') == 'question'),
        '',
    )
    if lookup is None:
        text = LOOKUP_UNAVAILABLE
    else:
        text = lookup.answer(
            question, str(user.get('id', '')), asker=str(user.get('username', ''))
        ).text
    try:
        edit(str(interaction.get('application_id', '')), token, text)
    except Exception as exc:  # noqa: BLE001 - see the docstring
        say(f'  ! could not deliver /look-up {interaction_id}: {exc}')
        return None
    say(f'  -> /look-up for {user.get("username")}: {question!r}')
    return text


async def pump(
    socket: Any,
    fleet: Fleet,
    decider: Decider,
    session: gateway.Session,
    *,
    memory: Memory | None = None,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    clock: Callable[[], float] = time.monotonic,
    send: Callable[..., None] = gateway.send_message,
    say: Callable[[str], None] = print,
    lookup: Any = None,
    seen: Seen | None = None,
    defer: Callable[..., None] = gateway.defer_ephemeral,
    edit: Callable[..., None] = gateway.edit_original,
) -> str:
    """Run one connection until it ends. Returns why, so the caller can decide.

    'resume' means reconnect keeping the session; 'restart' means the session is
    gone and the next connection must identify afresh.
    """
    beat: asyncio.Task[None] | None = None
    seen = seen if seen is not None else collections.deque(maxlen=500)
    lookups: set[asyncio.Task[str | None]] = set()
    try:
        async for raw in socket:
            payload = json.loads(raw)
            session.note(payload)
            op = payload.get('op')
            if op == gateway.OP_HELLO:
                interval = float((payload.get('d') or {}).get('heartbeat_interval', 41250))
                if session.resumable:
                    await socket.send(json.dumps(gateway.resume(fleet.listener_token, session)))
                else:
                    await socket.send(json.dumps(gateway.identify(fleet.listener_token)))
                beat = asyncio.create_task(
                    gateway.heartbeat_forever(socket, session, interval, sleep)
                )
            elif op == gateway.OP_RECONNECT:
                return 'resume'
            elif op == gateway.OP_INVALID_SESSION:
                return 'resume' if payload.get('d') is True else 'restart'
            elif op == gateway.OP_DISPATCH and payload.get('t') == 'INTERACTION_CREATE':
                task = asyncio.create_task(
                    asyncio.to_thread(
                        answer_interaction,
                        payload.get('d') or {},
                        lookup,
                        seen,
                        defer=defer,
                        edit=edit,
                        say=say,
                    )
                )
                lookups.add(task)
                task.add_done_callback(lookups.discard)
            elif op == gateway.OP_DISPATCH and payload.get('t') == 'MESSAGE_CREATE':
                message = payload.get('d') or {}
                for application_id in handle(
                    message, decider, fleet, now=clock(), memory=memory, send=send, say=say
                ):
                    say(
                        f'  -> {application_id} replied in {message.get("channel_id")} '
                        f'to {(message.get("author") or {}).get("username")}'
                    )
    finally:
        if beat is not None:
            beat.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await beat
        # Let an answer already being written finish: its token outlives this
        # connection, and the player is waiting on it.
        await asyncio.gather(*lookups, return_exceptions=True)
    return 'resume'


async def run_forever(
    *,
    fleet: Fleet | None = None,
    connect: Callable[..., Any] | None = None,
    resolve_url: Callable[[str], str] = gateway.gateway_url,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    say: Callable[[str], None] = print,
    attempts: int | None = None,
    make_lookup: Callable[[Callable[[str], None]], Any] = load_lookup,
) -> None:
    """Connect, listen, reconnect on failure, forever.

    `attempts` bounds the loop for tests; production passes None and never stops.
    A dropped connection is normal - Discord recycles gateways - so a failure to
    connect backs off rather than retrying instantly.
    """
    from websockets.asyncio.client import connect as ws_connect

    fleet = fleet or load_fleet()
    opener = connect or ws_connect
    decider = Decider(known=dict(fleet.tokens))
    # One memory for the process: it is what keeps a bot from repeating itself and
    # what remembers how far the feud has gone in each channel.
    memory = Memory()
    session = gateway.Session()
    failures = 0
    tries = 0
    say(f'listening as {fleet.listener}; can speak as {", ".join(sorted(fleet.tokens))}')
    # After the "listening as" line, which is the first thing the GM looks for in
    # the journal to see the bot is alive.
    lookup = make_lookup(say)
    seen: Seen = collections.deque(maxlen=500)
    while attempts is None or tries < attempts:
        tries += 1
        # `resumable` guarantees resume_url is set; mypy cannot see that through the
        # property, and asserting the invariant here is better than widening the type.
        url = (
            session.resume_url
            if session.resumable and session.resume_url
            else resolve_url(fleet.listener_token)
        )
        try:
            async with opener(url) as socket:
                failures = 0
                outcome = await pump(
                    socket,
                    fleet,
                    decider,
                    session,
                    memory=memory,
                    sleep=sleep,
                    say=say,
                    lookup=lookup,
                    seen=seen,
                )
            if outcome == 'restart':
                session.forget()
        except Exception as exc:  # noqa: BLE001 - the point is to survive the night
            failures += 1
            delay = gateway.backoff(failures)
            say(f'  ! connection lost ({exc}); retrying in {delay:.1f}s')
            await sleep(delay)
