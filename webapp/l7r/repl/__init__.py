"""The GM's Python REPL for the L7R campaign (``scripts/repl.py``).

``namespace()`` is everything the prompt starts with; ``help_text()`` is the
banner that lists it. Add a function here and it is at the prompt.
"""

from __future__ import annotations

from typing import Any

from l7r.repl.dice import Dist, actual_xky, d10, dist, initiative, percent, prob, xky
from l7r.repl.names import Pick, bank, name, names, place

__all__ = [
    'Dist',
    'Pick',
    'actual_xky',
    'bank',
    'd10',
    'dist',
    'initiative',
    'name',
    'names',
    'percent',
    'place',
    'prob',
    'xky',
]

#: (name, one-line summary) in banner order.
COMMANDS: tuple[tuple[str, str], ...] = (
    ('d10()', 'one exploding d10; d10(reroll=False) for a flat one'),
    ('xky(6, 3)', 'roll 6 keep 3: prints the dice, returns the total'),
    ('initiative(5, 2)', 'the 2 lowest of 5 flat d10s'),
    ('percent()', 'd100'),
    ('prob(6, 3)', 'exact mean of 6k3;  prob(6, 3, 20) = P(>= 20);  prob(6, 3, table=True)'),
    (
        'prob[6, 3]',
        'dict-style: same as prob(6, 3);  prob[6, 3, 20];  prob[False][6, 3] = flat dice',
    ),
    ('name()', 'a given name off the pool: name("f"), name("m", peasant=True)'),
    ('names("f", 3)', 'several, mutually distinct;  bank(3) = 3 male + 3 female'),
    ('place("village")', 'a place name: province / town / village / hamlet'),
)


def namespace() -> dict[str, Any]:
    """The REPL's starting globals."""
    import l7r.repl as pkg

    return {n: getattr(pkg, n) for n in __all__}


def help_text() -> str:
    width = max(len(c) for c, _ in COMMANDS)
    lines = ['L7R GM REPL - Python 3 with the campaign tools loaded:']
    lines += [f'  {c:<{width}}  {summary}' for c, summary in COMMANDS]
    lines.append('  help_l7r()  prints this again')
    return '\n'.join(lines)
