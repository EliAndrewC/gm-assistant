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
from typing import TYPE_CHECKING, Literal

from l7r.repl.gmrolls import GmRoll

if TYPE_CHECKING:
    from l7r.repl.honor import Record

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
    #: True when the GM marked this a mistake in `annotate()`. Never written, never
    #: offered again, and never holds the conversation open.
    discarded: bool = False
    #: Contest bonuses, kept PER SIDE and never netted. The GM's reason: *"a player
    #: whose Opponent received two free raises should not have this reflected by
    #: having minus ten applied to their own roll because the value of their own roll
    #: is still significant in and of itself. It makes a difference whether they got
    #: a 30 or a 40."* A bonus to the NPC raises the NPC's total; it never lowers
    #: the player's.
    bonus_self: int = 0
    bonus_opposed: int = 0
    #: The total of the GM's opposing roll when this was contested; None when open.
    #: Stored as a bare number rather than a reference to the GM roll because the
    #: winner and margin are derived at render time and nothing else needs the dice.
    #: IGNORED for an Interrogation roll, along with both bonuses: that skill is
    #: never written against its opposing roll (feature 206).
    opposed_total: int | None = None
    #: Feature 206. The line of questioning this INTERROGATION roll belongs to - a
    #: small id unique within the conversation, None until annotated and always None
    #: for any other skill. A line of questioning is DERIVED: it is the set of rolls
    #: sharing this id, with its note and grilling flag read off them. There is no
    #: Line object, so the annotate menu's stage-then-commit and Ctrl-C-discards-all
    #: need no second code path (specs/206, research R2). The cost is that the note
    #: and flag are duplicated across every roll on the line.
    line: int | None = None
    #: Whether the interrogator was grilling on this roll's line. The players know
    #: this, so it is the ONE conditional Sincerity bonus that may be written - as a
    #: flag, never as a number. Meaningless when `line` is None.
    grilling: bool = False
    #: Feature 207. What the players GOT from a hidden-opposition roll (interrogation,
    #: acting), in the GM's words. Empty means the skill's default outcome - which is
    #: what makes a truthful NPC, a good liar and an NPC never rolled for write the
    #: SAME line. Rollers on one line of questioning are grouped by this.
    outcome: str = ''
    #: Feature 207. The GM was asked for this roll's rank and had none to give, so
    #: `annotate()` stops asking. Only meaningful while `rank` is None.
    rank_settled: bool = False

    @property
    def annotated(self) -> bool:
        return bool(self.note.strip())

    @property
    def final_total(self) -> int:
        """This side's total after its OWN contest bonus."""
        return self.total + self.bonus_self

    @property
    def final_opposed(self) -> int | None:
        """The opposing side's total after ITS own contest bonus."""
        if self.opposed_total is None:
            return None
        return self.opposed_total + self.bonus_opposed

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


@dataclass(slots=True)
class Line:
    """One line of questioning, DECLARED by the GM (feature 207).

    Feature 206 derived a line purely from the rolls sharing an id, and rendering
    still does. This object exists beside that because a declared line may have no
    rolls yet, and because it owns the one thing a roll must never carry: the NPC's
    hidden Sincerity roll. `sincerity` is the GM's live roll (so a later `_ + 15`
    counts) or a bare total; None when the NPC was simply telling the truth.
    """

    id: int
    description: str
    at: datetime
    grilling: bool = False
    sincerity: GmRoll | int | None = None


@dataclass(slots=True)
class DiscernEntry:
    """One PC's Discern Honor answer for one conversation (feature 212).

    `record` is the PC's Obsidian Portal line AS IT WILL READ once they ask - decided
    when the conversation opens, so that asking is a lookup and cannot give two
    answers. It is written only if `asked` becomes true; otherwise it is forgotten,
    and the d10 rolled for a first read with it.
    """

    character_id: int
    pc: str
    group: int
    record: Record
    asked: bool = False
    committed: bool = False


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
    #: Feature 207. The NPC's rings and skill ranks - the LOCAL copy, loaded from the
    #: GM-only notes when the conversation begins and checked against at once,
    #: whether or not it has been persisted yet (the GM: *"we will have updated our
    #: local cache even if we have not yet persisted it to Obsidian Portal"*).
    numbers: dict[str, int] = field(default_factory=dict)
    #: The schools the NPC's record names that roll an extra die on something.
    schools: tuple[str, ...] = ()
    #: The lines of questioning the GM has declared, in order.
    lines: list[Line] = field(default_factory=list)
    #: What was last persisted to the GM-only notes, so an unchanged tick writes
    #: nothing: the numbers, and this conversation's hidden-roll entries.
    numbers_written: dict[str, int] = field(default_factory=dict)
    hidden_written: tuple[str, ...] = ()
    #: Feature 212. The id minted when the conversation opens - the marker a Discern
    #: Honor record carries so this conversation can advance it only once - and what
    #: each PC with the knack will be told, decided at open and never recomputed.
    conversation_id: str = ''
    discern: dict[int, DiscernEntry] = field(default_factory=dict)
    #: The NPC's true Honor as read at open. Never leaves this process.
    honor: float | None = None
    #: The gaming groups whose sheet-side conversation was opened successfully -
    #: the only ones worth polling or closing - and whether a failed poll has been
    #: reported yet, so an unreachable app complains once and not every 20 seconds.
    discern_groups: tuple[int, ...] = ()
    discern_complained: bool = False

    def planned(self, pc: str) -> Record | None:
        """What `pc` (a given name, any case) is told in this conversation, if decided."""
        for entry in self.discern.values():
            if entry.pc.lower() == pc.lower():
                return entry.record
        return None

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
