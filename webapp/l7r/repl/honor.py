"""The Discern Honor school knack, tracked on Obsidian Portal.

``discern_honor("Otsuki", "Jimen", rank=2)`` looks the NPC up on OP, reads
their true Honor from the ``Honor: X.Y`` line of the GM-only notes, applies
the knack, records the result back into those notes, and prints what to tell
the player.

THE RULE (``rules/05-school_knacks.md``, "Discern Honor"): the first
conversation tells the player ``honor + 0.5 * (d10 - 5)`` - a flat d10, so
the guess lands 2.0 below to 2.5 above the truth in half-point steps. (The
rules file used to say ``(1k1 - 0.5)``, which would put every first guess ABOVE
the truth; flagged 2026-08-27, and on 2026-09-21 the GM had the rules text
corrected to ``(1k1 - 5)`` "rolled without rerolling 10s".) Each conversation after
the first moves the told value ``0.X`` closer to the truth, X = the PC's rank
in the knack, until it locks in at the true value.

WHY IT IS TRACKED: a second conversation only refines the FIRST answer, so
the GM must know who asked, what they were told, and how many times. The
record is a block in the NPC's ``game_master_info``::

    Discern Honor:
    - Jimen (rank 2): told 4.5 after 1 conversation
    - Kaede (rank 1): told 3.0 after 4 conversations - locked in
    - Makoto (rank 4): told 3.4 after 2 conversations [c-20260921-7f3a, was 3.8]

One line per PC. The bracketed marker (feature 212) names the conversation that
last advanced the record and what the PC had been told before it: a conversation
opened with ``begin_conversation`` advances a record ONCE however often it is
asked, by the player's ``/discern-honor`` or by this function, and
``abandon_conversation`` can undo it. ``l7r/repl/rolls/discern.py`` is that half.

The rank comes from the PC's public character sheet
(``l7r.repl.sheets``, 24 h cache) when the PC is registered there, so
``discern_honor("Otsuki", Jimen)`` needs nothing else; ``rank=`` overrides
it, and is required for a PC with no sheet. Nothing older than this block is
read: the GM ruled (2026-08-27) that no backward compatibility with prose
notes is wanted.

UNCONVENTIONAL / VIRTUE (``rules/08-disadvantages.md``, ``07-advantages.md``):
these belong to the TARGET, so they are read off the NPC's OP notes, never
the PC's sheet (GM 2026-08-27). An NPC listing ``Unconventional`` seems LESS
honorable at first - the first-conversation adjustment is
``- |0.5 * (d10 - 5)|``; one listing ``Virtue`` seems MORE honorable -
``+ |0.5 * (d10 - 5)|``. Otsuki is Unconventional.
"""

from __future__ import annotations

import re
import threading
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from chargen import op
from chargen.opsynth import match_character
from l7r.repl.dice import d10
from l7r.repl.sheets import PC, knack_rank, resolve_pc

if TYPE_CHECKING:
    from l7r.repl.rolls.models import Conversation

HEADING = 'Discern Honor:'

#: Held across every read-modify-write of an NPC's GM-only notes that this module or
#: the conversation watcher makes (feature 212). The watcher's thread commits a
#: PC's record when it sees they asked; the GM's thread can call `discern_honor()`
#: for the same NPC at the same moment; both render the whole block, so the later
#: write would silently drop the earlier one's line.
NOTES_LOCK = threading.RLock()


def d10_flat() -> int:
    """The knack's die: a d10 that does NOT reroll 10s (GM 2026-09-21, now in the
    rules text too). An exploding 10 would break the stated -2.0 .. +2.5 range."""
    return d10(reroll=False)


_HONOR_RE = re.compile(r'^\s*Honor:\s*(-?\d+(?:\.\d+)?)\s*$', re.MULTILINE)
#: THE LINE FORMAT IS PINNED (spec 212 FR-006), because `parse_records` silently
#: drops a line this pattern cannot match - a writer and a pattern that drift would
#: orphan a PC's history without an error. `test_every_written_line_parses` asserts
#: that every shape `Record.line()` can produce is matched here. The trailing
#: marker is OPTIONAL: lines written before feature 212 carry none, and gain one
#: the next time a conversation advances them.
_LINE_RE = re.compile(
    r'^- (?P<pc>.+?) \(rank (?P<rank>\d+)\): told (?P<told>-?\d+\.\d) '
    r'after (?P<n>\d+) conversations?(?P<locked> - locked in)?'
    r'(?: \[(?P<last>[^,\]\s]+), (?:was (?P<was>-?\d+\.\d)|first)\])?$'
)


@dataclass(frozen=True)
class Record:
    pc: str
    rank: int
    told: float
    conversations: int
    locked: bool = False
    #: Feature 212. The conversation this record was last advanced in - the id
    #: `begin_conversation` mints - and what the PC had been told BEFORE it (None
    #: for a first conversation). `last` is what makes an advance idempotent: the
    #: same conversation never advances a record twice. `was` is what makes
    #: `abandon_conversation` able to undo it mechanically. Both are empty for a
    #: manual call made outside a conversation, which behaves as it always has.
    last: str = ''
    was: float | None = None

    def line(self) -> str:
        s = 's' if self.conversations != 1 else ''
        lock = ' - locked in' if self.locked else ''
        marker = ''
        if self.last:
            before = 'first' if self.was is None else f'was {self.was:.1f}'
            marker = f' [{self.last}, {before}]'
        return (
            f'- {self.pc} (rank {self.rank}): told {self.told:.1f} '
            f'after {self.conversations} conversation{s}{lock}{marker}'
        )


def parse_honor(gm_info: str) -> float | None:
    """The NPC's true Honor from the ``Honor: X.Y`` line, or None."""
    m = _HONOR_RE.search(gm_info)
    return float(m.group(1)) if m else None


def _split(gm_info: str) -> tuple[list[str], int, int]:
    """Lines of ``gm_info`` plus the [start, end) of the Discern Honor block
    (heading and its ``- `` lines); ``start == -1`` when there is none."""
    lines = gm_info.replace('\r\n', '\n').split('\n')
    try:
        start = next(i for i, ln in enumerate(lines) if ln.strip() == HEADING)
    except StopIteration:
        return lines, -1, -1
    end = start + 1
    while end < len(lines) and lines[end].startswith('- '):
        end += 1
    return lines, start, end


def parse_records(gm_info: str) -> dict[str, Record]:
    """The block's records keyed by lowercased PC name (insertion order kept)."""
    lines, start, end = _split(gm_info)
    out: dict[str, Record] = {}
    if start < 0:
        return out
    for ln in lines[start + 1 : end]:
        m = _LINE_RE.match(ln)
        if m:
            rec = Record(
                m['pc'],
                int(m['rank']),
                float(m['told']),
                int(m['n']),
                bool(m['locked']),
                last=m['last'] or '',
                was=float(m['was']) if m['was'] else None,
            )
            out[rec.pc.lower()] = rec
    return out


def render(gm_info: str, records: Mapping[str, Record]) -> str:
    """``gm_info`` with the Discern Honor block replaced (or appended)."""
    lines, start, end = _split(gm_info)
    block = [HEADING, *(r.line() for r in records.values())]
    if start < 0:
        while lines and not lines[-1].strip():
            lines.pop()
        lines += ['', *block]
    else:
        lines[start:end] = block
    return '\n'.join(lines)


def perceived(gm_info: str) -> str:
    """``'low'`` when the NPC's GM notes list Unconventional, ``'high'`` for
    Virtue (each a line of its own, the way chargen writes them), else
    ``'normal'``. These are the TARGET's traits, so the NPC's notes."""
    lines = {ln.strip().lower() for ln in gm_info.splitlines()}
    if 'unconventional' in lines:
        return 'low'
    if 'virtue' in lines:
        return 'high'
    return 'normal'


def first_guess(honor: float, die: int, reads: str = 'normal') -> float:
    """``honor + 0.5 * (die - 5)``: -2.0 .. +2.5 on a flat d10. An
    Unconventional target always reads low (``- |adjust|``), a Virtue target
    always high (``+ |adjust|``)."""
    adjust = 0.5 * (die - 5)
    if reads == 'low':
        adjust = -abs(adjust)
    elif reads == 'high':
        adjust = abs(adjust)
    return round(honor + adjust, 1)


def refine(told: float, honor: float, rank: int) -> float:
    """One more conversation: ``0.X`` closer to the truth, never past it."""
    step = min(0.1 * rank, abs(told - honor))
    return round(told + step if told < honor else told - step, 1)


def advance(
    record: Record | None,
    pc: str,
    honor: float,
    rank: int | None,
    die: int,
    reads: str = 'normal',
    marker: str = '',
) -> Record:
    """The record after this conversation. A missing ``rank`` is an error on
    a first conversation and 'keep the stored rank' afterwards.

    ``marker`` is the open conversation's id (feature 212), and THE IDEMPOTENCY
    RULE LIVES IN THE FIRST BRANCH: a record this conversation has already
    advanced comes back unchanged, however many times and by whichever path it is
    asked for - the player's command, the watcher's commit, the GM's manual call.
    The GM: *"if somebody slips up and accidentally runs discern honor twice in the
    same conversation, then it will return the same result rather than incrementing
    them closer"*. With no marker (a manual call outside a conversation) nothing is
    idempotent and nothing is marked: one call is one conversation, as it always
    was - the GM's own call is the boundary there. A same-calendar-day suppression
    was drafted for that case and struck by the spec review: his semantic is a
    conversation, not a time window."""
    if record is not None and marker and record.last == marker:
        return record
    if record is None:
        if rank is None:
            raise ValueError(
                f'{pc} has never used Discern Honor on this character: pass rank=<knack rank>'
            )
        told = first_guess(honor, die, reads)
        return Record(pc, rank, told, 1, locked=told == honor, last=marker)
    r = rank if rank is not None else record.rank
    told = refine(record.told, honor, r)
    return replace(
        record,
        rank=r,
        told=told,
        conversations=record.conversations + 1,
        locked=told == honor,
        last=marker,
        was=record.told if marker else None,
    )


def rollback(records: Mapping[str, Record], marker: str, honor: float) -> dict[str, Record]:
    """``records`` as they stood before conversation ``marker`` touched them.

    `abandon_conversation()` is the wrong-NPC exit, and the GM approved "discard on
    abandon" - so an advance this conversation already committed must not be left
    standing on a character it was never about. A ``first`` record is removed; any
    other gets its ``was`` value back and one conversation fewer. The previous
    conversation's own marker is not restored (it is gone), which costs nothing: a
    closed conversation's id never comes round again."""
    out: dict[str, Record] = {}
    for key, rec in records.items():
        if not marker or rec.last != marker:
            out[key] = rec
        elif rec.was is not None:
            out[key] = replace(
                rec,
                told=rec.was,
                conversations=rec.conversations - 1,
                locked=rec.was == honor,
                last='',
                was=None,
            )
    return out


_READS_NOTE = {'low': ' (Unconventional: reads low)', 'high': ' (Virtue: reads high)', 'normal': ''}


def describe(
    npc: str, honor: float, before: Record | None, after: Record, reads: str = 'normal'
) -> str:
    lines = [f'{npc} - true Honor {honor:.1f}{_READS_NOTE[reads]}']
    if before == after:
        lines.append(
            f'{after.pc} (rank {after.rank}) has already been answered in this conversation: '
            f'tell them {after.told:.1f} again'
        )
    elif before is None:
        lines.append(
            f'{after.pc} (Discern Honor rank {after.rank}), first conversation: '
            f'tell them {after.told:.1f}'
        )
    else:
        lines.append(
            f'{after.pc} (rank {after.rank}) was told {before.told:.1f} after '
            f'{before.conversations} conversation{"s" if before.conversations != 1 else ""}'
        )
        lines.append(f'conversation {after.conversations}: tell them {after.told:.1f}')
    if after.locked:
        lines.append('locked in - this is the true value')
    return '\n'.join(lines)


def _open_conversation() -> Conversation | None:
    """The conversation open right now, if any. Imported at CALL time: `rolls`
    imports this module for the knack's rules, so a top-level import would cycle."""
    from l7r.repl.rolls import conversation

    return conversation.current()


def discern_honor(
    npc: str,
    pc: str | PC,
    rank: int | None = None,
    *,
    upload: bool = True,
    rank_lookup: Callable[[PC], int] = knack_rank,
    characters: Callable[[], Sequence[Mapping[str, object]]] = op.existing_characters,
    get_body: Callable[[str], Mapping[str, object] | None] = op.get_character_body,
    update: Callable[..., object] = op.update_character,
    roll: Callable[[], int] = d10_flat,
    conversation: Callable[[], Conversation | None] = _open_conversation,
) -> Record:
    """Resolve one Discern Honor conversation between ``pc`` and ``npc``,
    record it on OP (``upload=False`` to only preview), print the result.
    ``pc`` is a registered PC in any form (``Jimen``, ``"Tsuruchi Jimen"``,
    ``TSURUCHI_JIMEN``) - their rank is read off the character sheet - or
    any name with an explicit ``rank=``.

    INSIDE A CONVERSATION WITH THIS NPC (feature 212) this is the same answer the
    player's `/discern-honor` gives, not a second one: the value was decided when
    the conversation opened, the record advances once, and calling again - before
    or after the player asks - changes nothing. With no conversation open against
    this NPC (none at all, or one with somebody else) one call is one
    conversation, exactly as before."""
    who = resolve_pc(pc)
    pc_name = who.given if who else str(pc)
    if rank is None and who is not None:
        rank = rank_lookup(who)
        print(f'{pc_name}: Discern Honor rank {rank} (character sheet {who.url})')
    match = match_character(npc, characters())
    if match.kind == 'ambiguous':
        names = ', '.join(str(c['name']) for c in match.matches)
        raise ValueError(f'{npc!r} matches several characters: {names}')
    if match.kind == 'none':
        raise ValueError(f'no character matches {npc!r}; nearest: {", ".join(match.nearest)}')
    char = match.character
    with NOTES_LOCK:
        return _resolve(char, pc_name, rank, upload, get_body, update, roll, conversation)


def _resolve(
    char: Mapping[str, object],
    pc_name: str,
    rank: int | None,
    upload: bool,
    get_body: Callable[[str], Mapping[str, object] | None],
    update: Callable[..., object],
    roll: Callable[[], int],
    conversation: Callable[[], Conversation | None],
) -> Record:
    """The read-decide-write half of `discern_honor`, under `NOTES_LOCK`."""
    body = get_body(str(char['id']))
    if body is None:
        raise RuntimeError(f'could not fetch {char["name"]} from Obsidian Portal')
    gm_info = str(body.get('game_master_info') or '')
    honor = parse_honor(gm_info)
    if honor is None:
        raise ValueError(f'{char["name"]} has no "Honor: X.Y" line in the GM-only notes')
    records = parse_records(gm_info)
    before = records.get(pc_name.lower())
    reads = perceived(gm_info)
    conv = conversation()
    talking = conv is not None and conv.npc_id == str(char['id'])
    marker = conv.conversation_id if conv is not None and talking else ''
    planned = conv.planned(pc_name) if conv is not None and talking else None
    if planned is not None and not (before is not None and before.last == marker):
        # Decided at begin_conversation, and possibly already shown to the player:
        # the GM's screen and the player's reply must never disagree.
        after = planned
    else:
        after = advance(
            before, before.pc if before else pc_name, honor, rank, roll(), reads, marker
        )
    records[after.pc.lower()] = after
    print(describe(str(char['name']), honor, before, after, reads))
    if before == after:
        print('(already recorded)')
    elif upload:
        update(str(char['id']), game_master_info=render(gm_info, records))
        print(f'recorded on {char["character_url"]}')
    else:
        print('(not uploaded)')
    return after
