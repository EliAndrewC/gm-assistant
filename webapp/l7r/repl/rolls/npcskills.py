"""`tact`, `sincerity` and the rest at the prompt: tag a roll, or roll for the NPC.

Feature 207. The GM's habit-to-be: *"instead of saying `xky(8, 3) + 10` I will try
to start saying `xky(8, 3) + 10 - sincerity`"*. The tag does three jobs:

- it says what the roll WAS, so `annotate()` can pair a player's manipulation with
  the GM's tact roll by itself;
- it reads the NPC's ring and rank off the dice and REMEMBERS them
  (`npcnumbers.py`), so the same NPC has the same tact next month;
- it checks the roll against what is remembered and STOPS when they disagree.

The same names are callable, and roll for the NPC from the record:

    tact()          roll from the record, asking for whatever is missing
    tact(2)         state the rank; the ring comes from the record or is asked for
    tact(5, 3)      exactly `xky(5, 3) - tact`
    tact(vp)        spend a void point: one more rolled AND kept; `vp * 2` for two

THE ONE DIFFERENCE between `sincerity(8, 3)` and `xky(8, 3) - sincerity` is the
automatic free raises (acting on sincerity and intimidation, history on culture, law
and strategy): ONLY the called form adds them. The GM (2026-09-19): *"The automatic
raises should only be applied when we roll with the skill function and not when I
roll with the xky function"* - because the `+ 10` they type onto an `xky` roll IS
the acting bonus, and the tag adding it again would count it twice.

`acting(2)` and `history(3)` RECORD and never roll: *"me saying `acting(2)` or
`history(3)` do not actually generate rolls the way that they do for every other
skill. Instead, that serves only to record that the NPC has that rank."*

NOTHING IS RECORDED OR CHECKED WITHOUT AN OPEN CONVERSATION. A tag made outside one
only marks the roll. The GM scoped the check to *"if we are in a conversation with
an NPC"*, and the fidelity review struck a draft that recorded such rolls later: the
numbers could land on the wrong NPC's permanent record.

ONE NPC AT A TIME, by the GM's ruling for now. A later feature will track several,
which is why a tag holds no NPC and the numbers live on the conversation.
"""

from __future__ import annotations

import functools
import importlib
from collections.abc import Callable

from l7r.repl import dice, gmrolls
from l7r.repl.rolls import npcnumbers
from l7r.repl.rolls.models import Conversation
from l7r.repl.rolls.skills import advanced_skills, load_skills, rules_skills, skill_rings

Ask = Callable[[str], str]

RANKS = (0, 5)
RING_VALUES = (2, 6)


def _ask(question: str) -> str:
    """Every prompt here goes through the annotate menu's quiet input, so answers
    stay out of the readline history (2026-09-09). Resolved at call time so a test
    can replace `ask_quietly`."""
    # `annotate` the FUNCTION shadows the module on the package, so import by path.
    module = importlib.import_module('l7r.repl.rolls.annotate')
    asker: Ask = module.ask_quietly
    return asker(question)


def _open() -> Conversation | None:
    from l7r.repl.rolls import conversation

    return conversation._open


@functools.cache
def extra_dice_table() -> dict[str, frozenset[str]]:
    """school -> skills with an extra die. Read once; the rules do not change mid-session."""
    return npcnumbers.school_extra_dice(load_skills())


def extra_dice(skill: str, schools: tuple[str, ...]) -> tuple[int, str]:
    """How many of this pool's dice are the NPC's school's, and which school."""
    table = extra_dice_table()
    for school in schools:
        if skill in table.get(school, frozenset()):
            return 1, school
    return 0, ''


class VoidPoints:
    """`vp`: says a called roll spends a void point. `vp * 2` spends two."""

    def __init__(self, count: int = 1) -> None:
        if count < 1:
            raise ValueError('a void point marker spends at least one')
        self.count = count

    def __mul__(self, times: int) -> VoidPoints:
        return VoidPoints(self.count * int(times))

    __rmul__ = __mul__

    def __repr__(self) -> str:
        return 'vp' if self.count == 1 else f'vp * {self.count}'


vp = VoidPoints()


def _ask_number(question: str, low: int, high: int, ask: Ask) -> int:
    while True:
        answer = ask(question).strip()
        if answer.isdigit() and low <= int(answer) <= high:
            return int(answer)
        print(f'  ? a whole number from {low} to {high}')


def resolve(
    conv: Conversation, entry: gmrolls.GmRoll, reading: npcnumbers.Reading, ask: Ask
) -> None:
    """Record what a tagged roll says, or stop and ask when it disagrees.

    The two answers are the GM's: *"given the option to either correct the skill
    that is there or cancel ... I would like to be able to cancel either by hitting
    Ctrl+c and having that actually caught and recorded as indicating that I made a
    mistake and that I will redo the skill correctly."* So Ctrl-C here is an ANSWER,
    not an interruption, and is caught. The void point answer joined on 2026-09-19
    for a roll that is off by exactly 1k1 or 2k2.
    """
    found = npcnumbers.compare(conv.numbers, reading)
    if found is None:
        added = npcnumbers.fill(conv.numbers, reading)
        if added:
            print(f'  recorded for {conv.npc_name}: {", ".join(added)}')
        return
    print(f'  ! {conv.npc_name}: {found.describe}.')
    choices = ['[m] the roll was a mistake (or Ctrl-C)', '[r] the record was wrong']
    if found.void_answer:
        choices.append(f'[v] {found.void_answer}')
    print('    ' + '   '.join(choices))
    allowed = 'mrv' if found.void_answer else 'mr'
    answer = ''
    while answer not in tuple(allowed):
        try:
            answer = ask('    > ').strip().lower()[:1]
        except KeyboardInterrupt, EOFError:
            print()
            answer = 'm'
    if answer == 'm':
        entry.mistake = True
        print('  marked as a mistake - the record is unchanged. Roll it again.')
    elif answer == 'r':
        npcnumbers.accept(conv.numbers, reading)
        ring = reading.ring_name.capitalize()
        print(f'  record corrected: {ring} {reading.ring}, {reading.skill} {reading.rank}')
    elif found.void_points > 0:
        entry.void_points = found.void_points
        npcnumbers.fill(conv.numbers, reading_without(reading, found.void_points))
        print('  noted - the record is unchanged.')
    else:
        npcnumbers.accept(conv.numbers, reading)
        print(f'  record corrected: {reading.ring_name.capitalize()} {reading.ring}')


def reading_without(reading: npcnumbers.Reading, void_points: int) -> npcnumbers.Reading:
    """The same reading with `void_points` dice taken back out of the ring."""
    return npcnumbers.Reading(
        reading.skill, reading.ring_name, reading.ring - void_points, reading.rank
    )


class SkillTag:
    """One skill's name at the prompt."""

    def __init__(self, name: str, ring_name: str, *, advanced: bool = False) -> None:
        self.name = name
        self.ring_name = ring_name
        self.advanced = advanced

    def __repr__(self) -> str:
        return f'<{self.name}: `roll - {self.name}` tags a roll, `{self.name}()` rolls it>'

    # --- the tag form -------------------------------------------------------

    def tag_roll(self, total: dice.DiceTotal, *, ask: Ask | None = None) -> dice.DiceTotal:
        """`xky(5, 3) - tact`. Called by `DiceTotal.__sub__`; returns the same total."""
        entry = total.entry
        if entry.tagged:
            raise ValueError(
                f'that roll is already tagged {entry.tagged} - a second tag would overwrite '
                'what it was. Roll again if it was the wrong one.'
            )
        entry.tagged = self.name
        conv = _open()
        if conv is None:
            print(f'  tagged {self.name} - no conversation is open, so nothing is recorded.')
            return total
        self._check(conv, entry, ask or _ask)
        return total

    def __rsub__(self, other: object) -> object:
        """A plain number minus a tag: there is no roll behind it to tag."""
        raise TypeError(
            f'only a roll can be tagged: `xky(5, 3) - {self.name}`, or `{self.name}(5, 3)`'
        )

    def _check(self, conv: Conversation, entry: gmrolls.GmRoll, ask: Ask) -> None:
        extra, school = extra_dice(self.name, conv.schools)
        if extra:
            print(f"  ({school} school: one of those dice is the school's)")
        reading = npcnumbers.infer(
            entry.asked,
            self.name,
            self.ring_name,
            extra_dice=extra,
            void_points=entry.void_points,
        )
        resolve(conv, entry, reading, ask)

    # --- the called form ----------------------------------------------------

    def __call__(self, *args: int | VoidPoints, ask: Ask | None = None) -> dice.DiceTotal | None:
        asker = ask or _ask
        conv = _open()
        if conv is None:
            raise RuntimeError(
                f'no conversation open - there is no NPC to roll {self.name} for. '
                'begin_conversation("Name") first.'
            )
        spent = sum(a.count for a in args if isinstance(a, VoidPoints))
        numbers = [int(a) for a in args if not isinstance(a, VoidPoints)]
        if len(numbers) > 2:
            raise TypeError(f'{self.name}(), {self.name}(rank) or {self.name}(rolled, kept)')
        if self.name in npcnumbers.RECORD_ONLY:
            self._record_only(conv, numbers, spent, asker)
            return None
        if len(numbers) == 2:
            return self._pool(conv, numbers[0], numbers[1], spent, asker)
        rank = self._rank(conv, numbers[0] if numbers else None, asker)
        if rank is None:
            return None
        ring = conv.numbers.get(self.ring_name)
        if ring is None:
            ring = _ask_number(
                f"  {conv.npc_name}'s {self.ring_name.capitalize()}? "
                f'[{RING_VALUES[0]}-{RING_VALUES[1]}] > ',
                *RING_VALUES,
                asker,
            )
            conv.numbers[self.ring_name] = ring
            print(f'  recorded for {conv.npc_name}: {self.ring_name.capitalize()} {ring}')
        extra, _ = extra_dice(self.name, conv.schools)
        return self._roll(conv, ring + rank + extra + spent, ring + spent, rank, spent)

    def _rank(self, conv: Conversation, stated: int | None, ask: Ask) -> int | None:
        """The rank to roll: stated, recorded, or asked for. None cancels the roll."""
        recorded = conv.numbers.get(self.name)
        if stated is None:
            if recorded is not None:
                return recorded
            stated = _ask_number(
                f"  {conv.npc_name}'s {self.name} rank? [{RANKS[0]}-{RANKS[1]}] > ", *RANKS, ask
            )
        if not RANKS[0] <= stated <= RANKS[1]:
            raise ValueError(f'a rank runs from {RANKS[0]} to {RANKS[1]}, not {stated}')
        if recorded is None:
            conv.numbers[self.name] = stated
            print(f'  recorded for {conv.npc_name}: {self.name} {stated}')
            return stated
        if recorded == stated:
            return stated
        print(f'  ! {conv.npc_name}: {self.name} {recorded} recorded, you said {stated}.')
        print('    [m] I made a mistake (or Ctrl-C)   [r] the record was wrong')
        answer = ''
        while answer not in ('m', 'r'):
            try:
                answer = ask('    > ').strip().lower()[:1]
            except KeyboardInterrupt, EOFError:
                print()
                answer = 'm'
        if answer == 'm':
            print('  nothing rolled and nothing changed.')
            return None
        conv.numbers[self.name] = stated
        print(f'  record corrected: {self.name} {stated}')
        return stated

    def _record_only(self, conv: Conversation, numbers: list[int], spent: int, ask: Ask) -> None:
        """`acting(2)` / `history(3)`: say what the NPC has. Never a roll."""
        if len(numbers) == 2 or spent:
            raise TypeError(
                f'{self.name} is recorded, never rolled: `{self.name}(2)` says the NPC has '
                f'{self.name} 2. To tag a real roll of it, `xky(6, 3) - {self.name}`.'
            )
        if not numbers and self.name in conv.numbers:
            print(f'  {conv.npc_name}: {self.name} {conv.numbers[self.name]}')
            return
        self._rank(conv, numbers[0] if numbers else None, ask)

    def _pool(
        self, conv: Conversation, rolled: int, kept: int, spent: int, ask: Ask
    ) -> dice.DiceTotal:
        """`tact(5, 3)` - the stated pool, checked exactly as a tagged `xky` is.

        With `vp`, the stated pool is the BASE and the void point dice go on top, so
        `tact(5, 3, vp)` rolls 6k4 and still reads as tact 2, Air 3.
        """
        extra, _ = extra_dice(self.name, conv.schools)
        rank = max(0, rolled - kept - extra)
        total = self._roll(conv, rolled + spent, kept + spent, rank, spent)
        self._check(conv, total.entry, ask)
        return total

    def _roll(
        self, conv: Conversation, rolled: int, kept: int, rank: int, spent: int
    ) -> dice.DiceTotal:
        """Roll the pool and add what the called form adds by itself.

        A rank of 0 does not reroll tens, and an ADVANCED skill at 0 takes -10
        (`rules/02-skills.md`: *"If you roll any skill which you have at 0, you
        don't reroll 10s. If the skill is advanced, subtract 10 from your total."*).
        """
        print(f'  {conv.npc_name} {self.name}: {rolled}k{kept}')
        total = dice.xky(rolled, kept, reroll=rank > 0)
        total.entry.tagged = self.name
        total.entry.void_points = spent
        if rank == 0 and self.advanced:
            total = total + -10
            print('  -10: an advanced skill at rank 0')
        for source, source_rank, bonus in npcnumbers.automatic_raises(self.name, conv.numbers):
            total = total + bonus
            print(f'  +{bonus} {source} {source_rank}')
        return total


def build_tags() -> dict[str, SkillTag]:
    """One tag per skill in the rules' skill list, keyed by the name at the prompt.

    Read from the rules, so a skill added there is at the prompt without an edit
    here. A missing rules mount means no tags rather than a REPL that will not
    start: the dice and the name picks do not need the rules.
    """
    try:
        rings = skill_rings()
        advanced = advanced_skills()
        names = rules_skills()
    except OSError:
        return {}
    return {
        name: SkillTag(name, rings[name], advanced=name in advanced)
        for name in names
        if name in rings
    }
