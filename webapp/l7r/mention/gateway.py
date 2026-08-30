"""The Discord gateway connection, and the REST call that replies.

This is the only module that touches the network. Everything it decides is
decided in `policy.py` and `rules.py`, which are synchronous and pure, so the
guards that keep this thing safe are testable without a socket.

THE PROTOCOL, briefly, because a reader should not have to go and look it up:

1. `GET /gateway/bot` gives a websocket URL.
2. Connect, and Discord sends HELLO (op 10) carrying `heartbeat_interval`.
3. Send IDENTIFY (op 2) with the token and the intents, or RESUME (op 6) with a
   session id and the last sequence number if reconnecting.
4. Heartbeat (op 1) forever at the interval, echoing the last sequence seen.
5. Events arrive as op 0 with a `t` naming them; `MESSAGE_CREATE` is the one we
   want. READY carries the session id and the URL to resume against.
6. Discord may send RECONNECT (op 7) or INVALID_SESSION (op 9) at any time. The
   first means reconnect and resume; the second means the session is gone - resume
   only if it says the session is resumable, otherwise identify afresh.

Resuming REPLAYS events that may already have been handled, which is why
`policy.Decider` remembers message ids across reconnects (FR-007).
"""

from __future__ import annotations

import json
import random
import urllib.request
from collections.abc import Awaitable, Callable
from typing import Any

API = 'https://discord.com/api/v10'

USER_AGENT = 'L7RMentionResponder (https://github.com/EliAndrewC/gm-assistant, 0.1)'

#: GUILD_MESSAGES (1 << 9) | MESSAGE_CONTENT (1 << 15). Nothing else is needed:
#: this process reads messages and replies over REST, so it wants no member,
#: presence or voice state, and asking for them would be both slower and ruder.
INTENTS = (1 << 9) | (1 << 15)

OP_DISPATCH = 0
OP_HEARTBEAT = 1
OP_IDENTIFY = 2
OP_RESUME = 6
OP_RECONNECT = 7
OP_INVALID_SESSION = 9
OP_HELLO = 10
OP_HEARTBEAT_ACK = 11

#: Backoff between reconnection attempts, in seconds. Doubling with a cap, plus
#: jitter, because a fleet of bots all retrying in lockstep after a Discord blip is
#: how a service gets hammered - the thing "conform to however Discord expects that
#: bots will work" is asking us not to do.
BACKOFF_START = 1.0
BACKOFF_CAP = 60.0


def gateway_url(token: str, opener: Callable[..., Any] = urllib.request.urlopen) -> str:
    """The websocket URL to connect to, from `GET /gateway/bot`."""
    request = urllib.request.Request(
        f'{API}/gateway/bot',
        headers={'Authorization': f'Bot {token}', 'User-Agent': USER_AGENT},
    )
    with opener(request, timeout=20) as response:
        return f'{json.load(response)["url"]}?v=10&encoding=json'


def send_message(
    channel_id: str,
    token: str,
    content: str,
    *,
    reply_to: str | None = None,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> None:
    """Post a reply AS the bot whose token this is.

    `allowed_mentions` is empty on purpose: a reply that pings people is a reply
    that can start an argument with another bot, and nothing the responder says
    needs to notify anyone. It also means a joke containing an `@` cannot become a
    mention.
    """
    payload: dict[str, Any] = {'content': content, 'allowed_mentions': {'parse': []}}
    if reply_to:
        # fail_if_not_exists: a deleted message must not turn the reply into an error.
        payload['message_reference'] = {'message_id': reply_to, 'fail_if_not_exists': False}
    request = urllib.request.Request(
        f'{API}/channels/{channel_id}/messages',
        data=json.dumps(payload).encode(),
        headers={
            'Authorization': f'Bot {token}',
            'User-Agent': USER_AGENT,
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    with opener(request, timeout=20):
        return


def backoff(attempt: int, jitter: Callable[[], float] = random.random) -> float:
    """Seconds to wait before retry `attempt`, doubling to a cap, with jitter."""
    base: float = min(BACKOFF_START * (2**attempt), BACKOFF_CAP)
    return float(base * (0.5 + 0.5 * jitter()))


class Session:
    """One connection's worth of state: what to resume with, and where."""

    def __init__(self) -> None:
        self.session_id: str | None = None
        self.sequence: int | None = None
        self.resume_url: str | None = None

    def note(self, payload: dict[str, Any]) -> None:
        if payload.get('s') is not None:
            self.sequence = int(payload['s'])
        if payload.get('t') == 'READY':
            data = payload.get('d') or {}
            self.session_id = data.get('session_id')
            self.resume_url = f'{data.get("resume_gateway_url", "")}?v=10&encoding=json'

    @property
    def resumable(self) -> bool:
        return bool(self.session_id and self.sequence is not None and self.resume_url)

    def forget(self) -> None:
        self.session_id = None
        self.sequence = None
        self.resume_url = None


def identify(token: str) -> dict[str, Any]:
    return {
        'op': OP_IDENTIFY,
        'd': {
            'token': token,
            'intents': INTENTS,
            'properties': {'os': 'linux', 'browser': 'l7r-mention', 'device': 'l7r-mention'},
        },
    }


def resume(token: str, session: Session) -> dict[str, Any]:
    return {
        'op': OP_RESUME,
        'd': {'token': token, 'session_id': session.session_id, 'seq': session.sequence},
    }


async def heartbeat_forever(
    socket: Any, session: Session, interval_ms: float, sleep: Callable[[float], Awaitable[None]]
) -> None:
    """Heartbeat until cancelled. Discord closes the socket if this stops."""
    while True:
        await sleep(interval_ms / 1000.0)
        await socket.send(json.dumps({'op': OP_HEARTBEAT, 'd': session.sequence}))
