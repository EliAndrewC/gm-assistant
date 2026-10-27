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
    from l7r.repl.rolls.sheet import Ceilings, KnackHolder

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
    #: The GM has said what this hidden-opposition roll got the players - in
    #: `annotate()` (Enter keeps the default) or with `detected()`. Until then an
    #: interrogation roll the tool reckons DETECTED waits, like an unannotated roll
    #: (GM 2026-09-29: the default was being written with no chance to say otherwise).
    outcome_settled: bool = False
    #: The ROLLER's own ceiling on this skill, read off their character sheet when the
    #: roll is collected (`sheet.roll_ceilings`). Withdrawn (`rules/08-disadvantages.md`):
    #: *"your etiquette and open sincerity rolls are never considered to be higher than
    #: 15"*. The GM (2026-09-29) wants it applied without the player having to say so,
    #: so a typed `34 Etiquette` is written as 15 whatever the parser read. `ceiling`
    #: holds on every roll of the skill; `open_ceiling` only on an OPEN roll, which is
    #: how the sheet itself scopes Withdrawn's sincerity half. The raw `total` is kept.
    ceiling: int | None = None
    open_ceiling: int | None = None
    #: Feature 214. An Isawa Ishi 3rd Dan boost on this roll, ALREADY FOLDED INTO
    #: `total`, and who made it. Folded in because every recording rule - rounding,
    #: the Etiquette cap, ceilings, the contest margin - reads `total` at render
    #: time, so a 13 boosted by 8 renders from 21 even after a 10 was written (the
    #: GM's own example). Kept beside it for once-per-roll and `cancel_boost()`.
    boost: int = 0
    boosted_by: str = ''
    #: Feature 230. An OPPOSE roll's target: the id of the member whose Air / Water
    #: rolls it taxes. The primary when it is seen (GM 2026-10-26: *"default it to
    #: the primary with a way for me to move it"* - `move_oppose`), '' for none.
    against: str = ''
    #: Feature 230. A CONTESTED roll's opposing NPC, by name: the member whose roll
    #: `annotate()` paired with it. Empty means the conversation's primary, which is
    #: what every roll before this feature meant.
    npc: str = ''

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


@dataclass(slots=True)
class Boost:
    """An Isawa Ishi 3rd Dan roll (feature 214): Xk1 added to ANOTHER character's roll.

    `target_message_id` is the Discord message it was aimed at - by the sheet bot's
    message command, or by posting it as a reply - and is empty for a free-floating
    one. `applied_to` is the index into `Conversation.rolls` once it has been added;
    until then it is HELD, `held_because` says why, and `annotate()` asks.
    """

    character: str
    total: int
    message_id: str
    at: datetime
    target_message_id: str = ''
    applied_to: int | None = None
    held_because: str = ''
    discarded: bool = False

    @property
    def held(self) -> bool:
        return self.applied_to is None and not self.discarded


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
class VoidSpend:
    """One void point answer the GM gave while a conversation was open (feature 217).

    `earlier` is the disagreement prompt's "The previous roll spent N": the roll the
    record was read from spent them, not `entry`, so `entry` only says which skill.
    """

    entry: GmRoll
    count: int
    earlier: bool = False


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


@dataclass(slots=True)
class Member:
    """One NPC in a conversation (feature 230), and what is about THAT NPC alone.

    The first member is the PRIMARY: the conversation's public lines go to their bio for
    the whole conversation, whoever joins or leaves (GM 2026-10-26). Everything here is
    written to this member's own GM-only notes. `handle` is the name the member answers
    to at the prompt (`souma`); `present` turns False when they leave.
    """

    npc: Mapping[str, object]
    handle: str = ''
    present: bool = True
    numbers: dict[str, int] = field(default_factory=dict)
    schools: tuple[str, ...] = ()
    numbers_written: dict[str, int] = field(default_factory=dict)
    hidden_written: tuple[str, ...] = ()
    void_written: tuple[str, ...] = ()
    discern: dict[int, DiscernEntry] = field(default_factory=dict)
    honor: float | None = None

    @property
    def name(self) -> str:
        return str(self.npc.get('name') or '')

    @property
    def id(self) -> str:
        return str(self.npc.get('id') or '')


@dataclass(frozen=True, slots=True)
class Event:
    """A member joined or left the conversation, at `at` (feature 230)."""

    member: str
    kind: Literal['joined', 'left']
    at: datetime


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
    #: The lines of questioning the GM has declared, in order.
    lines: list[Line] = field(default_factory=list)
    #: Feature 212. The id minted when the conversation opens - the marker a Discern
    #: Honor record carries so this conversation can advance it only once - and what
    #: each PC with the knack will be told, decided at open and never recomputed
    #: (`Member.discern`; feature 230 made it per NPC).
    conversation_id: str = ''
    #: The gaming groups whose sheet-side conversation was opened successfully -
    #: the only ones worth polling or closing - and whether a failed poll has been
    #: reported yet, so an unreachable app complains once and not every 20 seconds.
    discern_groups: tuple[int, ...] = ()
    discern_complained: bool = False
    #: Feature 230. The knack-holders found at the open, and what a RESUMED sheet
    #: conversation had already served, by (member id, sheet character id) - so a
    #: member who joins later is planned against the same people, and nobody's first
    #: read is re-rolled.
    discern_holders: tuple[KnackHolder, ...] = ()
    discern_served: dict[tuple[str, int], float] = field(default_factory=dict)
    #: Recorded rolls (character, skill, total, time) already joined to a Discord
    #: image. A recorded roll backs AT MOST ONE message: measured 2026-09-29, a player
    #: posted a paw-print picture 90 s after their `/etiquette` card, the join's 300 s
    #: window matched the same recorded roll again, and Yudai was written twice.
    joined: set[tuple[str, str, int, str]] = field(default_factory=set)
    #: Every Discord message id collected, so a forward of a message this conversation
    #: already read (from one watched channel into another) is not read twice.
    consumed: set[str] = field(default_factory=set)
    #: Each collected message's `edited_timestamp` as last read ('' = never edited), so
    #: a player's later correction of a typed roll is noticed (`conversation.revise`).
    edited: dict[str, str] = field(default_factory=dict)
    #: Each roller's sheet ceilings, by sheet id, fetched once per conversation.
    ceilings: dict[int, Ceilings] = field(default_factory=dict)
    #: What the GM said the conversation is about - `begin_conversation("Otsuki",
    #: "confrontation on the Imperial road")` - written as a heading over its lines so
    #: one conversation's rolls can be told from the next one's. Empty for none.
    title: str = ''
    #: Feature 214. Every Isawa Ishi 3rd Dan boost seen, applied or held.
    boosts: list[Boost] = field(default_factory=list)
    #: EVERY Sincerity roll the GM made for the NPC while this conversation was open,
    #: with the id of the line of questioning current when it was rolled (None before
    #: the first) - not only the one handed to `new_line_of_questioning`. The GM
    #: (2026-10-04): a roll made on its own was being written nowhere. A roll handed
    #: to a declaration leaves this list (`hidden.claim`); `hidden.line_roll` derives
    #: which of the rest opposes each line, and `hidden.entries` writes them all.
    sincerity_rolls: list[tuple[GmRoll, int | None]] = field(default_factory=list)
    #: The `GmRoll.seq` of each of those the watcher has already told the GM about.
    sincerity_announced: set[int] = field(default_factory=set)
    #: Feature 217. Every void point the GM marked while this conversation was open -
    #: `tact(vp)` or the `[v]` answer - and the `Void points spent:` entries last
    #: written for them. The GM (2026-10-17): before a fight they need *"all of the
    #: conversations in which the NPC has spent void points"*.
    void_spends: list[VoidSpend] = field(default_factory=list)
    #: Feature 230. Every NPC in the conversation, PRIMARY FIRST, present or departed.
    #: The per-NPC state lives on each `Member`; the properties below hand the
    #: primary's to every caller that predates the feature, which is what keeps a
    #: one-NPC conversation unchanged (FR-012).
    members: list[Member] = field(default_factory=list)
    #: Feature 230. Who joined or left, and when - written into the bio as markers.
    events: list[Event] = field(default_factory=list)
    #: Feature 230. The conversation has had more than one member, at some point. A
    #: bare tag then waits for its NPC to be settled (`npcskills.settle_pending`).
    ever_multi: bool = False

    def __post_init__(self) -> None:
        if not self.members:
            self.members.append(Member(self.npc))

    @property
    def primary(self) -> Member:
        return self.members[0]

    def member(self, member_id: str) -> Member:
        """The member with this Obsidian Portal id; KeyError when there is none."""
        for found in self.members:
            if found.id == member_id:
                return found
        raise KeyError(member_id)

    def owner(self, entry: GmRoll) -> Member:
        """The member a GM roll was made for; an unsettled one reads as the primary's."""
        try:
            return self.member(entry.npc) if entry.npc else self.primary
        except KeyError:  # an older conversation's NPC: reads as before the feature
            return self.primary

    @property
    def present(self) -> list[Member]:
        return [m for m in self.members if m.present]

    @property
    def numbers(self) -> dict[str, int]:
        return self.primary.numbers

    @numbers.setter
    def numbers(self, value: dict[str, int]) -> None:
        self.primary.numbers = value

    @property
    def schools(self) -> tuple[str, ...]:
        return self.primary.schools

    @schools.setter
    def schools(self, value: tuple[str, ...]) -> None:
        self.primary.schools = value

    @property
    def numbers_written(self) -> dict[str, int]:
        return self.primary.numbers_written

    @numbers_written.setter
    def numbers_written(self, value: dict[str, int]) -> None:
        self.primary.numbers_written = value

    @property
    def hidden_written(self) -> tuple[str, ...]:
        return self.primary.hidden_written

    @hidden_written.setter
    def hidden_written(self, value: tuple[str, ...]) -> None:
        self.primary.hidden_written = value

    @property
    def void_written(self) -> tuple[str, ...]:
        return self.primary.void_written

    @void_written.setter
    def void_written(self, value: tuple[str, ...]) -> None:
        self.primary.void_written = value

    @property
    def discern(self) -> dict[int, DiscernEntry]:
        return self.primary.discern

    @discern.setter
    def discern(self, value: dict[int, DiscernEntry]) -> None:
        self.primary.discern = value

    @property
    def honor(self) -> float | None:
        return self.primary.honor

    @honor.setter
    def honor(self, value: float | None) -> None:
        self.primary.honor = value

    def planned(self, pc: str, member: str = '') -> Record | None:
        """What `pc` (a given name, any case) is told about a member (the primary by
        default) in this conversation, if decided."""
        who = self.member(member) if member else self.primary
        for entry in who.discern.values():
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
