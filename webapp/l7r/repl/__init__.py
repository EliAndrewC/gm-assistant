"""The GM's Python REPL for the L7R campaign (``scripts/repl.py``).

``namespace()`` is everything the prompt starts with; ``help_text()`` is the
banner that lists it. Add a function here and it is at the prompt.
"""

from __future__ import annotations

from typing import Any

from l7r.repl.dice import Dist, actual_xky, d10, dist, initiative, percent, prob, xky
from l7r.repl.honor import discern_honor
from l7r.repl.names import (
    Pick,
    bank,
    cache_status,
    hamlet_name,
    name,
    names,
    place,
    province_name,
    town_name,
    village_name,
)
from l7r.repl.rolls import (
    abandon_conversation,
    begin_conversation,
    conversation_status,
    end_conversation,
)
from l7r.repl.sheets import PC, PCS, knack_rank

__all__ = [
    'PC',
    'PCS',
    'Dist',
    'Pick',
    'abandon_conversation',
    'actual_xky',
    'bank',
    'begin_conversation',
    'cache_status',
    'conversation_status',
    'd10',
    'discern_honor',
    'dist',
    'end_conversation',
    'hamlet_name',
    'initiative',
    'knack_rank',
    'name',
    'names',
    'percent',
    'place',
    'province_name',
    'prob',
    'town_name',
    'village_name',
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
    ('village_name()', 'same; also province_name(), town_name(), hamlet_name()'),
    ('cache_status()', 'did the background roster refresh (OP + character-sheet app) succeed?'),
    (
        'discern_honor("Otsuki", Jimen)',
        'the knack: reads Honor off OP and the rank off the sheet, records it (rank= to override)',
    ),
    ('Jimen / TSURUCHI_JIMEN', 'the PCs with the knack, as constants or "strings"; PCS lists them'),
    (
        'begin_conversation("Otsuki")',
        'watch every channel for rolls and record them against that NPC',
    ),
    ('end_conversation()', "write the round into the NPC's Obsidian Portal bio and stop"),
    ('conversation_status()', 'what is open and the line so far; abandon_conversation() discards'),
)


def namespace() -> dict[str, Any]:
    """The REPL's starting globals."""
    import l7r.repl as pkg

    ns = {n: getattr(pkg, n) for n in __all__}
    for pc in PCS:  # Jimen, TsuruchiJimen, JIMEN, TSURUCHI_JIMEN ...
        ns.update(pc.constants)
    return ns


def help_text() -> str:
    width = max(len(c) for c, _ in COMMANDS)
    lines = ['L7R GM REPL - Python 3 with the campaign tools loaded:']
    lines += [f'  {c:<{width}}  {summary}' for c, summary in COMMANDS]
    lines.append('  help_l7r()  prints this again')
    return '\n'.join(lines)
