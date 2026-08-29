"""The entities. Everything here is pure data; the behavior lives in `rules.py`.

`Roll.total` is deliberately NOT decomposed into dice plus bonuses. The
character-sheet app owns the dice math and this feature never reimplements it
(see the repository split recorded in `specs/201-discord-roll-capture/plan.md`),
and the typed path usually omits the decomposition anyway - `38 Etiquette @3`
states no dice at all. What the GM records is the total after the player's own
bonuses, which is exactly what both paths supply.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

#: Where a roll came from. `recorded` means it was joined to a row in the
#: character-sheet app's roll history and is therefore exact; `typed` means a
#: human wrote it in Discord. On a dedup, `recorded` wins (FR-009).
Source = Literal['recorded', 'typed']


@dataclass(frozen=True, slots=True)
class Roll:
    """One roll by one character."""

    character: str
    skill: str
    total: int
    source: Source
    message_id: str
    at: datetime
    rank: int | None = None
    #: What the roll was FOR, in the GM's words. Empty until annotated. A bare
    #: "Jimen precepts: 25" read back months later tells the GM nothing, which is
    #: the entire reason this field exists.
    note: str = ''
    #: The total of the GM's opposing roll when this was contested; None when open.
    #: Stored as a bare number rather than a reference to the GM roll because the
    #: winner and margin are derived at render time and nothing else needs the dice.
    opposed_total: int | None = None

    @property
    def annotated(self) -> bool:
        return bool(self.note.strip())

    @property
    def contested(self) -> bool:
        return self.opposed_total is not None

    @property
    def attributed(self) -> bool:
        """False when we could not name the character.

        An unattributed roll is reported to the GM and kept out of the line
        (FR-020): the GM's format pairs every total with a name, so a nameless
        total has nowhere to go.
        """
        return bool(self.character.strip())


@dataclass(frozen=True, slots=True)
class Contest:
    """Two rolls on opposing sides, plus what the GM's rule derives from them.

    Both totals stay unrounded. The GM was explicit: *"The difference between the
    rolls is rounded down to an increment of five, but the rolls themselves are
    not rounded."*
    """

    left: Roll
    right: Roll
    winner: str | None
    margin: int

    @property
    def tied(self) -> bool:
        return self.winner is None


@dataclass(frozen=True, slots=True)
class RecordingRule:
    """How a raw total becomes the number written down.

    This is data rather than code so that a further rule is a data change
    (FR-013, SC-006): another capped skill is one more entry in `caps`.
    """

    increment: int = 5
    caps: Mapping[str, int] = field(default_factory=lambda: {'etiquette': 40})


@dataclass(slots=True, repr=False)
class Conversation:
    """The one piece of mutable state in the feature. At most one is open.

    `npc` is the matched Obsidian Portal record, so it carries the id the write
    needs. `last_seen` maps channel id -> newest message already consumed, which
    makes polling incremental and has to be PER CHANNEL: a conversation watches
    every monitored channel at once, and one cursor shared between them would let
    a busy channel drag the others past unread messages.
    """

    npc: Mapping[str, object]
    opened_at: datetime
    channels: tuple[str, ...]
    rolls: list[Roll] = field(default_factory=list)
    last_seen: dict[str, str] = field(default_factory=dict)
    unresolved: list[str] = field(default_factory=list)
    #: The lines most recently written to Obsidian Portal - one per skill - so the
    #: next write REPLACES them instead of stacking more under the portrait.
    written: tuple[str, ...] = ()
    #: Monotonic timestamp of that write, for the debounce.
    written_at: float = 0.0

    def __repr__(self) -> str:
        """One line, because the REPL echoes whatever `begin_conversation` returns.

        The generated dataclass repr printed the entire Obsidian Portal record, every
        channel id and every empty field - about 700 characters of noise straight
        after the one line that actually said what happened. The object still carries
        all of it; it just does not shout it.
        """
        rolls = f'{len(self.rolls)} roll' + ('' if len(self.rolls) == 1 else 's')
        watching = f'{len(self.channels)} channel' + ('' if len(self.channels) == 1 else 's')
        return f'<talking to {self.npc_name}: {rolls}, watching {watching}>'

    @property
    def npc_name(self) -> str:
        return str(self.npc.get('name') or '')

    @property
    def npc_id(self) -> str:
        return str(self.npc.get('id') or '')
