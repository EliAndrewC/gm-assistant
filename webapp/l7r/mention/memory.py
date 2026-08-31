"""What a bot remembers about a channel: its last line, and the feud.

Two jobs, both small and both per (bot, channel):

  - **FR-003**: never give the same answer twice in a row. Without this, a pool
    of twelve still lands on a repeat about one time in twelve, and a repeat is
    the single thing that makes a bot feel like a lookup table.
  - **FR-007**: how many times a player has RELAYED what the other bot said, so
    the feud can go further the second time rather than the same distance twice.

DELIBERATELY IN-PROCESS AND FORGETFUL. It resets on redeploy, and that is the
right trade for a joke bot - a database would be a bigger commitment than the
feature. The dict is bounded so a busy server cannot grow it without limit; the
oldest key is dropped, which at worst means one repeated line months later.

The relay count refines WHICH tier line is used. It is never the thing that
creates depth on its own - the spec is explicit that a neutral question asked
repeatedly must not reach the deepest insult (FR-007, and the fidelity review
rejected an earlier design that let exactly that happen).
"""

from __future__ import annotations

from collections import OrderedDict

#: Distinct (bot, channel) pairs held before the oldest is dropped.
KEYS = 400


class Memory:
    """Per-bot, per-channel state. Not thread-safe; the responder is one task."""

    def __init__(self, keys: int = KEYS) -> None:
        self._last: OrderedDict[tuple[str, str], str] = OrderedDict()
        self._relays: OrderedDict[tuple[str, str], int] = OrderedDict()
        self._keys = keys

    @staticmethod
    def _key(application_id: str | None, channel: str | None) -> tuple[str, str]:
        return (application_id or '', channel or '')

    def _trim(self, store: OrderedDict[tuple[str, str], object]) -> None:
        while len(store) > self._keys:
            store.popitem(last=False)

    def last_reply(self, application_id: str | None, channel: str | None) -> str | None:
        """The previous thing this bot said here, or None."""
        return self._last.get(self._key(application_id, channel))

    def remember_reply(self, application_id: str | None, channel: str | None, reply: str) -> None:
        key = self._key(application_id, channel)
        self._last[key] = reply
        self._last.move_to_end(key)
        self._trim(self._last)  # type: ignore[arg-type]

    def relays(self, application_id: str | None, channel: str | None) -> int:
        """How many times the feud has been stoked here by relaying gossip."""
        return self._relays.get(self._key(application_id, channel), 0)

    def note_relay(self, application_id: str | None, channel: str | None) -> int:
        """Count one relay and return the new total."""
        key = self._key(application_id, channel)
        total = self._relays.get(key, 0) + 1
        self._relays[key] = total
        self._relays.move_to_end(key)
        self._trim(self._relays)  # type: ignore[arg-type]
        return total
