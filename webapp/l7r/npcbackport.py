"""A character-sheet NPC's built stats, written back to Obsidian Portal (feature 226).

The GM (2026-10-25): *"when we create characters on the character sheet, ... backport any
rings and stats we established back into obsidian portal so that e.g. whatever their Air ring
ends up being in the character sheet app gets backported to their Obsidian Portal page."*

The stats go into the `NPC numbers:` block of the GM-only notes (feature 207,
`l7r.repl.rolls.npcnumbers`), which the REPL reads so an NPC rolls the same tact next month.
Only gm-assistant writes to Obsidian Portal, so the sheet posts its build to `/api/npc-numbers`
(`l7r.app.NamesApi`) and this module does the rest:

- **The sheet wins on every stat it sends**, higher or lower ("whatever their Air ring ends up
  being"); every change is reported `old -> new`. A first draft kept a lower value as "used in
  play" - the fidelity review struck it: the request admits no carve-out by value.
- **A block line the sheet did not send is kept** (a hand-written `heraldry 3`), and so is a line
  `parse` cannot read (`npcnumbers.render`).
- **Nothing is written when nothing changed**, and nothing at all for a name that matches no
  record or several: most generated NPCs are nameless guards with no page.

PURE apart from the three injected Obsidian Portal callables, the way `honor.discern_honor`
takes them. Every failure is an answer, never an exception: the sheet's NPC must not depend on
this.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from chargen.opsynth import match_character
from l7r.repl.rolls import npcnumbers

MAX_RANK = 6

#: A block line's name: letters and spaces (`npcnumbers._ENTRY`). Sheet ids put underscores
#: where the block has spaces (`double_attack`), so those are turned into spaces first.
_NAME = re.compile(r'^[a-z][a-z ]*$')


def normalize(stats: Mapping[str, object]) -> tuple[dict[str, int], list[str]]:
    """``(stats keyed as block names, names that cannot be a block line)``.

    Raises ValueError on a value that is not a whole number from 0 to `MAX_RANK`: that is a
    broken request, refused before Obsidian Portal is touched, while a name the block cannot
    hold is one stat left out and reported.
    """
    kept: dict[str, int] = {}
    refused: list[str] = []
    for key, value in stats.items():
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= MAX_RANK:
            raise ValueError(f'{key} must be a whole number from 0 to {MAX_RANK}')
        name = ' '.join(str(key).replace('_', ' ').lower().split())
        if _NAME.match(name):
            kept[name] = value
        else:
            refused.append(str(key))
    return kept, refused


@dataclass(frozen=True)
class Merge:
    """The block's numbers after a backport, and what happened to each stat sent."""

    numbers: dict[str, int]
    added: list[str]
    changed: dict[str, tuple[int, int]]
    unchanged: list[str]


def merge(existing: Mapping[str, int], sent: Mapping[str, int]) -> Merge:
    """`sent` over `existing`: existing names keep their order, new ones follow in sent order."""
    numbers = dict(existing)
    added: list[str] = []
    changed: dict[str, tuple[int, int]] = {}
    unchanged: list[str] = []
    for name, value in sent.items():
        old = existing.get(name)
        if old is None:
            added.append(name)
        elif old == value:
            unchanged.append(name)
        else:
            changed[name] = (old, value)
        numbers[name] = value
    return Merge(numbers, added, changed, unchanged)


def _label(name: str) -> str:
    return name.capitalize() if name in npcnumbers.RINGS else name


def describe(record_name: str, m: Merge) -> str:
    """One line for the GM, shown on the sheet as is."""
    parts = []
    if m.added:
        parts.append('added ' + ', '.join(f'{_label(n)} {m.numbers[n]}' for n in m.added))
    if m.changed:
        parts.append(', '.join(f'{_label(n)} {a} -> {b}' for n, (a, b) in m.changed.items()))
    if not parts:
        return f'{record_name}: Obsidian Portal already has these numbers'
    if m.unchanged:
        parts.append(f'{len(m.unchanged)} unchanged')
    return f'{record_name}: ' + '; '.join(parts)


def backport(
    name: str,
    stats: Mapping[str, object],
    *,
    characters: Callable[[], Sequence[Mapping[str, object]]],
    get_body: Callable[[str], Mapping[str, object] | None],
    update: Callable[..., object],
) -> dict[str, Any]:
    """Write `stats` into the NPC numbers of the one character `name` resolves to.

    The answer's `status` is `written`, `unchanged`, `no_record`, `ambiguous` or `failed`, and
    `message` says the same in one line. ValueError (from `normalize`) is the only raise.
    """
    sent, refused = normalize(stats)
    answer: dict[str, Any] = {'name': name, 'refused': refused}
    roster = characters()
    if not roster:  # `op.existing_characters` answers [] when Obsidian Portal is unreachable
        message = 'could not list the Obsidian Portal characters; nothing written'
        return {**answer, 'status': 'failed', 'message': message}
    match = match_character(name, roster)
    if match.kind == 'none':
        message = f'no Obsidian Portal record for {name}; nothing written'
        return {**answer, 'status': 'no_record', 'nearest': list(match.nearest), 'message': message}
    if match.kind == 'ambiguous':
        candidates = [str(c.get('name', '')) for c in match.matches]
        listed = ', '.join(candidates)
        message = f'{name} matches several Obsidian Portal records ({listed}); nothing written'
        return {**answer, 'status': 'ambiguous', 'candidates': candidates, 'message': message}
    char = match.character
    record_name = str(char.get('name', ''))
    answer['record'] = {'name': record_name, 'url': str(char.get('character_url', ''))}
    try:
        # Read fresh right before the write: the GM or the REPL may have edited the notes.
        body = get_body(str(char['id']))
        if body is None:
            raise RuntimeError('could not read the record')
        notes = str(body.get('game_master_info') or '')
        m = merge(npcnumbers.parse(notes), sent)
        if m.added or m.changed:
            update(str(char['id']), game_master_info=npcnumbers.render(notes, m.numbers))
    except Exception as exc:  # noqa: BLE001 - reported to the sheet, never fatal to it
        return {**answer, 'status': 'failed', 'message': f'{record_name}: {exc}; nothing written'}
    return {
        **answer,
        'status': 'written' if m.added or m.changed else 'unchanged',
        'added': {n: m.numbers[n] for n in m.added},
        'changed': {n: list(pair) for n, pair in m.changed.items()},
        'unchanged': m.unchanged,
        'message': describe(record_name, m),
    }
