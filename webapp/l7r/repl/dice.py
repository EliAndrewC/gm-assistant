"""L7R dice for the GM's REPL: exploding d10s, roll-and-keep, exact odds.

Replaces the GM's ``current/dice.py`` (a copy-paste-into-the-REPL file). The
functions keep their old names and signatures - ``d10()``, ``xky(6, 3)``,
``initiative``, ``percent`` - but the probabilities are now EXACT rather than
a 1,000-trial Monte Carlo dump that lived at ``/tmp/probabilities.py``.

The exact method: an exploding d10 has survival function
``P(X >= 10m + r) = (1/10)^m * (11 - r) / 10`` for ``1 <= r <= 10``, and
the sum of the top ``k`` of ``n`` dice is ``k + sum over thresholds t >= 2 of
min(k, N_t)`` where ``N_t`` counts the dice showing at least ``t``.
``N_{t+1} | N_t`` is binomial, so a dynamic program over ``t`` gives the
whole distribution of the kept total with no sampling. Values are capped at
``_CAP``, past which the mass left is under 1e-12.
"""

from __future__ import annotations

import random as _random
from functools import cache
from math import comb

_CAP = 130  # a die above this carries < 1e-12 of the mass


def d10(reroll: bool = True) -> int:
    """One d10; a 10 is rolled again and added while ``reroll`` is on."""
    total = die = _random.randint(1, 10)
    while reroll and die == 10:
        die = _random.randint(1, 10)
        total += die
    return total


def actual_xky(roll: int, keep: int) -> tuple[int, int, int]:
    """L5R's overflow rule: dice past 10 rolled become kept dice, kept dice
    past 10 become a flat bonus. Returns ``(roll, keep, bonus)``."""
    bonus = 0
    if roll > 10:
        keep += roll - 10
        roll = 10
    if keep > 10:
        bonus = keep - 10
        keep = 10
    keep = min(keep, roll)
    return roll, keep, bonus


def xky(roll: int, keep: int, reroll: bool = True, print_dice: bool = True) -> int:
    """Roll ``roll`` d10s and keep the best ``keep``. Prints the sorted dice
    (the GM's REPL habit) and returns the kept total."""
    roll, keep, bonus = actual_xky(roll, keep)
    dice = sorted(d10(reroll) for _ in range(roll))
    if print_dice:
        print(dice)
    return bonus + sum(dice[-keep:])


def initiative(roll: int, keep: int) -> list[int]:
    """The ``keep`` lowest of ``roll`` non-exploding d10s, ascending."""
    return sorted(d10(reroll=False) for _ in range(roll))[:keep]


def percent() -> int:
    """d100."""
    return _random.randint(1, 100)


def survival(t: int, reroll: bool = True) -> float:
    """``P(one die >= t)``."""
    if t <= 1:
        return 1.0
    if not reroll:
        return 0.0 if t > 10 else (11 - t) / 10
    m, r = divmod(t - 1, 10)
    r += 1
    return (0.1**m) * (11 - r) / 10


class Dist:
    """The exact distribution of an XkY total.

    ``dist.mean``, ``dist.at_least(tn)`` (the L5R success test, ``>=``),
    ``dist.exactly(v)``, ``dist.table()`` for a printable CDF. Comparing or
    formatting a ``Dist`` uses its mean, so ``prob(6, 3) > 20`` reads naturally.
    """

    def __init__(self, roll: int, keep: int, reroll: bool, pmf: dict[int, float]) -> None:
        self.roll, self.keep, self.reroll = roll, keep, reroll
        self.pmf = dict(sorted(pmf.items()))
        self.mean = sum(v * p for v, p in self.pmf.items())

    def exactly(self, value: int) -> float:
        return self.pmf.get(value, 0.0)

    def at_least(self, tn: int) -> float:
        return sum(p for v, p in self.pmf.items() if v >= tn)

    def percentile(self, q: float) -> int:
        """Smallest total reached with probability at least ``1 - q``..."""
        acc = 0.0
        for v, p in self.pmf.items():
            acc += p
            if acc >= q:
                return v
        return max(self.pmf)  # pragma: no cover - the pmf sums to 1

    def table(self, step: int = 5, upto: int | None = None) -> str:
        """``TN  P(>= TN)`` rows every ``step`` points, to ``upto`` (default:
        the 99th percentile)."""
        top = upto if upto is not None else self.percentile(0.99)
        lines = [
            f'{self.roll}k{self.keep}{"" if self.reroll else " (no reroll)"}  mean {self.mean:.2f}'
        ]
        tn = step
        while tn <= top:
            lines.append(f'  TN {tn:>3}  {self.at_least(tn):6.1%}')
            tn += step
        return '\n'.join(lines)

    def __float__(self) -> float:
        return self.mean

    def __repr__(self) -> str:
        return f'{self.mean:.2f}'

    def __format__(self, spec: str) -> str:
        return format(self.mean, spec)

    @staticmethod
    def _num(other: object) -> float | None:
        if isinstance(other, Dist):
            return other.mean
        return other if isinstance(other, int | float) else None

    def __lt__(self, other: object) -> bool:
        o = self._num(other)
        return NotImplemented if o is None else self.mean < o

    def __le__(self, other: object) -> bool:
        o = self._num(other)
        return NotImplemented if o is None else self.mean <= o

    def __gt__(self, other: object) -> bool:
        o = self._num(other)
        return NotImplemented if o is None else self.mean > o

    def __ge__(self, other: object) -> bool:
        o = self._num(other)
        return NotImplemented if o is None else self.mean >= o


@cache
def dist(roll: int, keep: int, reroll: bool = True) -> Dist:
    """Exact distribution of ``roll`` k ``keep`` (overflow rule applied)."""
    n, k, bonus = actual_xky(roll, keep)
    # state: {(dice still >= t, kept-sum so far): probability}
    states: dict[tuple[int, int], float] = {(n, k): 1.0}
    for t in range(2, _CAP + 1):
        s_prev = survival(t - 1, reroll)
        if s_prev == 0.0:  # a flat d10 has nothing above 10
            break
        p = survival(t, reroll) / s_prev
        nxt: dict[tuple[int, int], float] = {}
        for (alive, total), prob_ in states.items():
            if alive == 0:
                nxt[(0, total)] = nxt.get((0, total), 0.0) + prob_
                continue
            for j in range(alive + 1):
                q = comb(alive, j) * p**j * (1 - p) ** (alive - j)
                if q < 1e-15:
                    continue
                key = (j, total + min(k, j))
                nxt[key] = nxt.get(key, 0.0) + prob_ * q
        states = nxt
    pmf: dict[int, float] = {}
    for (_, total), prob_ in states.items():
        pmf[total + bonus] = pmf.get(total + bonus, 0.0) + prob_
    return Dist(roll, keep, reroll, pmf)


class _Prob:
    """``prob(6, 3)`` -> mean; ``prob(6, 3, 20)`` -> P(total >= 20);
    ``prob(6, 3, table=True)`` prints the CDF. The old dict-style indexing
    ``prob[True][6, 3]`` and ``prob[True][6, 3, 20]`` still works (note the
    old Monte Carlo table counted ``> tn``; this one counts ``>= tn``, which
    is the actual L5R rule)."""

    def __call__(
        self, roll: int, keep: int, tn: int | None = None, reroll: bool = True, table: bool = False
    ) -> Dist | float:
        d = dist(roll, keep, reroll)
        if table:
            print(d.table())
        if tn is None:
            return d
        return d.at_least(tn)

    def __getitem__(self, reroll: bool) -> _Indexed:
        return _Indexed(reroll)


class _Indexed:
    def __init__(self, reroll: bool) -> None:
        self.reroll = reroll

    def __getitem__(self, key: tuple[int, ...]) -> Dist | float:
        roll, keep, *rest = key
        tn = rest[0] if rest else None
        return prob(roll, keep, tn, reroll=self.reroll)


prob = _Prob()
