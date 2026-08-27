"""The Discern Honor school knack, tracked on Obsidian Portal.

``discern_honor("Otsuki", "Jimen", rank=2)`` looks the NPC up on OP, reads
their true Honor from the ``Honor: X.Y`` line of the GM-only notes, applies
the knack, records the result back into those notes, and prints what to tell
the player.

THE RULE (``rules/05-school_knacks.md``, "Discern Honor"): the first
conversation tells the player ``honor + 0.5 * (d10 - 5)`` - a flat d10, so
the guess lands 2.0 below to 2.5 above the truth in half-point steps (the
rules file says ``(1k1 - 0.5)``, which would put every first guess ABOVE the
truth; the GM's stated range of -2.0 .. +2.5 is what ``- 5`` gives, and is
what is implemented - flagged to the GM 2026-08-27). Each conversation after
the first moves the told value ``0.X`` closer to the truth, X = the PC's rank
in the knack, until it locks in at the true value.

WHY IT IS TRACKED: a second conversation only refines the FIRST answer, so
the GM must know who asked, what they were told, and how many times. The
record is a block in the NPC's ``game_master_info``::

    Discern Honor:
    - Jimen (rank 2): told 4.5 after 1 conversation
    - Kaede (rank 1): told 3.0 after 4 conversations - locked in

One line per PC; the rank is stored so it need only be given once (passing
``rank=`` again updates it - a PC who bought a rank). Nothing older than
this block is read: the GM ruled (2026-08-27) that no backward compatibility
with prose notes is wanted.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace

from chargen import op
from chargen.opsynth import match_character
from l7r.repl.dice import d10

HEADING = 'Discern Honor:'
_HONOR_RE = re.compile(r'^\s*Honor:\s*(-?\d+(?:\.\d+)?)\s*$', re.MULTILINE)
_LINE_RE = re.compile(
    r'^- (?P<pc>.+?) \(rank (?P<rank>\d+)\): told (?P<told>-?\d+\.\d) '
    r'after (?P<n>\d+) conversations?(?P<locked> - locked in)?$'
)


@dataclass(frozen=True)
class Record:
    pc: str
    rank: int
    told: float
    conversations: int
    locked: bool = False

    def line(self) -> str:
        s = 's' if self.conversations != 1 else ''
        lock = ' - locked in' if self.locked else ''
        return (
            f'- {self.pc} (rank {self.rank}): told {self.told:.1f} '
            f'after {self.conversations} conversation{s}{lock}'
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
            rec = Record(m['pc'], int(m['rank']), float(m['told']), int(m['n']), bool(m['locked']))
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


def first_guess(honor: float, die: int) -> float:
    """``honor + 0.5 * (die - 5)``: -2.0 .. +2.5 on a flat d10."""
    return round(honor + 0.5 * (die - 5), 1)


def refine(told: float, honor: float, rank: int) -> float:
    """One more conversation: ``0.X`` closer to the truth, never past it."""
    step = min(0.1 * rank, abs(told - honor))
    return round(told + step if told < honor else told - step, 1)


def advance(record: Record | None, pc: str, honor: float, rank: int | None, die: int) -> Record:
    """The record after this conversation. A missing ``rank`` is an error on
    a first conversation and 'keep the stored rank' afterwards."""
    if record is None:
        if rank is None:
            raise ValueError(
                f'{pc} has never used Discern Honor on this character: pass rank=<knack rank>'
            )
        told = first_guess(honor, die)
        return Record(pc, rank, told, 1, locked=told == honor)
    r = rank if rank is not None else record.rank
    told = refine(record.told, honor, r)
    return replace(
        record, rank=r, told=told, conversations=record.conversations + 1, locked=told == honor
    )


def describe(npc: str, honor: float, before: Record | None, after: Record) -> str:
    lines = [f'{npc} - true Honor {honor:.1f}']
    if before is None:
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


def discern_honor(
    npc: str,
    pc: str,
    rank: int | None = None,
    *,
    upload: bool = True,
    characters: Callable[[], Sequence[Mapping[str, object]]] = op.existing_characters,
    get_body: Callable[[str], Mapping[str, object] | None] = op.get_character_body,
    update: Callable[..., object] = op.update_character,
    roll: Callable[[], int] = lambda: d10(reroll=False),
) -> Record:
    """Resolve one Discern Honor conversation between ``pc`` and ``npc``,
    record it on OP (``upload=False`` to only preview), print the result."""
    match = match_character(npc, characters())
    if match.kind == 'ambiguous':
        names = ', '.join(str(c['name']) for c in match.matches)
        raise ValueError(f'{npc!r} matches several characters: {names}')
    if match.kind == 'none':
        raise ValueError(f'no character matches {npc!r}; nearest: {", ".join(match.nearest)}')
    char = match.character
    body = get_body(str(char['id']))
    if body is None:
        raise RuntimeError(f'could not fetch {char["name"]} from Obsidian Portal')
    gm_info = str(body.get('game_master_info') or '')
    honor = parse_honor(gm_info)
    if honor is None:
        raise ValueError(f'{char["name"]} has no "Honor: X.Y" line in the GM-only notes')
    records = parse_records(gm_info)
    before = records.get(pc.lower())
    after = advance(before, before.pc if before else pc, honor, rank, roll())
    records[after.pc.lower()] = after
    print(describe(str(char['name']), honor, before, after))
    if upload:
        update(str(char['id']), game_master_info=render(gm_info, records))
        print(f'recorded on {char["character_url"]}')
    else:
        print('(not uploaded)')
    return after
