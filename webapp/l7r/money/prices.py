"""The Money section's price sheets (`/money/prices`, feature 225): the ledger's prices by kind.

Every synthesis row (one with an `id`) that is a Rokugani price is shown on exactly one sheet: the
first sheet in `SHEETS` sharing one of its tags. Comparative rows (another society's prices) and
source rows (what one source says, not yet a synthesis) are never shown as Rokugani prices, and the
shrine builder's line items stay on the shrine builder. A shrine-builder line is tagged BOTH
`construction` and `shrine`: the tag `shrine` alone also marks the Fox shrine-grade charcoal, an
ordinary fuel price that belongs on the fuel sheet (spec-fidelity, feature 225). `unplaced` names an
eligible row that no sheet takes; a test fails on one, so a new tag cannot make a price silently
disappear.

The order of `SHEETS` settles a row with tags from two sheets: wages and takings before the goods
they mention (a troupe's takings are an income, not entertainment), entertainment before clothing (a
stage costume belongs with the troupe), land before rent (a plot's rent is about land), and
offerings before paper (shrine paper is an offering).
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from html import escape

from l7r.money import coins
from l7r.money.ledger import Row, Swing, swing_for
from l7r.money.readings import laborer_days

__all__ = [
    'SHEETS',
    'Item',
    'Sheet',
    'SheetView',
    'eligible',
    'price',
    'sheet_for',
    'sheets',
    'plain',
    'research_title',
    'source_link',
    'unplaced',
]


@dataclass(frozen=True, slots=True)
class Sheet:
    id: str
    title: str
    blurb: str
    tags: tuple[str, ...]
    wage: bool = False  # read in wage dollars (how much it matters), not goods dollars


SHEETS = (
    Sheet(
        'wages',
        'Wages and incomes',
        'What work pays, by the day or the year, and what a maker or a troupe takes in. Its '
        'dollars are wage dollars, how much a sum matters to the earner: about twenty times a '
        "goods dollar, so a laborer's day reads $122 here and an inn's night $4 on the next "
        'sheet.',
        ('wage', 'income', 'troupe'),
        wage=True,
    ),
    Sheet(
        'entertainment',
        'Entertainment',
        "Seats at a play, street performers, and an entertainer's costumes and instruments.",
        ('entertainment',),
    ),
    Sheet(
        'travel',
        'Lodging, travel and horses',
        'Inns and cheap lodging on the road, a horse fed and stabled, a cart hired.',
        ('travel', 'transport', 'horse', 'animal'),
    ),
    Sheet(
        'land', 'Land and farms', "A family farm's price, rent and tax.", ('land', 'farm', 'tax')
    ),
    Sheet(
        'housing',
        'Housing and rent',
        'A room, a house or an estate in a domain capital, by the month; a warehouse by the week.',
        ('rent', 'housing'),
    ),
    Sheet(
        'food',
        'Food and drink',
        'A meal, salt, fruit from a cart, sake at the shop and in the tavern.',
        ('food', 'drink', 'meal'),
    ),
    Sheet(
        'clothing',
        'Cloth and clothing',
        'Cotton and silk by the length, a kimono made up, bedding and bags.',
        ('clothing', 'cloth'),
    ),
    Sheet('offerings', 'Offerings', 'Small things given at a shrine.', ('religious', 'offering')),
    Sheet(
        'paper',
        'Paper and books',
        'Paper, a notice put up, a book bought, borrowed or copied by hand.',
        ('paper', 'book', 'writing'),
    ),
    Sheet(
        'tools',
        'Tools and weapons',
        "A smith's work: knives, a sickle, arrows.",
        ('tool', 'tools', 'weapon', 'knife'),
    ),
    Sheet('fuel', 'Fuel', 'Charcoal, from a small bag to an ox-cart load.', ('fuel', 'charcoal')),
)

REPO = 'https://github.com/EliAndrewC/gm-assistant'
# Rows that lead their sheet whatever their price: the laborer's day and year are the yardstick the
# Days column counts in (design review, feature 225).
FIRST = ('wage-unskilled-day', 'wage-unskilled-year')
# The research record's verdict words, as plain English for a reader of the sheets.
PLAIN = (
    ('NOT ATTESTED', 'not recorded'),
    ('ATTESTED ONLY FOR', 'recorded only for'),
    ('ATTESTED', 'recorded'),
    ('SILENT', 'unrecorded'),
    ('diagram names', 'the research names'),
)

SOLIDITY = {
    'historical': 'researched',
    'guess': 'guess',
    'deviation': 'departs from history',
}


def eligible(row: Row) -> bool:
    """A Rokugani price the sheets show: a synthesis row, neither comparative nor a shrine-builder
    line."""
    return (
        bool(row.id)
        and row.label != 'comparative'
        and not {'construction', 'shrine'} <= set(row.tags)
    )


def sheet_for(row: Row) -> Sheet | None:
    return next((s for s in SHEETS if set(s.tags) & set(row.tags)), None)


def unplaced(rows: Iterable[Row]) -> list[str]:
    """Eligible rows no sheet takes (the gate's test expects none)."""
    return [r.id for r in rows if eligible(r) and sheet_for(r) is None]


@dataclass(frozen=True, slots=True)
class Item:
    row: Row
    price: str  # '3-5 zeni', 'about 1 koku 5 bu'
    days: str  # laborer-days, '0.5' or '2-6'
    dollars: str  # '$12-$40' in the sheet's reading
    solidity: str  # 'researched', 'guess', 'departs from history'
    unverified: bool  # a historical row resting on a lead, not research or the canon


@dataclass(frozen=True, slots=True)
class SheetView:
    sheet: Sheet
    items: tuple[Item, ...]
    swings: tuple[tuple[str, Swing], ...]  # each with the name it goes by on this sheet


def _span(a: str, b: str) -> str:
    return a if a == b else f'{a} to {b}'


def _days(sen: int) -> str:
    d = laborer_days(sen)
    return f'{d:,.0f}' if d >= 10 else f'{d:.1f}' if d >= 0.1 else '<0.1'


def _dollars(sen: int, per_koku: float) -> str:
    x = coins.koku(sen) * per_koku
    return f'${x:,.0f}' if x >= 10 else f'${x:,.2f}'


def price(low: int, high: int) -> str:
    """'3 zeni to 5 zeni'; a range from nothing reads 'up to 1 sen' (a donation)."""
    if low == 0 < high:
        return f'up to {coins.everyday(high)}'
    return _span(coins.everyday(low), coins.everyday(high))


def plain(text: str) -> str:
    """The record's verdict words (SILENT, ATTESTED ONLY FOR) in plain English."""
    for word, said in PLAIN:
        text = text.replace(word, said)
    return text


def research_title(url: str) -> str:
    """A diagram research page's title from its file name: '0262-what-did-sake-cost.html' -> 'What
    did sake cost?'."""
    slug = url.rsplit('/', 1)[-1].removesuffix('.html')
    words = slug.split('-')[1:]
    return (' '.join(words).capitalize() + '?') if words else 'research'


def source_link(source: str) -> str:
    """An item's source as HTML: a link for research, the canon's section, or the estimate it was
    derived from (on GitHub); a lead names its file."""
    if source.startswith('https://'):
        label = 'source'
        if re.search(r'/questions/\d{4}-', source):
            label = f'research: {research_title(source)}'
        return f'<a class="koku-link" href="{escape(source)}">{escape(label)}</a>'
    kind, _, rest = source.partition(':')
    if kind == 'derived':
        path, _, anchor = rest.partition('#')
        url = f'{REPO}/blob/main/{path}'
        text = (
            f'a logged estimate, {anchor}'
            if anchor.startswith('E0')
            else 'derived in the money skill'
        )
        return f'<a class="koku-link" href="{escape(url)}">{escape(text)}</a>'
    if kind == 'canon':
        return 'the setting notes'
    return "the GM's earlier notes, not yet checked against research"


def sheets(
    rows: Sequence[Row], swings: Sequence[Swing], goods_per_koku: float, wage_per_koku: float
) -> list[SheetView]:
    """Every sheet with its items, cheapest first, and the swing notes its goods carry."""
    out = []
    for sheet in SHEETS:
        mine = sorted(
            (r for r in rows if eligible(r) and sheet_for(r) == sheet),
            key=lambda r: (
                r.id not in FIRST,
                FIRST.index(r.id) if r.id in FIRST else 0,
                r.low,
                r.high,
            ),
        )
        per = wage_per_koku if sheet.wage else goods_per_koku
        items = tuple(
            Item(
                r,
                price(r.low, r.high),
                _span(_days(r.low), _days(r.high)) if r.low else f'up to {_days(r.high)}',
                _span(_dollars(r.low, per), _dollars(r.high, per))
                if r.low
                else f'up to {_dollars(r.high, per)}',
                SOLIDITY[r.label],
                r.label == 'historical' and r.source.startswith('lead:'),
            )
            for r in mine
        )
        found = dict.fromkeys(s for r in mine if (s := swing_for(r, list(swings))))
        tags = [t for r in mine for t in r.tags]
        # A class goes by the first of its tags this sheet's goods carry: the rent class reads
        # "lodging" on the lodging sheet (design review).
        notes = tuple((next(t for t in tags if t in s.tags), s) for s in found)
        if items:
            out.append(SheetView(sheet, items, notes))
    return out
