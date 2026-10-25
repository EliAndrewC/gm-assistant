"""Baskets of goods, their dated dollar prices, and the eras that price them in silver (222).

Three kinds of data, kept apart so each can change alone:

- a BASKET is what is bought: goods and quantities per adult per year (`data/baskets/<id>.json`);
- a SNAPSHOT is what each good cost in US dollars in a month, first option the default and the rest
  substitutes (`data/snapshots/YYYY-MM.json`, never edited once committed);
- an ERA is what the goods, the coins and an unskilled day cost in grams of pure silver at one place
  and time (`data/eras/<id>.json`; a new era is a new file).

THE REFERENCE ERA ANCHORS THE COIN; ALL THE ERAS PRICE THE GOODS (feature 223). The 2017 sheet
anchored the zeni on Kyoto 1745-54's rice price (1.49 g of silver a kg at Bassino & Ma's 3.11 g a
monme; 0.826 g at the Genbun monme's 1.725 g of pure silver, which the reference era uses since
diagram#13), and a koku is that rice's silver. Every other good's Rokugani price is the weighted
geometric mean, over the eras that price it beside rice, of its price IN RICE (kg of rice a unit),
times the rice anchor: each era's silver was its own coinage, debased or not, and Rokugan's coin is
pegged to rice, so rice is the numeraire. The mean across eras is geometric because a price in rice
is a ratio (fish at twice rice and fish at half rice average to rice, whichever good is the
numeraire). Era weights are the GM's (`data/era-weights.json`, default 1 each, provisional: the GM,
2026-10-25, *"how representative we think they are of our setting"*); only Kyoto 1745-54 at 1
reproduces feature 222's prices exactly.

A KOKU'S GOODS-DOLLAR VALUE IS AN INDEX OVER GOODS, AND IT HAS NO SINGLE ANSWER (feature 223). Each
good's single-good koku is what a koku's silver bought of that good alone, at today's dollars (rice:
151.5 kg times today's rice price). They span about a hundredfold (cloth ~$36, housing ~$4,400), so
the figure depends on the mean. Two readings, shown together as the range:

- the WHOLE BASKET: a year's necessities cost N koku in Rokugan and $D today, so a koku is $D/N.
  That is, identically, the spending-weighted ARITHMETIC mean of the single-good kokus (a Laspeyres
  index), and it is the high reading: base-period weights over prices that moved a hundredfold are
  dominated by the goods that became dear (housing alone is over half of it).
- the AVERAGE OVER GOODS: the single-good kokus averaged by the chosen mean, by default the
  spending-weighted GEOMETRIC mean, the central reading (the mean statistical agencies use where
  buyers substitute, and the one an outlier cannot dominate). Fisher (the geometric mean of
  Laspeyres and Paasche) replaces it as central once modern quantities exist (diagram#17
  question 6).
  Goods switched off or added by a visitor change this reading only.

An era's money converts by that era's price level against Rokugan's over the goods priced in both,
by the same mean, valued at the reading's dollars a Rokugani gram.

A GOOD COUNTS ONLY WHERE IT IS PRICED ON EVERY SIDE IN USE. The 2017 snapshot never priced salt,
fuel or housing, and Tokyo 1882-86 has no price for them either; such goods are left out of that
reading and named, never priced at zero (which would silently shrink one side of the ratio).

WHY HOUSING IS A GOOD, NOT ALLEN'S 5% RENT MARKUP: a uniform markup on both sides of a ratio
cancels, so it would change nothing; the GM approved housing in the standard basket (spec 222,
FR-008).
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

__all__ = [
    'DATA',
    'STANDARD',
    'MEANS',
    'Basket',
    'Conversion',
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
MEANS = ('geometric', 'arithmetic')


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
    complete: bool = False  # a whole household year: only these feed the whole-basket reading


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
    borrowed: str = (
        ''  # not an independent price in rice (from another era, or set equal to a good)
    )
    excluded: str = ''  # not a pre-modern price (the GM's ruling): never in the cross-era mean


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
    era_weights: Mapping[str, float] = field(default_factory=dict)  # an era not named weighs 1

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

    def weights(self, overrides: Mapping[str, float] | None = None) -> dict[str, float]:
        """Every era's weight: the override, else the data file's, else 1. If no era that prices
        rice keeps a weight, the reference era alone stands (never a division by zero)."""
        overrides = overrides or {}
        w = {e: max(overrides.get(e, self.era_weights.get(e, 1.0)), 0.0) for e in self.eras}
        if not any(w[e.id] and 'rice' in e.goods for e in self.eras.values()):
            w = {e: float(e == self.reference.id) for e in self.eras}
        return w

    def reference_only(self) -> dict[str, float]:
        """Kyoto 1745-54 alone: feature 222's prices, which the calibration tests pin."""
        return {e: float(e == self.reference.id) for e in self.eras}

    def rests_on(self, good: str, weights: Mapping[str, float] | None = None) -> tuple[str, ...]:
        """The eras whose prices make up this good's Rokugani price under these weights. A
        borrowed price (another era's ratio, or a good set equal to another) is left out unless no
        weighted era observes the good, so one observation never counts twice. An excluded price
        (one the opening to foreign trade changed, such as Tokyo 1882's kerosene) is left out even
        then: it is not a pre-modern price at all, so it may not stand in for one."""
        w = self.weights(weights)
        eras = [
            e
            for e in self.eras.values()
            if w[e.id] and good in e.goods and 'rice' in e.goods and not e.goods[good].excluded
        ]
        observed = [e for e in eras if not e.goods[good].borrowed]
        return tuple(e.id for e in (observed or eras))

    def prices(self, weights: Mapping[str, float] | None = None) -> dict[str, float]:
        """Rokugan's grams of silver a unit of each good: the weighted geometric mean over the
        eras of its price in rice, times the rice anchor. A good no weighted era prices is
        absent."""
        w = self.weights(weights)
        out = {}
        for good in self.goods:
            num = den = 0.0
            for era_id in self.rests_on(good, w):
                g = self.eras[era_id].goods
                num += w[era_id] * math.log(g[good].silver_g / g['rice'].silver_g)
                den += w[era_id]
            if den:
                out[good] = self.rice_ref * math.exp(num / den)
        return out


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
        baskets[path.stem] = Basket(
            path.stem, raw['name'], raw['description'], raw['goods'], raw.get('complete', False)
        )
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
                k: Price(
                    v['silver_g'],
                    v['label'],
                    v['source'],
                    v.get('note', ''),
                    v.get('borrowed', ''),
                    v.get('excluded', ''),
                )
                for k, v in raw['goods'].items()
            },
            raw['wage']['silver_g_per_day'],
            raw['wage']['source'],
        )
    weights_path = data / 'era-weights.json'
    weights = _read(weights_path)['weights'] if weights_path.exists() else {}
    return Model(goods, baskets, tuple(snapshots), eras, weights)


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
    for era_id, weight in model.era_weights.items():
        if era_id not in model.eras:
            out.append(f'era-weights: unknown era {era_id!r}')
        elif weight < 0:
            out.append(f'era-weights: negative weight for {era_id}')
    if not any(b.complete for b in model.baskets.values()):
        out.append('no basket is marked complete (the whole-basket reading needs one)')
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
    mean: str = 'geometric'
    equal: bool = False  # weigh every counted good alike instead of by its share of spending

    @property
    def dollars(self) -> float:
        return sum(line.dollars for line in self.lines)

    @property
    def silver(self) -> float:
        return sum(line.silver for line in self.lines)

    @property
    def koku_silver(self) -> float:
        return self.koku_kg * self.rice_ref

    @property
    def koku_cost(self) -> float:
        """N: what the counted goods cost in Rokugan, in koku."""
        return self.silver / self.koku_silver

    def alone(self, line: Line) -> float:
        """The single-good koku: what a koku's silver bought of this good, at today's dollars."""
        return (line.dollars_per_unit or 0) / (line.silver_per_unit or 1) * self.koku_silver

    @property
    def weighted(self) -> tuple[tuple[Line, float], ...]:
        """Each counted good with its weight in the average (summing to 1)."""
        counted = [ln for ln in self.lines if ln.counted]
        if self.equal:
            return tuple((ln, 1 / len(counted)) for ln in counted)
        return tuple((ln, ln.silver / self.silver) for ln in counted)

    @property
    def arithmetic(self) -> float:
        """With spending weights, identically $D/N: the whole-basket reading."""
        return sum(w * self.alone(ln) for ln, w in self.weighted)

    @property
    def geometric(self) -> float:
        if not self.weighted:
            return 0.0
        return math.exp(sum(w * math.log(self.alone(ln)) for ln, w in self.weighted))

    @property
    def whole(self) -> float:
        """$D/N over the counted goods: the basket's dollars over its koku. Equal to `arithmetic`
        under spending weights."""
        return self.dollars / self.silver * self.koku_silver if self.silver else 0.0

    @property
    def per_koku(self) -> float:
        """Goods dollars a koku by the chosen mean."""
        return self.geometric if self.mean == 'geometric' else self.arithmetic

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
    mean: str = 'geometric',
    equal: bool = False,
    weights: Mapping[str, float] | None = None,
) -> Reading:
    """The basket priced at the snapshot against Rokugan's prices under these era weights.
    `quantities` overrides the basket's (0 switches a good off); `choices` picks a substitute."""
    if mean not in MEANS:
        raise SystemExit(f'no mean {mean!r}; have {", ".join(MEANS)}')
    choices = choices or {}
    qty = {**basket.quantities, **(quantities or {})}
    ref = model.prices(weights)
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
                ref.get(good),
                pick.priced_as if pick else '',
            )
        )
    return Reading(tuple(lines), koku_kg, model.rice_ref, mean, equal)


@dataclass(frozen=True, slots=True)
class Conversion:
    era: Era
    unit: str
    amount: float
    silver_g: float
    goods_dollars: float
    goods_dollars_high: float
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
    *,
    mean: str = 'geometric',
    weights: Mapping[str, float] | None = None,
) -> Conversion:
    """An amount of an era's money -> goods dollars, wage dollars and Rokugani sen.

    Over the goods G priced in this era and in Rokugan, the era's price level against Rokugan's is
    the mean of era price / Rokugani price, weighted by Rokugan's spending on G (by `mean`; the
    arithmetic form is the basket ratio sum(q x era) / sum(q x Rokugan)); the amount buys what S /
    level grams bought in Rokugan. Those grams are valued at the whole basket's reading by the same
    mean, in goods dollars and in sen at the rice anchor, so the two always agree with the koku's
    headline. Valuing them over G alone, as before diagram#13, made an era's dollars depend on which
    goods it happened to price. `goods_dollars_high` is the same by the arithmetic mean throughout
    (the whole-basket, high reading). Wage dollars go by the era's own laborer's day."""
    if unit not in era.coins:
        raise SystemExit(f'{era.title} has no coin {unit!r}; have {", ".join(era.coins)}')
    rok = model.prices(weights)
    full = reading(model, basket, snapshot, koku_kg, mean=mean, weights=weights)
    used, left = [], []
    shared: list[tuple[float, float]] = []  # (Rokugan spending, era price / Rokugani price)
    for good, q in basket.quantities.items():
        if q <= 0:
            continue
        name = model.goods[good].name
        if good in era.goods and good in rok:
            used.append(name)
            shared.append((q * rok[good], era.goods[good].silver_g / rok[good]))
        else:
            left.append(name)
    if not used:
        raise SystemExit(f'{era.title} prices none of basket {basket.id!r}')
    total = sum(s for s, _ in shared)
    arith = sum(s * r for s, r in shared) / total
    level = (
        math.exp(sum(s * math.log(r) for s, r in shared) / total) if mean == 'geometric' else arith
    )
    silver = amount * era.coins[unit].silver_g
    in_rok = silver / level
    return Conversion(
        era,
        unit,
        amount,
        silver,
        in_rok / full.koku_silver * full.per_koku,
        silver / arith / full.koku_silver * full.arithmetic,
        silver / era.wage_g_per_day * modern_day_wage,
        in_rok * 1000 / full.koku_silver,
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
