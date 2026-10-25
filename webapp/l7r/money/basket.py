"""Baskets of goods, their dated dollar prices, and the eras that price them in silver (222).

Three kinds of data, kept apart so each can change alone:

- a BASKET is what is bought: goods and quantities per adult per year (`data/baskets/<id>.json`);
- a SNAPSHOT is what each good cost in US dollars in a month, first option the default and the rest
  substitutes (`data/snapshots/YYYY-MM.json`, never edited once committed);
- an ERA is what the goods, the coins and an unskilled day cost in grams of pure silver at one place
  and time (`data/eras/<id>.json`; a new era is a new file).

THE REFERENCE ERA IS ROKUGAN. The 2017 sheet anchored the zeni on Kyoto 1745-54's rice price (1.49 g
of silver a kg at Bassino & Ma's 3.11 g a monme; 0.826 g at the Genbun monme's 1.725 g of pure
silver, which the reference era uses since diagram#13), so Rokugan's price of every good is Kyoto
1745-54's. Rescaling every reference gram alike moves no reading: each is a ratio of grams. A koku's
goods-dollar value is then the basket's dollars over its reference silver, times the silver in a
koku of rice; an era's money converts by the ratio of that era's basket cost to the reference's,
over the goods priced in both.

A GOOD COUNTS ONLY WHERE IT IS PRICED ON EVERY SIDE IN USE. The 2017 snapshot never priced salt,
fuel or housing, and Tokyo 1882-86 has no price for them either; such goods are left out of that
reading and named, never priced at zero (which would silently shrink one side of the ratio).

WHY HOUSING IS A GOOD, NOT ALLEN'S 5% RENT MARKUP: a uniform markup on both sides of a ratio
cancels, so it would change nothing; the GM approved housing in the standard basket (spec 222,
FR-008).
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

__all__ = [
    'DATA',
    'STANDARD',
    'Basket',
    'Conversion',
    'Custom',
    'Era',
    'Good',
    'Line',
    'Model',
    'Option',
    'Reading',
    'Snapshot',
    'convert',
    'load',
    'problems',
    'reading',
    'reprice',
]

DATA = Path(__file__).parent / 'data'
STANDARD = 'standard'
LABELS = ('historical', 'guess')


@dataclass(frozen=True, slots=True)
class Good:
    id: str
    name: str
    unit: str
    why: str


@dataclass(frozen=True, slots=True)
class Basket:
    id: str
    name: str
    description: str
    quantities: Mapping[str, float]


@dataclass(frozen=True, slots=True)
class Option:
    priced_as: str
    dollars_per_unit: float | None
    link: str
    series: str = ''  # a BLS average-price series (via FRED) that `reprice` fills it from
    factor: float = 1.0  # this good's units per the series' pound


@dataclass(frozen=True, slots=True)
class Snapshot:
    date: str
    priced_by: str
    source: str
    options: Mapping[str, tuple[Option, ...]]

    def price(self, good: str, choice: int = 0) -> float | None:
        """Dollars per unit of the chosen option, or None where the good is unpriced."""
        opts = self.options.get(good, ())
        if not opts:
            return None
        return opts[min(max(choice, 0), len(opts) - 1)].dollars_per_unit


@dataclass(frozen=True, slots=True)
class Price:
    silver_g: float
    label: str
    source: str
    note: str


@dataclass(frozen=True, slots=True)
class Coin:
    silver_g: float
    source: str
    note: str


@dataclass(frozen=True, slots=True)
class Era:
    id: str
    place: str
    years: str
    reference: bool
    confidence: str
    coins: Mapping[str, Coin]
    goods: Mapping[str, Price]
    wage_g_per_day: float
    wage_source: str

    @property
    def title(self) -> str:
        return f'{self.place} {self.years}'


@dataclass(frozen=True, slots=True)
class Model:
    goods: Mapping[str, Good]
    baskets: Mapping[str, Basket]
    snapshots: tuple[Snapshot, ...]
    eras: Mapping[str, Era]

    @property
    def reference(self) -> Era:
        return next(e for e in self.eras.values() if e.reference)

    @property
    def rice_ref(self) -> float:
        """Grams of silver a kg of rice in the reference era: the anchor of Rokugan's coins."""
        return self.reference.goods['rice'].silver_g

    def snapshot(self, date: str | None = None) -> Snapshot:
        if date is None:
            return self.snapshots[-1]
        for snap in self.snapshots:
            if snap.date == date:
                return snap
        have = ', '.join(s.date for s in self.snapshots)
        raise SystemExit(f'no snapshot dated {date}; have {have}')

    def basket(self, name: str | None = None) -> Basket:
        name = name or STANDARD
        if name not in self.baskets:
            raise SystemExit(f'no basket {name!r}; have {", ".join(self.baskets)}')
        return self.baskets[name]

    def era(self, name: str) -> Era:
        if name not in self.eras:
            raise SystemExit(f'no era {name!r}; have {", ".join(self.eras)}')
        return self.eras[name]


def _read(path: Path) -> dict[str, Any]:
    raw: dict[str, Any] = json.loads(path.read_text())
    return raw


def load(data: Path = DATA) -> Model:
    """Every good, basket, snapshot (oldest first; the last is the default) and era."""
    goods = {
        k: Good(k, v['name'], v['unit'], v['why'])
        for k, v in _read(data / 'goods.json').items()
        if not k.startswith('_')
    }
    baskets = {}
    for path in sorted((data / 'baskets').glob('*.json')):
        raw = _read(path)
        baskets[path.stem] = Basket(path.stem, raw['name'], raw['description'], raw['goods'])
    snapshots = []
    for path in sorted((data / 'snapshots').glob('*.json')):
        raw = _read(path)
        options = {
            k: tuple(
                Option(
                    o['priced_as'],
                    o['dollars_per_unit'],
                    o['link'],
                    o.get('series', ''),
                    o.get('factor', 1.0),
                )
                for o in v
            )
            for k, v in raw['goods'].items()
        }
        snapshots.append(Snapshot(raw['date'], raw['priced_by'], raw['source'], options))
    if not snapshots:
        raise FileNotFoundError(f'no snapshots in {data / "snapshots"}')
    eras = {}
    for path in sorted((data / 'eras').glob('*.json')):
        raw = _read(path)
        eras[path.stem] = Era(
            path.stem,
            raw['place'],
            raw['years'],
            raw.get('reference', False),
            raw['confidence'],
            {
                k: Coin(v['silver_g'], v['source'], v.get('note', ''))
                for k, v in raw['coins'].items()
            },
            {
                k: Price(v['silver_g'], v['label'], v['source'], v.get('note', ''))
                for k, v in raw['goods'].items()
            },
            raw['wage']['silver_g_per_day'],
            raw['wage']['source'],
        )
    return Model(goods, baskets, tuple(snapshots), eras)


def problems(model: Model) -> list[str]:
    """Everything `check` refuses: unknown goods, unpriced or unlinked options, bad labels."""
    out = []
    if STANDARD not in model.baskets:
        out.append(f'no {STANDARD!r} basket')
    refs = [e.id for e in model.eras.values() if e.reference]
    if len(refs) != 1:
        out.append(f'exactly one era must be the reference; have {refs or "none"}')
    elif 'rice' not in model.reference.goods:
        out.append(f'the reference era {refs[0]} has no rice price')
    for basket in model.baskets.values():
        for good, qty in basket.quantities.items():
            if good not in model.goods:
                out.append(f'basket {basket.id}: unknown good {good!r}')
            if qty < 0:
                out.append(f'basket {basket.id}: negative quantity of {good}')
    for snap in model.snapshots:
        for good, opts in snap.options.items():
            if good not in model.goods:
                out.append(f'snapshot {snap.date}: unknown good {good!r}')
            for opt in opts:
                if opt.dollars_per_unit is None or opt.dollars_per_unit <= 0:
                    out.append(f'snapshot {snap.date}: {good} ({opt.priced_as or "?"}) unpriced')
                if not opt.link:
                    out.append(f'snapshot {snap.date}: {good} ({opt.priced_as or "?"}) has no link')
    for era in model.eras.values():
        for good, price in era.goods.items():
            if good not in model.goods:
                out.append(f'era {era.id}: unknown good {good!r}')
            if price.label not in LABELS:
                out.append(f'era {era.id}: {good} label {price.label!r} not in {LABELS}')
            if not price.source:
                out.append(f'era {era.id}: {good} has no source')
        if not era.coins:
            out.append(f'era {era.id}: no coins')
    return out


@dataclass(frozen=True, slots=True)
class Custom:
    """A good the playground's visitor adds: both prices are theirs."""

    name: str
    unit: str
    quantity: float
    silver_g: float | None
    dollars: float | None


@dataclass(frozen=True, slots=True)
class Line:
    good: str
    name: str
    unit: str
    quantity: float
    dollars_per_unit: float | None
    silver_per_unit: float | None
    priced_as: str

    @property
    def counted(self) -> bool:
        return self.quantity > 0 and bool(self.dollars_per_unit) and bool(self.silver_per_unit)

    @property
    def dollars(self) -> float:
        return self.quantity * (self.dollars_per_unit or 0) if self.counted else 0.0

    @property
    def silver(self) -> float:
        return self.quantity * (self.silver_per_unit or 0) if self.counted else 0.0


@dataclass(frozen=True, slots=True)
class Reading:
    lines: tuple[Line, ...]
    koku_kg: float
    rice_ref: float

    @property
    def dollars(self) -> float:
        return sum(line.dollars for line in self.lines)

    @property
    def silver(self) -> float:
        return sum(line.silver for line in self.lines)

    @property
    def per_koku(self) -> float:
        """Goods dollars a koku: the basket's dollars per reference gram, times a koku's grams."""
        if not self.silver:
            return 0.0
        return self.dollars / self.silver * self.koku_kg * self.rice_ref

    @property
    def left_out(self) -> tuple[str, ...]:
        """Goods in the basket that this reading could not price on both sides."""
        return tuple(ln.name for ln in self.lines if ln.quantity > 0 and not ln.counted)


def reading(
    model: Model,
    basket: Basket,
    snapshot: Snapshot,
    koku_kg: float,
    *,
    choices: Mapping[str, int] | None = None,
    quantities: Mapping[str, float] | None = None,
    custom: Sequence[Custom] = (),
) -> Reading:
    """The basket priced at the snapshot against the reference era. `quantities` overrides the
    basket's (0 switches a good off); `choices` picks a substitute per good."""
    choices = choices or {}
    qty = {**basket.quantities, **(quantities or {})}
    ref = model.reference.goods
    lines = []
    for good, q in qty.items():
        g = model.goods[good]
        opts = snapshot.options.get(good, ())
        pick = opts[min(max(choices.get(good, 0), 0), len(opts) - 1)] if opts else None
        lines.append(
            Line(
                good,
                g.name,
                g.unit,
                q,
                pick.dollars_per_unit if pick else None,
                ref[good].silver_g if good in ref else None,
                pick.priced_as if pick else '',
            )
        )
    for i, c in enumerate(custom):
        lines.append(Line(f'custom-{i}', c.name, c.unit, c.quantity, c.dollars, c.silver_g, ''))
    return Reading(tuple(lines), koku_kg, model.rice_ref)


@dataclass(frozen=True, slots=True)
class Conversion:
    era: Era
    unit: str
    amount: float
    silver_g: float
    goods_dollars: float
    wage_dollars: float
    rokugan_sen: float
    used: tuple[str, ...]
    left_out: tuple[str, ...]

    @property
    def coverage(self) -> str:
        if not self.left_out:
            return 'the whole basket'
        if self.used == ('Rice',):
            return 'rice alone'
        return f'{len(self.used)} of {len(self.used) + len(self.left_out)} goods'


def convert(
    model: Model,
    era: Era,
    amount: float,
    unit: str,
    basket: Basket,
    snapshot: Snapshot,
    koku_kg: float,
    modern_day_wage: float,
) -> Conversion:
    """An amount of an era's money -> goods dollars, wage dollars and Rokugani sen.

    Over the goods G priced in this era and the reference era: r = era silver(G) / reference
    silver(G) is how much dearer the era was, and the amount buys what S / r grams bought in
    Rokugan. Those grams are valued at Rokugan's own rate, the WHOLE basket's dollars over its
    reference silver (the goods priced in the reference and the snapshot), in goods dollars and in
    sen at the rice anchor, so the two always agree with the koku's headline dollars. Valuing them
    over G alone, as before diagram#13, made an era's dollars depend on which goods it happened to
    price: a rice-only era read in rice dollars, less than half the basket's. Wage dollars go by the
    era's own laborer's day."""
    if unit not in era.coins:
        raise SystemExit(f'{era.title} has no coin {unit!r}; have {", ".join(era.coins)}')
    ref = model.reference.goods
    used, left = [], []
    era_silver = ref_silver = basket_silver = dollars = 0.0
    for good, q in basket.quantities.items():
        if q <= 0:
            continue
        price = snapshot.price(good)
        if good in ref and price:
            basket_silver += q * ref[good].silver_g
            dollars += q * price
        name = model.goods[good].name
        if good in era.goods and good in ref:
            used.append(name)
            era_silver += q * era.goods[good].silver_g
            ref_silver += q * ref[good].silver_g
        else:
            left.append(name)
    if not used:
        raise SystemExit(f'{era.title} prices none of basket {basket.id!r}')
    silver = amount * era.coins[unit].silver_g
    in_ref = silver * ref_silver / era_silver
    return Conversion(
        era,
        unit,
        amount,
        silver,
        in_ref * dollars / basket_silver,
        silver / era.wage_g_per_day * modern_day_wage,
        in_ref * 1000 / (koku_kg * model.rice_ref),
        tuple(used),
        tuple(left),
    )


def reprice(
    model: Model, date: str, series: Mapping[str, float] | None = None, data: Path = DATA
) -> Path:
    """Start the snapshot for `date` from the newest: every good of every basket, each option's
    price and link blank for the session to fill, except an option tied to a BLS series, which is
    filled from `series` (dollars a pound, newest month) when it is given. `check` refuses the file
    until every option is filled."""
    path = data / 'snapshots' / f'{date}.json'
    if path.exists():
        raise SystemExit(f'{path.name} exists: a snapshot is never edited once committed')
    newest = model.snapshots[-1]
    wanted = sorted({g for b in model.baskets.values() for g in b.quantities})
    goods = {}
    for good in wanted:
        opts = newest.options.get(good) or (Option('', None, ''),)
        goods[good] = [_blank(o, series or {}) for o in opts]
    raw = {'date': date, 'priced_by': '', 'source': '', 'note': '', 'goods': goods}
    path.write_text(json.dumps(raw, indent=2, ensure_ascii=False) + '\n')
    return path


def _blank(opt: Option, series: Mapping[str, float]) -> dict[str, Any]:
    if opt.series:
        price = series.get(opt.series)
        return {
            'priced_as': opt.priced_as,
            'dollars_per_unit': None if price is None else round(price * opt.factor, 3),
            'link': opt.link if price is not None else '',
            'series': opt.series,
            'factor': opt.factor,
        }
    return {'priced_as': opt.priced_as, 'dollars_per_unit': None, 'link': ''}
