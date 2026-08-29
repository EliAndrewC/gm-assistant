"""The GM's Python REPL for the L7R campaign (``scripts/repl.py``).

``namespace()`` is everything the prompt starts with; ``help_text()`` is the
banner that lists it. Add a function here and it is at the prompt.
"""

from __future__ import annotations

import re
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
    annotate,
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
    'annotate',
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

#: (name, one-line summary) for everything worth documenting, in banner order.
#:
#: `BANNER` below picks the subset printed at STARTUP. This whole list is what
#: `help_l7r()` prints, alongside anything in the namespace that has no row here -
#: the GM wants the short version when the prompt opens and the long version on
#: demand: *"if I ever need to look something up or confirm for myself that
#: something exists or is supposed to, then I have an easy way to do that."*
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
    ('names(f, 3)', 'several, mutually distinct;  bank(3) = 3 male + 3 female'),
    ('m / f', 'bare "m" and "f", so names(f, 3) needs no quotes'),
    ('place("village")', 'a place name: province / town / village / hamlet'),
    ('village_name()', 'a village name; also province_name(), town_name(), hamlet_name()'),
    (
        'cache_status()',
        'did the background roster refresh (OP + character-sheet app) succeed?',
    ),
    (
        'discern_honor("Otsuki", Jimen)',
        'the knack: reads Honor off OP and the rank off the sheet, records it (rank= to override)',
    ),
    ('Jimen / TSURUCHI_JIMEN', 'the PCs with the knack, as constants or "strings"; PCS lists them'),
    (
        'begin_conversation("Otsuki")',
        'watch every channel for rolls and record them against that NPC',
    ),
    ('annotate()', 'say what each roll was for; only Etiquette is saved without it'),
    ('end_conversation()', "write the round into the NPC's Obsidian Portal bio and stop"),
    ('conversation_status()', 'what is open and the line so far; abandon_conversation() discards'),
)

#: What the STARTUP banner shows - the rows the GM still wants reminding of. The
#: rest stay in `COMMANDS`, in the namespace, and in `help_l7r()`; they simply do
#: not cost a line every time the prompt opens (GM 2026-08-29: *"many of the things
#: have been around for so long that I don't need a reminder of them"*). Hiding a
#: row here NEVER removes anything - `tests/test_repl_shell.py` pins that.
BANNER: frozenset[str] = frozenset(
    {
        'name()',
        'names(f, 3)',
        'village_name()',
        'cache_status()',
        'discern_honor("Otsuki", Jimen)',
        'begin_conversation("Otsuki")',
        'annotate()',
        'end_conversation()',
        'conversation_status()',
    }
)


#: Bare `m` and `f` at the prompt, so the GM can write `names(f, 3)` rather than
#: `names("f", 3)` (their request, 2026-08-29). Added here rather than to `__all__`
#: because they are constants, not part of the package's API - the same treatment
#: the PC constants get. Shadowing them with a loop variable is ordinary Python and
#: costs nothing but the shortcut.
GENDERS: dict[str, str] = {'m': 'm', 'f': 'f'}


def namespace() -> dict[str, Any]:
    """The REPL's starting globals."""
    import l7r.repl as pkg

    ns: dict[str, Any] = {n: getattr(pkg, n) for n in __all__}
    for pc in PCS:  # Jimen, TsuruchiJimen, JIMEN, TSURUCHI_JIMEN ...
        ns.update(pc.constants)
    ns.update(GENDERS)
    return ns


def undocumented() -> tuple[str, ...]:
    """Namespace names that no `COMMANDS` row mentions.

    DERIVED rather than listed, so nothing at the prompt can be invisible: a new
    export shows up here the moment it exists, without anyone remembering to add a
    row. A name counts as documented if it appears anywhere in a row - `bank` and
    `province_name` are covered by other rows' descriptions, for instance.
    """
    text = ' '.join(f'{command} {summary}' for command, summary in COMMANDS)
    # Whole IDENTIFIERS, not substrings. Measured: a substring test counted `dist`
    # as documented because "mutually distinct" contains it, and would have hidden
    # `record` behind "records it" - a loose match loses exactly the names most
    # likely to be looked up.
    mentioned = set(re.findall(r'[A-Za-z_][A-Za-z0-9_]*', text))
    return tuple(
        sorted(
            entry for entry in namespace() if not entry.startswith('_') and entry not in mentioned
        )
    )


def help_text(full: bool = False) -> str:
    """The banner. `full=True` lists everything, which is what `help_l7r()` does.

    Startup passes the short form; the GM asked for the long one on demand so they
    can confirm something exists without reading the source.
    """
    rows = COMMANDS if full else tuple(row for row in COMMANDS if row[0] in BANNER)
    width = max(len(c) for c, _ in rows)
    lines = ['L7R GM REPL - Python 3 with the campaign tools loaded:']
    lines += [f'  {c:<{width}}  {summary}' for c, summary in rows]
    if full:
        rest = undocumented()
        if rest:
            lines.append('')
            lines.append('  also in the namespace:')
            lines += [f'    {chunk}' for chunk in _wrap(rest)]
    lines.append('  help_l7r()  prints this again;  help_l7r(False) for the short version')
    return '\n'.join(lines)


def _wrap(names: tuple[str, ...], width: int = 88) -> list[str]:
    """Pack names onto as few lines as will stay readable."""
    lines: list[str] = []
    current = ''
    for entry in names:
        candidate = f'{current}, {entry}' if current else entry
        if len(candidate) > width:
            lines.append(current)
            current = entry
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines
