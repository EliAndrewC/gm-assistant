"""Rokugani coin arithmetic: 1 koku (gold) = 10 bu (silver) = 100 zeni (copper) = 1,000 sen.

The canon is `setting/l7r.md` "Money". Every amount is held as a whole number of sen, so sums
and conversions are exact; an amount typed with a fraction ("1.33 zeni") rounds to the nearest
sen once, at parse time.
"""

from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

__all__ = ['COINS', 'SEN_PER', 'everyday', 'fmt', 'koku', 'parse']

COINS = ('koku', 'bu', 'zeni', 'sen')
SEN_PER = {'koku': 1000, 'bu': 100, 'zeni': 10, 'sen': 1}

_PART = re.compile(r'\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*(koku|bu|zeni|sen)\b', re.IGNORECASE)


def parse(text: str) -> int:
    """'3 koku 2 bu', '1.5 koku', '13 sen' -> sen. Raises ValueError on anything else."""
    pos, total, seen = 0, Decimal(0), False
    bad = (
        f'not an amount of koku/bu/zeni/sen: {text!r} '
        '(every number needs its coin, e.g. "13 sen"; nothing found is "0 sen")'
    )
    text = text.strip()
    while pos < len(text):
        m = _PART.match(text, pos)
        if not m:
            raise ValueError(bad)
        try:
            number = Decimal(m.group(1).replace(',', ''))
        except InvalidOperation as exc:  # pragma: no cover - the regex admits only numbers
            raise ValueError(text) from exc
        total += number * SEN_PER[m.group(2).lower()]
        pos, seen = m.end(), True
        while pos < len(text) and text[pos] in ' ,+':
            pos += 1
    if not seen:
        raise ValueError(bad)
    return int(total.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def fmt(sen: int) -> str:
    """Exact: 3215 -> '3 koku 2 bu 1 zeni 5 sen'; 0 -> '0 sen'."""
    if sen < 0:
        return '-' + fmt(-sen)
    parts = []
    for coin in COINS:
        count, sen = divmod(sen, SEN_PER[coin])
        if count:
            parts.append(f'{count:,} {coin}')
    return ' '.join(parts) or '0 sen'


def koku(sen: int) -> float:
    return sen / SEN_PER['koku']


def everyday(sen: int) -> str:
    """The amount in the two largest coins it needs, rounded: how a buyer would say it.

    'about' marks a rounded figure. A commoner's purchase stays in copper (sen and zeni); silver
    bu are for sums of a bu or more; gold koku only for sums of a koku or more.
    """
    if sen < SEN_PER['bu']:
        return fmt(sen)
    big = next(c for c in COINS if sen >= SEN_PER[c])
    small = COINS[COINS.index(big) + 1]
    rounded = round(sen / SEN_PER[small]) * SEN_PER[small]
    text = fmt(rounded)
    return text if rounded == sen else f'about {text}'
