"""The GM's own rolls, kept in a rolling buffer for `annotate()` to offer.

When a player's roll is contested, the opposing side is one the GM made at the
prompt - almost always `xky(7, 4) + 8`.

**Rolls are kept whether or not a conversation is open**, because that is the GM's
actual order of operations (2026-08-29): *"I would like to be able to roll the NPCs
side before opening. That is actually the most common workflow is that by the time
I go to annotate something, I have already made the roll."* An earlier version
recorded only while a conversation was open - faithful to the GM's first statement,
wrong about how they work, and the kind of error only using the thing finds.

That reversal cost a property worth naming, since it was deliberate: `xky` used to
return a plain `int` outside a conversation, so no other code path could mutate a
record by doing arithmetic on a roll. It now always returns a `DiceTotal`. The cost
is bounded - a stray bonus lands on a buffer entry only `annotate()` reads, and the
menu shows each candidate's current total before the GM picks one.

**It imports nothing from its own package.** `dice.py` writes to it and
`rolls/annotate.py` reads from it, and those sit on opposite sides of the package's
import order; a registry with any dependency of its own would close that loop.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime

#: How many rolls the buffer holds. The GM's own framing is "recently", so any
#: reasonable bound satisfies the request; naming it here stops a later session
#: inventing a different one and calling it a fix. Twenty is several minutes of a
#: GM rolling steadily, and an older candidate is one they would not recognize in
#: the menu anyway.
BUFFER = 20


@dataclass
class GmRoll:
    """One roll the GM made at the prompt.

    Mutable, unlike a player's `Roll`, because the whole point is that a bonus can
    arrive after the dice are seen - `xky(7, 4) + 8` in one expression, or `_ + 15`
    later once a school's third-dan free raises are spent.
    """

    seq: int
    dice: tuple[int, ...]
    keep: int
    base: int
    #: The pool as the GM ASKED for it, before `actual_xky` applies the ten-die cap.
    #: The skill inference needs this: a skill roll is (Ring + skill)k(Ring), so the
    #: skill is rolled minus kept - but above ten dice the cap converts the excess
    #: into a flat bonus, and inferring from the capped pool gives the wrong answer.
    asked: tuple[int, int] = (0, 0)
    bonus: int = 0
    at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def total(self) -> int:
        return self.base + self.bonus

    @property
    def skill(self) -> int:
        """The skill this roll implies - rolled dice minus kept dice.

        `rules/02-skills.md:68`: a roll with no skill is (2 * Ring)k(Ring), so a
        skill roll is (Ring + skill)k(Ring) and a 7k4 implies skill 3. The GM warned
        this is *"not completely reliable because there are things that can cause
        extra dice to be rolled"*, which is why it is only ever a DEFAULT the GM can
        override.
        """
        rolled, kept = self.asked if self.asked != (0, 0) else (len(self.dice), self.keep)
        return max(0, rolled - kept)

    def describe(self) -> str:
        """One line for the annotate menu."""
        kept = ', '.join(str(d) for d in sorted(self.dice, reverse=True)[: self.keep])
        rolled, keeping = self.asked if self.asked != (0, 0) else (len(self.dice), self.keep)
        bonus = f' {self.bonus:+d}' if self.bonus else ''
        return f'{self.total}  ({rolled}k{keeping}: kept {kept}{bonus}) at {self.at:%H:%M:%S}'


_recorded: deque[GmRoll] = deque(maxlen=BUFFER)
_seq = 0


def start() -> None:
    """A conversation opened.

    Deliberately does NOT clear the buffer: the rolls made just before opening are
    the ones the GM most wants to pair with a player's roll.
    """


def stop() -> None:
    """A conversation closed. Also does not clear, for the same reason in reverse -
    the next conversation may be opened moments later against the same rolls."""


def clear() -> None:
    """Forget everything. For tests, and for a GM who wants a clean slate."""
    global _seq
    _recorded.clear()
    _seq = 0


def record(dice: tuple[int, ...], keep: int, base: int, asked: tuple[int, int] = (0, 0)) -> GmRoll:
    """Remember one roll. Always records - see the module docstring."""
    global _seq
    _seq += 1
    entry = GmRoll(seq=_seq, dice=dice, keep=keep, base=base, asked=asked)
    _recorded.append(entry)
    return entry


def recent() -> tuple[GmRoll, ...]:
    """The buffered rolls, oldest first."""
    return tuple(_recorded)
