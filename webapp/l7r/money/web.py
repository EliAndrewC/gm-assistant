"""The Money section's koku-worth playground (`/money/koku`, feature 221): its state, data and rows.

The whole state lives in the link, so a link reopens the same variant:
`b=<basket>`, `s=<snapshot date>`, `q_<good>=<quantity>` (0 switches a good off; a good outside the
basket switched on comes in at the standard basket's quantity), `x_<good>=<substitute index>`, and
`c1`..`c3` = `<name>|<unit>|<quantity>|<grams of silver a unit>|<dollars a unit>` for a good of the
visitor's own. A value that does not parse is ignored, never an error: a hand-edited link still
opens. `money.js` computes the same reading in the browser (`compute`), and
`tests/test_money_js.py` runs it under node against `basket.reading` so the two cannot drift.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from l7r.money import basket as bk
from l7r.money.readings import LABORER_KOKU_YEAR, Wage, wage_dollars_per_koku

__all__ = [
    'MAX_CUSTOM',
    'Row',
    'State',
    'custom_status',
    'drivers',
    'left_out',
    'page_data',
    'parse_state',
    'rows',
    'state_reading',
]

MAX_CUSTOM = 3


@dataclass(frozen=True, slots=True)
class State:
    basket: str
    snapshot: str
    quantities: Mapping[str, float] = field(default_factory=dict)
    choices: Mapping[str, int] = field(default_factory=dict)
    custom: tuple[bk.Custom | None, ...] = ()


def _number(text: str) -> float | None:
    try:
        value = float(text)
    except ValueError:
        return None
    return value if math.isfinite(value) and value >= 0 else None


def _custom(text: str) -> bk.Custom | None:
    parts = text.split('|')
    if len(parts) != 5 or not parts[0].strip():
        return None
    name, unit, qty, silver, dollars = (p.strip() for p in parts)
    return bk.Custom(name, unit, _number(qty) or 0.0, _number(silver), _number(dollars))


def parse_state(model: bk.Model, params: Mapping[str, Any]) -> State:
    basket = params.get('b', bk.STANDARD)
    basket = basket if basket in model.baskets else bk.STANDARD
    dates = [s.date for s in model.snapshots]
    snapshot = params.get('s', dates[-1])
    snapshot = snapshot if snapshot in dates else dates[-1]
    quantities, choices = {}, {}
    for good in model.goods:
        if (q := _number(str(params.get(f'q_{good}', '')))) is not None:
            quantities[good] = q
        if str(params.get(f'x_{good}', '')).isdigit():
            choices[good] = int(params[f'x_{good}'])
    custom = tuple(_custom(str(params.get(f'c{i}', ''))) for i in range(1, MAX_CUSTOM + 1))
    return State(basket, snapshot, quantities, choices, custom)


def state_reading(model: bk.Model, state: State, koku_kg: float) -> bk.Reading:
    return bk.reading(
        model,
        model.basket(state.basket),
        model.snapshot(state.snapshot),
        koku_kg,
        choices=state.choices,
        quantities=state.quantities,
        custom=[c for c in state.custom if c is not None],
    )


def _pct(part: float, whole: float) -> str:
    return '<1%' if part / whole < 0.005 else f'{round(part / whole * 100)}%'


def drivers(reading: bk.Reading) -> str:
    """The good that takes the largest share of each side: what moves the koku most."""
    counted = [ln for ln in reading.lines if ln.counted]
    if not counted:
        return 'Nothing in the basket is priced on both sides.'

    def top(side: str, total: float) -> str:
        shares = {ln.name: _pct(getattr(ln, side), total) for ln in counted}
        best = max(counted, key=lambda ln: float(getattr(ln, side)))
        tied = [n for n, s in shares.items() if s == shares[best.name]]
        each = ' each' if len(tied) > 1 else ''
        return f'{" and ".join(tied)} ({shares[best.name]}{each})'

    return (
        f"Largest share of today's cost: {top('dollars', reading.dollars)}. "
        f'Largest share of the 1740s cost: {top("silver", reading.silver)}.'
    )


def left_out(reading: bk.Reading) -> tuple[str, ...]:
    """Basket goods with no price on one side; a custom good has its own status line instead."""
    return tuple(
        ln.name
        for ln in reading.lines
        if ln.quantity > 0 and not ln.counted and not ln.good.startswith('custom-')
    )


def custom_status(state: State, reading: bk.Reading) -> list[str]:
    """One line under each custom row: whether it counts, and for how much."""
    lines = iter(ln for ln in reading.lines if ln.good.startswith('custom-'))
    out = []
    for c in state.custom:
        if c is None:
            out.append('')
            continue
        ln = next(lines)
        if not ln.counted:
            out.append('Not counted until all five are filled in.')
        else:
            out.append(
                f"Counts for {_pct(ln.dollars, reading.dollars)} of today's cost and "
                f'{_pct(ln.silver, reading.silver)} of the 1740s cost.'
            )
    return out


@dataclass(frozen=True, slots=True)
class Row:
    """One good on the page: every good of the catalog is listed, in or out of the basket."""

    good: bk.Good
    quantity: float
    default: float
    price: bk.Price | None
    options: tuple[bk.Option, ...]
    choice: int


def rows(model: bk.Model, state: State) -> list[Row]:
    basket = model.basket(state.basket).quantities
    standard = model.basket().quantities
    snap = model.snapshot(state.snapshot)
    out = []
    for gid, good in model.goods.items():
        default = basket.get(gid, 0.0)
        opts = snap.options.get(gid, ())
        choice = min(max(state.choices.get(gid, 0), 0), max(len(opts) - 1, 0))
        out.append(
            Row(
                good,
                state.quantities.get(gid, default),
                default or standard.get(gid, 1.0),
                model.reference.goods.get(gid),
                opts,
                choice,
            )
        )
    return out


def page_data(model: bk.Model, koku_kg: float, wage: Wage) -> dict[str, Any]:
    """Everything `money.js` needs to recompute the page, as plain JSON."""
    ref = model.reference
    return {
        'koku_kg': koku_kg,
        'rice_ref': model.rice_ref,
        'standard': bk.STANDARD,
        'newest': model.snapshots[-1].date,
        'wage_per_koku': wage_dollars_per_koku(wage),
        'laborer_koku_year': LABORER_KOKU_YEAR,
        'goods': {
            gid: {
                'name': g.name,
                'unit': g.unit,
                'silver': ref.goods[gid].silver_g if gid in ref.goods else None,
            }
            for gid, g in model.goods.items()
        },
        'baskets': {
            b.id: {'name': b.name, 'description': b.description, 'goods': dict(b.quantities)}
            for b in model.baskets.values()
        },
        'snapshots': {
            s.date: {
                'priced_by': s.priced_by,
                'goods': {
                    gid: [
                        {'priced_as': o.priced_as, 'dollars': o.dollars_per_unit, 'link': o.link}
                        for o in opts
                    ]
                    for gid, opts in s.options.items()
                },
            }
            for s in model.snapshots
        },
    }


def page_json(model: bk.Model, koku_kg: float, wage: Wage) -> str:
    """`page_data` for a `<script type="application/json">` block: `</` cannot close it early."""
    return json.dumps(page_data(model, koku_kg, wage), ensure_ascii=False).replace('</', '<\\/')
