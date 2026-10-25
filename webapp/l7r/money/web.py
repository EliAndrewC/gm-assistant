"""The Money section's koku-worth playground (`/money/koku`, features 222, 223): state, data, rows.

TWO READINGS, SHOWN TOGETHER (feature 223; the why is in `basket.py`): the WHOLE BASKET ($D/N over
a complete basket with every good; only a price source moves it) and the AVERAGE OVER GOODS (the
single-good kokus by the chosen mean; the goods switched in and out act on this one only). Together
they are the range. (The visitor's own goods, feature 223, were removed at the GM's word on
2026-10-25; an old link's `c1`..`c3` is ignored.)

The whole state lives in the link, so a link reopens the same variant:
`b=<basket the average starts from>`, `wb=<complete basket for the whole-basket reading>`,
`q_<good>=<quantity>` (0 switches a good out of the average; a good outside the basket switched on
comes in at the standard basket's quantity), `x_<good>=<substitute index>`, `m=<mean>`
(geometric, the default, or arithmetic), `eq=1` (weigh the goods equally instead of by spending),
and `w_<era>=<weight>` (an era's weight in Rokugan's prices; default 1). A value that does not parse
is ignored, never an error: a hand-edited link still opens, and a feature-222 link's toggles now act
on the average. Today's prices are always the newest snapshot (GM 2026-10-24), so an old link's `s=`
is ignored. A repeated parameter reads its last value: the form sends a hidden `q_<good>=0` before
each good's checkbox. `money.js` computes the same readings in the browser (`compute`), and
`tests/test_money_js.py` runs it under node against `basket.reading` so the two cannot drift.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from l7r.money import basket as bk
from l7r.money.readings import LABORER_KOKU_YEAR, Wage, wage_dollars_per_koku

__all__ = [
    'AXIS',
    'Row',
    'alone_of',
    'State',
    'axis_pct',
    'drivers',
    'left_out',
    'page_data',
    'parse_state',
    'rows',
    'sen',
    'sig3',
    'source_label',
    'state_reading',
    'whole_reading',
]

AXIS = (
    10.0,
    10_000.0,
)  # the dot track's dollars, log scale: the single-good kokus span ~$36-$4,400


@dataclass(frozen=True, slots=True)
class State:
    basket: str
    snapshot: str
    quantities: Mapping[str, float] = field(default_factory=dict)
    choices: Mapping[str, int] = field(default_factory=dict)
    mean: str = 'geometric'
    equal: bool = False
    weights: Mapping[str, float] = field(default_factory=dict)  # era overrides only
    whole: str = bk.STANDARD


def _number(text: str) -> float | None:
    try:
        value = float(text)
    except ValueError:
        return None
    return value if math.isfinite(value) and value >= 0 else None


def parse_state(model: bk.Model, params: Mapping[str, Any]) -> State:
    params = {k: v[-1] if isinstance(v, list) and v else v for k, v in params.items()}
    basket = params.get('b', bk.STANDARD)
    basket = basket if basket in model.baskets else bk.STANDARD
    whole = params.get('wb', bk.STANDARD)
    whole = whole if whole in model.baskets and model.baskets[whole].complete else bk.STANDARD
    snapshot = model.snapshots[-1].date
    quantities, choices = {}, {}
    for good in model.goods:
        if (q := _number(str(params.get(f'q_{good}', '')))) is not None:
            quantities[good] = q
        if str(params.get(f'x_{good}', '')).isdigit():
            choices[good] = int(params[f'x_{good}'])
    weights = {}
    for era in model.eras:
        if (w := _number(str(params.get(f'w_{era}', '')))) is not None:
            weights[era] = w
    mean = params.get('m', 'geometric')
    return State(
        basket,
        snapshot,
        quantities,
        choices,
        mean if mean in bk.MEANS else 'geometric',
        params.get('eq') == '1',
        weights,
        whole,
    )


def state_reading(model: bk.Model, state: State, koku_kg: float) -> bk.Reading:
    """The average over goods: toggles, the mean and the weighting act here."""
    return bk.reading(
        model,
        model.basket(state.basket),
        model.snapshot(state.snapshot),
        koku_kg,
        choices=state.choices,
        quantities=state.quantities,
        mean=state.mean,
        equal=state.equal,
        weights=state.weights,
    )


def whole_reading(model: bk.Model, state: State, koku_kg: float) -> bk.Reading:
    """The whole basket, every good: $D/N. Only price sources and era weights move it."""
    return bk.reading(
        model,
        model.basket(state.whole),
        model.snapshot(state.snapshot),
        koku_kg,
        choices=state.choices,
        mean='arithmetic',
        weights=state.weights,
    )


def _pct(part: float) -> str:
    return '<1%' if part < 0.005 else f'{round(part * 100)}%'


def _money(x: float) -> str:
    return f'${x:,.0f}'


def drivers(reading: bk.Reading) -> str:
    """The goods that pull the average furthest above and below it (by the reading's own mean)."""
    weighted = reading.weighted
    if not weighted:
        return 'Nothing in the basket is priced on both sides.'
    f = math.log if reading.mean == 'geometric' else float
    center = f(reading.per_koku)
    pulls = [(w * (f(reading.alone(ln)) - center), ln, w) for ln, w in weighted]
    up = max(pulls, key=lambda p: p[0])
    down = min(pulls, key=lambda p: p[0])

    def say(p: tuple[float, bk.Line, float]) -> str:
        return f'{p[1].name} ({_money(reading.alone(p[1]))} alone, {_pct(p[2])} of the weight)'

    if up[0] <= 0 or down[0] >= 0:
        return f'Every good reads the same: {say(up)}.'
    return f'Pulls the average up most: {say(up)}. Pulls it down most: {say(down)}.'


def left_out(reading: bk.Reading) -> tuple[str, ...]:
    """Basket goods with no price on one side."""
    return reading.left_out


def alone_of(reading: bk.Reading, good: str) -> float:
    """One good's single-good koku in a reading, 0 when it is not counted there."""
    return next((reading.alone(ln) for ln in reading.lines if ln.good == good and ln.counted), 0.0)


def axis_pct(dollars: float) -> float:
    """Where a dollar figure sits on the dot track, 0-100, clamped to the axis."""
    lo, hi = AXIS
    x = (math.log10(max(dollars, lo)) - math.log10(lo)) / (math.log10(hi) - math.log10(lo))
    return round(min(max(x, 0.0), 1.0) * 100, 2)


def sen(silver: float, model: bk.Model, koku_kg: float) -> float:
    """Rokugan's grams of silver as sen: a koku (1,000 sen) is `koku_kg` of rice."""
    return silver / (model.rice_ref * koku_kg) * 1000


def sig3(x: float) -> str:
    """Three significant figures, whole numbers with commas from 100: '6.6', '0.0412', '1,230'.
    `money.js` `sig3` is its twin."""
    v = float(f'{x:.3g}')
    return f'{v:,.0f}' if v >= 100 else f'{v:g}'


def source_label(url: str) -> str:
    """A footnote's link text: the diagram research question's number, else the source's name."""
    m = re.search(r'/research/questions/(\d{4})-', url)
    if m:
        return f'research, question {int(m.group(1))}'
    if 'bassino_and_ma' in url:
        return 'Bassino & Ma, Table 3'
    return 'source'


@dataclass(frozen=True, slots=True)
class Row:
    """One good on the page: every good of the catalog is listed, in or out of the average."""

    good: bk.Good
    quantity: float
    default: float
    silver: float | None  # Rokugan's grams of silver a unit, under the state's era weights
    options: tuple[bk.Option, ...]
    choice: int
    weight: float | None  # share of the average; None when not counted
    alone: float | None  # the single-good koku
    eras: tuple[bk.Era, ...]  # what Rokugan's price rests on
    candidates: tuple[bk.Era, ...]  # every era that could: prices it beside rice, not excluded


def rows(model: bk.Model, state: State, reading: bk.Reading) -> list[Row]:
    basket = model.basket(state.basket).quantities
    standard = model.basket().quantities
    snap = model.snapshot(state.snapshot)
    prices = model.prices(state.weights)
    weight = {ln.good: w for ln, w in reading.weighted}
    line = {ln.good: ln for ln in reading.lines}
    out = []
    for gid, good in model.goods.items():
        default = basket.get(gid, 0.0)
        opts = snap.options.get(gid, ())
        choice = min(max(state.choices.get(gid, 0), 0), max(len(opts) - 1, 0))
        counted = gid in weight
        out.append(
            Row(
                good,
                state.quantities.get(gid, default),
                default or standard.get(gid, 1.0),
                prices.get(gid),
                opts,
                choice,
                weight.get(gid),
                reading.alone(line[gid]) if counted else None,
                tuple(model.eras[e] for e in model.rests_on(gid, state.weights)),
                tuple(
                    e
                    for e in sorted(model.eras.values(), key=lambda e: e.years)
                    if gid in e.goods and 'rice' in e.goods and not e.goods[gid].excluded
                ),
            )
        )
    return out


def page_data(model: bk.Model, koku_kg: float, wage: Wage) -> dict[str, Any]:
    """Everything `money.js` needs to recompute the page, as plain JSON. Rokugan's prices are not
    sent: the script derives them from each era's prices in rice and the weights, as `prices`
    does."""
    defaults = model.weights()
    return {
        'koku_kg': koku_kg,
        'rice_ref': model.rice_ref,
        'standard': bk.STANDARD,
        'newest': model.snapshots[-1].date,
        'wage_per_koku': wage_dollars_per_koku(wage),
        'laborer_koku_year': LABORER_KOKU_YEAR,
        'axis': list(AXIS),
        'goods': {gid: {'name': g.name, 'unit': g.unit} for gid, g in model.goods.items()},
        'eras': {
            e.id: {
                'title': e.title,
                'weight': defaults[e.id],
                'reference': e.reference,
                'goods': {
                    gid: {
                        'ratio': p.silver_g / e.goods['rice'].silver_g,
                        'borrowed': bool(p.borrowed),
                        'excluded': bool(p.excluded),
                    }
                    for gid, p in e.goods.items()
                }
                if 'rice' in e.goods
                else {},
            }
            for e in model.eras.values()
        },
        'baskets': {
            b.id: {
                'name': b.name,
                'description': b.description,
                'goods': dict(b.quantities),
                'complete': b.complete,
            }
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
            for s in model.snapshots[-1:]
        },
    }


def page_json(model: bk.Model, koku_kg: float, wage: Wage) -> str:
    """`page_data` for a `<script type="application/json">` block: `</` cannot close it early."""
    return json.dumps(page_data(model, koku_kg, wage), ensure_ascii=False).replace('</', '<\\/')
