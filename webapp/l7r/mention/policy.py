"""Whether to answer a message at all, and how often.

Everything here is pure and synchronous so the rules that keep the responder safe
can be tested without a socket. The socket is `gateway.py`; the decisions are
here.

THE GUARD THAT MATTERS MOST is `should_answer`'s bot check. The GM has watched
this exact failure take a server down (2026-08-28): *"the bot was carelessly
programmed, so it just kept responding to itself in an infinite loop that was
really bad for the server and made it unusable."* Refusing every message whose
author is a bot makes the loop IMPOSSIBLE rather than unlikely - the reply can
never re-enter the trigger path no matter what it says, and with two bots in play
it also stops one of ours setting off the other.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

#: One reply per channel per this many seconds. FR-005. A burst of mentions is a
#: burst of ONE reply, which is what stops an excited table turning into a wall of
#: bot messages - and it is what "conform to however Discord expects that bots will
#: work" means in practice, since rate limits are their documented expectation.
QUIET_SECONDS = 5.0

#: How many message ids to remember for the duplicate check. A resume replays
#: events the responder may already have handled (FR-007), so ids are remembered
#: across reconnects. Bounded because this process is meant to run for weeks.
SEEN = 500


def is_bot(message: Mapping[str, Any]) -> bool:
    """True when a bot wrote this - including us."""
    author: Mapping[str, Any] = message.get('author') or {}
    return bool(author.get('bot'))


def mentioned_bots(message: Mapping[str, Any], known: Mapping[str, str]) -> list[str]:
    """Which of the bots we can speak as were DIRECTLY mentioned, in order.

    Only the `mentions` array counts. A role ping or `@everyone` reaches the bot
    but is not addressed TO it (FR-006) - Discord keeps those in separate fields
    (`mention_roles`, `mention_everyone`), so this is their distinction, not one we
    invented. Nobody pinging the room is asking the bot a question.
    """
    mentions: list[Mapping[str, Any]] = list(message.get('mentions') or [])
    return [str(user.get('id')) for user in mentions if str(user.get('id')) in known]


@dataclass
class Decider:
    """Should this message be answered, and by whom.

    Holds the two pieces of state that make the answer depend on history: which
    messages have already been handled, and when each channel last heard from us.
    """

    known: Mapping[str, str]
    quiet_seconds: float = QUIET_SECONDS
    _seen: list[str] = field(default_factory=list)
    _last: dict[str, float] = field(default_factory=dict)

    def should_answer(self, message: Mapping[str, Any], now: float) -> list[str]:
        """The bot ids that should reply to this message. Empty means stay quiet."""
        if is_bot(message):
            return []
        message_id = str(message.get('id') or '')
        if not message_id or message_id in self._seen:
            return []
        targets = mentioned_bots(message, self.known)
        if not targets:
            return []
        channel = str(message.get('channel_id') or '')
        if now - self._last.get(channel, float('-inf')) < self.quiet_seconds:
            return []
        self._remember(message_id)
        self._last[channel] = now
        return targets

    def _remember(self, message_id: str) -> None:
        self._seen.append(message_id)
        if len(self._seen) > SEEN:
            del self._seen[: len(self._seen) - SEEN]
