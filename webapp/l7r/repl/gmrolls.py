"""The GM's own rolls, remembered while a conversation is open.

When a player's roll is contested, the opposing side is one the GM made at the
prompt - almost always `xky(7, 4) + 8`. `annotate()` needs to offer those, so they
are recorded here as they happen.

TWO PROPERTIES THIS MODULE EXISTS TO HAVE:

**It imports nothing from its own package.** `dice.py` records into it and
`rolls/annotate.py` reads from it, and those two sit on opposite sides of the
package's import order; a registry with any dependency of its own would close that
loop. Keep it dependency-free.

**It only records while a conversation is open** (`start()` / `stop()`). That is the
GM's own scoping - *"if a roll such as this is made outside of the context of a
conversation, then it does not need to be stored"* - and it buys something further:
outside a conversation `xky` returns a plain `int`, so the capture machinery does
not exist at all during ordinary use and no other code path can mutate a record by
doing arithmetic on a roll.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class GmRoll:
    """One roll the GM made at the prompt while a conversation was open.

    Mutable, unlike a player's `Roll`, because the whole point is that a bonus can
    arrive after the dice are seen - `xky(7, 4) + 8` in one expression, or `_ + 15`
    later once a school's third-dan free raises are spent.
    """

    seq: int
    dice: tuple[int, ...]
    keep: int
    base: int
    bonus: int = 0
    at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def total(self) -> int:
        return self.base + self.bonus

    def describe(self) -> str:
        """One line for the annotate menu."""
        kept = ', '.join(str(d) for d in sorted(self.dice, reverse=True)[: self.keep])
        shown = f'{len(self.dice)}k{self.keep}'
        bonus = f' {self.bonus:+d}' if self.bonus else ''
        return f'{self.total}  ({shown}: kept {kept}{bonus}) at {self.at:%H:%M:%S}'


_recorded: list[GmRoll] = []
_open = False


def start() -> None:
    """Begin recording. Called when a conversation opens."""
    global _open
    _open = True
    _recorded.clear()


def stop() -> None:
    """Stop recording and forget everything. Called when a conversation closes."""
    global _open
    _open = False
    _recorded.clear()


def recording() -> bool:
    return _open


def record(dice: tuple[int, ...], keep: int, base: int) -> GmRoll | None:
    """Remember one roll, or return None when no conversation is open."""
    if not _open:
        return None
    entry = GmRoll(seq=len(_recorded) + 1, dice=dice, keep=keep, base=base)
    _recorded.append(entry)
    return entry


def recent() -> tuple[GmRoll, ...]:
    """Every roll recorded during the open conversation, oldest first."""
    return tuple(_recorded)
