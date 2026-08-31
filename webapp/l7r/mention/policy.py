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

import re
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


#: A mention as it appears in the raw message text, so its POSITION is knowable.
#: The `mentions` array has no order relative to the prose.
_MENTION_AT = re.compile(r'<@!?(\d+)>')


def addressed_bots(content: str, candidates: list[str]) -> list[str]:
    """Narrow to the bots named before a colon, if a colon addresses anyone.

    The GM's rule (2026-08-31): *"if there is a colon in the message then you only
    have whichever bot comes before the colon respond to it... But if someone puts
    both bots before the : or doesn't have a : in the message then both bots
    respond."* So::

        @GM Assistant: tell me about @Character Sheet   -> only the GM Assistant
        @GM Assistant @Character Sheet: settle this     -> both
        @GM Assistant tell me about @Character Sheet    -> both

    This is what makes it possible to ask ONE bot about the OTHER, which the feud
    needs and which was otherwise impossible: naming the other bot to ask about it
    also summoned it.

    A colon with no bot before it - "listen: @GM Assistant" - narrows nothing.
    Treating that as addressing nobody would silence the bots over punctuation.
    """
    head, colon, _ = content.partition(':')
    if not colon:
        return candidates
    before = [found for found in _MENTION_AT.findall(head) if found in candidates]
    return before or candidates


def mentioned_bots(message: Mapping[str, Any], known: Mapping[str, str]) -> list[str]:
    """Which of the bots we can speak as are being ADDRESSED, in order.

    Only the `mentions` array counts toward being mentioned at all. A role ping or
    `@everyone` reaches the bot but is not addressed TO it (FR-006) - Discord keeps
    those in separate fields (`mention_roles`, `mention_everyone`), so this is their
    distinction, not one we invented. Nobody pinging the room is asking the bot a
    question.

    Then `addressed_bots` applies the colon rule to whoever is left.
    """
    mentions: list[Mapping[str, Any]] = list(message.get('mentions') or [])
    candidates = [str(user.get('id')) for user in mentions if str(user.get('id')) in known]
    return addressed_bots(str(message.get('content') or ''), candidates)


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
