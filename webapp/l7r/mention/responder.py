"""Tie the pieces together: listen, decide, reply, and survive the night.

`run_forever` is the process. Everything it decides comes from `policy` and
`rules`; everything it touches comes from `gateway`. The loop itself is small on
purpose, because the parts worth trusting are the ones that can be tested
synchronously.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import time
from collections.abc import Awaitable, Callable
from typing import Any

from l7r.mention import gateway, rules
from l7r.mention.bots import Fleet, load_fleet
from l7r.mention.policy import Decider


def handle(
    message: dict[str, Any],
    decider: Decider,
    fleet: Fleet,
    *,
    now: float,
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
    reply = rules.respond_to(str(message.get('content') or ''))
    spoke: list[str] = []
    for application_id in targets:
        token = fleet.token_for(application_id)
        if token is None:  # pragma: no cover - should_answer only returns known ids
            continue
        try:
            send(channel, token, reply, reply_to=str(message.get('id') or ''))
        except Exception as exc:  # noqa: BLE001 - a failed reply must not kill the loop
            say(f'  ! could not reply as {application_id} in {channel}: {exc}')
            continue
        spoke.append(application_id)
    return spoke


async def pump(
    socket: Any,
    fleet: Fleet,
    decider: Decider,
    session: gateway.Session,
    *,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    clock: Callable[[], float] = time.monotonic,
    send: Callable[..., None] = gateway.send_message,
    say: Callable[[str], None] = print,
) -> str:
    """Run one connection until it ends. Returns why, so the caller can decide.

    'resume' means reconnect keeping the session; 'restart' means the session is
    gone and the next connection must identify afresh.
    """
    beat: asyncio.Task[None] | None = None
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
            elif op == gateway.OP_DISPATCH and payload.get('t') == 'MESSAGE_CREATE':
                message = payload.get('d') or {}
                for application_id in handle(
                    message, decider, fleet, now=clock(), send=send, say=say
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
    return 'resume'


async def run_forever(
    *,
    fleet: Fleet | None = None,
    connect: Callable[..., Any] | None = None,
    resolve_url: Callable[[str], str] = gateway.gateway_url,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    say: Callable[[str], None] = print,
    attempts: int | None = None,
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
    session = gateway.Session()
    failures = 0
    tries = 0
    say(f'listening as {fleet.listener}; can speak as {", ".join(sorted(fleet.tokens))}')
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
                outcome = await pump(socket, fleet, decider, session, sleep=sleep, say=say)
            if outcome == 'restart':
                session.forget()
        except Exception as exc:  # noqa: BLE001 - the point is to survive the night
            failures += 1
            delay = gateway.backoff(failures)
            say(f'  ! connection lost ({exc}); retrying in {delay:.1f}s')
            await sleep(delay)
