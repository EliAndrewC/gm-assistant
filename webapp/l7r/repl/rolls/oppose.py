"""Oppose Social and Oppose Knowledge: a player's roll that taxes the NPC's later ones. PURE.

Feature 208. The rules (`rules/05-school_knacks.md`): *"Once per conversation you may
target a character, roll this knack, and divide the result by 5, rounding down.
Subtract that amount from all skill rolls made by that character for the rest of the
conversation which roll with Air"* - Water, for Oppose Knowledge. The GM used to carry
that number in their head for the rest of the scene. Now (2026-09-19): *"if somebody
makes a 'oppose social' or a 'oppose knowledge' roll during a conversation, then I
would like for that to automatically apply the penalties ... They can just
automatically begin their effect."*

EVERYTHING HERE IS DERIVED FROM THE CONVERSATION'S ROLLS. There is no "current
penalty" stored anywhere: the penalty in effect for a ring at a moment is the highest
live oppose roll of the matching knack made at or before that moment. That one
definition gives the GM's three rules without a second code path:

- *"they do not stack, but rather whichever roll is highest is the one that takes
  effect"* - a maximum, not a sum;
- a roll the NPC made BEFORE the oppose roll is untouched - the oppose roll is not
  "at or before" it;
- a discarded oppose roll simply stops being counted.

THE ONE RETROACTIVE CASE is a line of questioning: *"if an oppose social roll is made
in the middle of a line of questioning ... the sincerity roll of the NPC will be
retroactively affected because that roll is still active. So this is basically the
same as what happens if someone goes from not grilling to grilling."* A line's
Sincerity roll stays active until the NEXT line is declared, so `for_line` asks a
different question from `in_effect`: not "was the oppose roll made before the
Sincerity roll" but "was it made before this line ENDED".

TIME IS MESSAGE TIME, as it is for `conversation.attach`: the watcher polls every 20
seconds, so an oppose roll is usually COLLECTED after the GM has already rolled for
the NPC. `settle` is what squares that - it re-derives the penalty on every tagged
roll the GM has made in this conversation, so a late-arriving oppose roll still lands
on the rolls made after its message time, and on none made before.

WHICH RING EACH KNACK TAXES IS THE GM'S OWN STATEMENT, written out in `TARGET_RINGS`:
*"oppose social affects any roll that is made using the air ring and oppose knowledge
affects any roll that is made using the water ring."* The rules text is only CHECKED
against it (`rules_disagreement`), and a disagreement is reported while the penalty
still applies. The fidelity review of the spec struck the first draft, which read the
mapping from the rules and went inert when it could not: a knack that silently does
nothing is the one failure the GM cannot see at the table. It also named the trap -
each knack's `**Ring:**` header is the ring it is ROLLED with, which is the OPPOSITE
ring (Oppose Social rolls Water and taxes Air), so "read the ring from the rules"
is satisfiable in a way that inverts the GM's instruction.
"""

from __future__ import annotations

import functools
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from l7r.repl.gmrolls import GmRoll
from l7r.repl.rolls import rules
from l7r.repl.rolls.models import Conversation, Line, Roll
from l7r.repl.rolls.skills import KNACKS_PATH, MULTIWORD_KNACKS, skill_rings

#: The rules divide the roll by this, rounding down.
DIVISOR = 5

#: knack -> the ring whose rolls it taxes. The GM's words; see the module docstring.
TARGET_RINGS = {'oppose social': 'air', 'oppose knowledge': 'water'}

_SECTION = re.compile(r'^## (?P<name>[^\n]+)\n(?P<body>.*?)(?=^## |\Z)', re.M | re.S)
_TARGET = re.compile(r'which\s+roll\s+with\s+(?P<ring>[A-Za-z]+)', re.I)


def rules_disagreement(path: Path = KNACKS_PATH) -> str:
    """'' when the rules text agrees with `TARGET_RINGS`; otherwise what to tell the GM.

    A CHECK, never the source: whatever this returns, the penalty applies as the GM
    stated it. An unreadable rules file is reported too, because the check not
    running is not the same as the check passing.
    """
    if not path.exists():
        return f'could not check the oppose knacks against the rules: {path} is missing'
    said: dict[str, str] = {}
    for section in _SECTION.finditer(path.read_text(encoding='utf-8')):
        target = _TARGET.search(section.group('body'))
        if target is not None:
            said[section.group('name').strip().lower()] = target.group('ring').lower()
    wrong = [
        f'{knack} taxes {ring.capitalize()} here but the rules say '
        f'{said[knack].capitalize() if knack in said else "nothing the tool can read"}'
        for knack, ring in TARGET_RINGS.items()
        if said.get(knack) != ring
    ]
    return '; '.join(wrong)


@functools.cache
def ring_of(skill: str) -> str:
    """The ring a SKILL rolls with, '' when the rules do not say."""
    try:
        return skill_rings().get(skill.lower(), '')
    except OSError:
        return ''


@dataclass(frozen=True)
class Penalty:
    """One oppose roll, read as what it costs the NPC."""

    roll: Roll

    @property
    def ring(self) -> str:
        return TARGET_RINGS[self.knack]

    @property
    def amount(self) -> int:
        return self.roll.total // DIVISOR

    @property
    def knack(self) -> str:
        return self.roll.skill.lower()

    def describe(self) -> str:
        """`-6 oppose social (Jimen 32)` - what every subtraction shows the GM."""
        who = rules.personal_name(self.roll.character)
        return f'-{self.amount} {self.knack} ({who} {self.roll.total})'


def is_oppose(roll: Roll) -> bool:
    return roll.skill.lower() in TARGET_RINGS


def live(rolls: Iterable[Roll]) -> list[Penalty]:
    """Every oppose roll that counts: attributed and not discarded."""
    return [Penalty(r) for r in rolls if is_oppose(r) and r.attributed and not r.discarded]


def _highest(found: Sequence[Penalty]) -> Penalty | None:
    """The highest wins; between equals the EARLIER one, which was already in effect."""
    worth = [p for p in found if p.amount > 0]
    if not worth:
        return None
    return max(worth, key=lambda p: (p.amount, -p.roll.at.timestamp()))


def in_effect(rolls: Iterable[Roll], ring: str, when: datetime) -> Penalty | None:
    """The penalty a roll made with `ring` at `when` takes, or None."""
    return _highest([p for p in live(rolls) if p.ring == ring and p.roll.at <= when])


def for_skill(conv: Conversation, skill: str, when: datetime) -> Penalty | None:
    """`in_effect`, from the NPC's SKILL rather than its ring."""
    return in_effect(conv.rolls, ring_of(skill), when)


def for_line(conv: Conversation, line: Line) -> Penalty | None:
    """The penalty on `line`'s hidden Sincerity roll - the one RETROACTIVE case.

    The Sincerity roll opposes every interrogation roll on the line until the next
    line is declared, so an oppose roll made any time before the line ENDED counts -
    including one made after the Sincerity roll itself. A line that had already ended
    is left alone: those contests are over.
    """
    later = [other.at for other in conv.lines if other.at > line.at]
    ended = min(later) if later else None
    ring = ring_of(rules.OPPOSING_SKILL[rules.INTERROGATION])
    found = [p for p in live(conv.rolls) if p.ring == ring and (ended is None or p.roll.at < ended)]
    return _highest(found)


def effect(conv: Conversation, roll: Roll) -> str:
    """What to tell the GM, in the TERMINAL, as an oppose roll arrives.

    Never written anywhere: the fidelity review struck a draft that put this text in
    the public bio as a tool-authored note, because the GM said the rolls *"do not
    even need to be annotated"* and every written line shape in this package is one
    the GM dictated. Worked out against the OTHER live oppose rolls, so it reads the
    same whether or not `roll` has been added to the conversation yet.
    """
    mine = Penalty(roll)
    ring = mine.ring.capitalize()
    others = [r for r in conv.rolls if r != roll]
    standing = in_effect(others, mine.ring, roll.at)
    if standing is not None and standing.amount >= mine.amount:
        who = rules.personal_name(standing.roll.character)
        return f"{mine.describe()} changes nothing - {who}'s -{standing.amount} stands"
    if mine.amount == 0:
        return f'{mine.describe()} is too low to cost {conv.npc_name} anything'
    text = f'{conv.npc_name} takes {mine.describe()} on every {ring} roll from here on'
    if standing is not None:
        text += f", replacing {rules.personal_name(standing.roll.character)}'s -{standing.amount}"
    return text


@dataclass(frozen=True)
class Change:
    """A GM roll whose penalty `settle` moved."""

    entry: GmRoll
    before: int

    def describe(self, npc: str) -> str:
        was = self.entry.unpenalized - self.before
        source = f' {self.entry.penalty_source}' if self.entry.penalty_source else ''
        return (
            f'{npc} {self.entry.tagged} {was} -> {self.entry.total}'
            f' (-{self.entry.penalty}{source}, rolled {self.entry.at:%H:%M:%S})'
        )


def penalize(conv: Conversation, entry: GmRoll, skill: str) -> Penalty | None:
    """SET `entry`'s penalty to what is in effect for `skill` at the moment it was rolled.

    Set, never added: calling this twice, or again after a higher oppose roll turns
    up, leaves the roll paying exactly one penalty. A roll marked a mistake pays none.
    """
    found = None if entry.mistake else for_skill(conv, skill, entry.at)
    entry.penalty = 0 if found is None else found.amount
    entry.penalty_source = '' if found is None else found.knack
    return found


def settle(conv: Conversation, entries: Iterable[GmRoll]) -> list[Change]:
    """Re-derive the penalty on every TAGGED roll the GM made in this conversation.

    Called when an oppose roll is collected, because collection lags the message by
    up to a poll: a `tact()` rolled ten seconds after the player posted was rolled
    under the penalty, and only finds out here. Untagged rolls have no known ring
    and are left for `annotate()` to price when it pairs them.
    """
    changed: list[Change] = []
    for entry in entries:
        if not entry.tagged or entry.at < conv.opened_at:
            continue
        before = entry.penalty
        penalize(conv, entry, entry.tagged)
        if entry.penalty != before:
            changed.append(Change(entry, before))
    return changed


assert set(TARGET_RINGS) == set(MULTIWORD_KNACKS), 'the vocabulary and the ring table differ'
