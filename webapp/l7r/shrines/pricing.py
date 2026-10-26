"""GM-only money: the fair price of a design, porterage, and Tadashi's per-contract haggling.

Nothing here is ever rendered for a non-GM viewer (the route builds a ledger only for a GM
session). The why behind the prices and the negotiation formula is in `CLAUDE.md`.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from urllib.parse import urlencode

from l7r.shrines.catalog import GM_PREFIX, Catalog
from l7r.shrines.design import Design, first, reference_design, share_query

__all__ = [
    'BUDGET_MAX',
    'OTHER_CONTRACT',
    'DEFAULT_BASELINE',
    'ROLL_MAX',
    'ContractResult',
    'Ledger',
    'LineItem',
    'Negotiation',
    'Pricing',
    'default_budget',
    'format_koku',
    'format_number',
    'gm_query',
    'negotiate',
    'parse_negotiation',
    'price_design',
    'saving_percent',
]

DEFAULT_BASELINE = 25  # the Culture gift rule's "roll minus 25" (rules/02-skills.md)
ROLL_MAX = 200
BUDGET_MAX = 100_000.0
# Feature 228 (FR-005): the contract every player's "Something else" is priced and haggled under.
OTHER_CONTRACT = 'other'


# --- pricing (GM only) --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class LineItem:
    category: str
    option: str
    contract: str
    koku: float
    heavy: float
    # Feature 228: a "Something else" line names its step, and is unpriced until the GM prices it.
    step: str = ''
    priced: bool = True


@dataclass(frozen=True, slots=True)
class Pricing:
    items: tuple[LineItem, ...]
    heavy: float
    rate: float
    by_contract: dict[str, float]

    @property
    def unpriced(self) -> int:
        """How many "Something else" lines the GM has not priced: the totals are not whole."""
        return sum(1 for i in self.items if not i.priced)

    @property
    def total(self) -> float:
        return sum(self.by_contract.values())


def price_design(
    catalog: Catalog,
    design: Design,
    remoteness: str,
    other_prices: Mapping[str, float] | None = None,
) -> Pricing:
    """Fair price of every line in the design, by contract, with porterage on heavy lines. Each
    "Something else" is a line of the Other work contract at the GM's price, or unpriced."""
    items: list[LineItem] = [
        LineItem('Site preparation', s.label, s.contract, s.koku, 0.0) for s in catalog.site_lines
    ]
    picked = [
        (category, key)
        for category in catalog.categories
        for key in (
            (design.choices[category.key],)
            if category.key in design.choices
            else design.multi.get(category.key, ())
        )
    ]
    for category, key in picked:
        option = category.option(key)
        assert option is not None  # resolve() keeps only real option keys
        for line in option.lines:
            factor = 1.0
            if line.per is not None:
                per_category = catalog.category(line.per)
                assert per_category is not None  # _validate checked `per`
                per_option = (
                    per_category.option(design.choices[line.per])
                    if line.per in design.choices
                    else None
                )
                factor = per_option.units if per_option is not None else 1.0
            items.append(
                LineItem(
                    category.label,
                    option.label,
                    line.contract,
                    line.koku * factor,
                    line.heavy * factor,
                )
            )
    for key, other in design.others.items():
        step = catalog.category(key)
        assert step is not None  # parse_design reads others only for catalog steps
        price = (other_prices or {}).get(key)
        items.append(
            LineItem(
                step.label,
                f'{"instead, " if other.instead else "plus "}{other.text}',
                OTHER_CONTRACT,
                price or 0.0,
                0.0,
                step=key,
                priced=price is not None,
            )
        )
    rate = catalog.remoteness_rate(remoteness)
    heavy = sum(i.heavy for i in items)
    by_contract = {c.key: 0.0 for c in catalog.contracts}
    for item in items:
        by_contract[item.contract] += item.koku
    by_contract['porterage'] += heavy * rate
    return Pricing(tuple(items), heavy, rate, by_contract)


def default_budget(catalog: Catalog) -> float:
    """Reference design at the default remoteness, padded for Tadashi's win, rounded up to 5."""
    fair = price_design(catalog, reference_design(catalog), catalog.default_remoteness).total
    return float(5 * math.ceil(fair * catalog.budget_padding / 5))


# --- the negotiation (GM only) ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Negotiation:
    budget: float
    remoteness: str
    rolls: dict[str, int] = field(default_factory=dict)
    baselines: dict[str, int] = field(default_factory=dict)
    # Feature 228: the GM's price for a step's "Something else" (absent = unpriced).
    others: dict[str, float] = field(default_factory=dict)


def _int(value: object, low: int, high: int) -> int | None:
    raw = first(value)
    if raw is None:
        return None
    try:
        number = int(raw.strip())
    except ValueError:
        return None
    return max(low, min(high, number))


def _koku(value: object) -> float | None:
    """A koku figure from a field: None when missing, blank or not a finite number."""
    raw = first(value)
    if raw is None:
        return None
    try:
        parsed = float(raw.strip())
    except ValueError:
        return None
    return max(0.0, min(BUDGET_MAX, parsed)) if math.isfinite(parsed) else None


def parse_negotiation(catalog: Catalog, params: Mapping[str, object]) -> Negotiation:
    """Read the GM's `gm_*` settings; anything missing or malformed takes its default."""
    budget = _koku(params.get(GM_PREFIX + 'budget'))
    if budget is None:
        budget = default_budget(catalog)
    remoteness = first(params.get(GM_PREFIX + 'remote'))
    if remoteness not in {r.key for r in catalog.remoteness}:
        remoteness = catalog.default_remoteness
    rolls: dict[str, int] = {}
    baselines: dict[str, int] = {}
    for contract in catalog.contracts:
        roll = _int(params.get(f'{GM_PREFIX}roll_{contract.key}'), 0, ROLL_MAX)
        if roll is not None:
            rolls[contract.key] = roll
        base = _int(params.get(f'{GM_PREFIX}base_{contract.key}'), 0, ROLL_MAX)
        if base is not None:
            baselines[contract.key] = base
    others = {}
    for category in catalog.categories:
        price = _koku(params.get(f'{GM_PREFIX}other_{category.key}'))
        if price is not None:
            others[category.key] = price
    assert remoteness is not None
    return Negotiation(budget, remoteness, rolls, baselines, others)


@dataclass(frozen=True, slots=True)
class ContractResult:
    key: str
    label: str
    fair: float
    roll: int | None
    baseline: int
    saving_pct: int
    items: tuple[LineItem, ...]

    @property
    def paid(self) -> float:
        return self.fair * (100 - self.saving_pct) / 100


@dataclass(frozen=True, slots=True)
class Ledger:
    contracts: tuple[ContractResult, ...]
    budget: float
    pricing: Pricing

    @property
    def fair_total(self) -> float:
        return sum(c.fair for c in self.contracts)

    @property
    def paid_total(self) -> float:
        return sum(c.paid for c in self.contracts)

    @property
    def remainder(self) -> float:
        """What Tadashi keeps; negative means the design costs more than the budget."""
        return self.budget - self.paid_total


def saving_percent(roll: int | None, baseline: int) -> int:
    """max(0, roll - baseline) percent, capped at 100 - the gift rule's shape (research R5)."""
    if roll is None:
        return 0
    return max(0, min(100, roll - baseline))


def negotiate(catalog: Catalog, design: Design, negotiation: Negotiation) -> Ledger:
    pricing = price_design(catalog, design, negotiation.remoteness, negotiation.others)
    results = []
    for contract in catalog.contracts:
        fair = pricing.by_contract[contract.key]
        # Other work shows while there is a "Something else" to price, even at nothing yet.
        if fair <= 0 and not (contract.key == OTHER_CONTRACT and design.others):
            continue
        roll = negotiation.rolls.get(contract.key)
        baseline = negotiation.baselines.get(contract.key, DEFAULT_BASELINE)
        results.append(
            ContractResult(
                key=contract.key,
                label=contract.label,
                fair=fair,
                roll=roll,
                baseline=baseline,
                saving_pct=saving_percent(roll, baseline),
                items=tuple(i for i in pricing.items if i.contract == contract.key),
            )
        )
    return Ledger(tuple(results), negotiation.budget, pricing)


def gm_query(catalog: Catalog, design: Design, negotiation: Negotiation) -> str:
    """The GM's own link: the design plus every `gm_*` setting."""
    pairs = [
        (GM_PREFIX + 'budget', format_number(negotiation.budget)),
        (GM_PREFIX + 'remote', negotiation.remoteness),
    ]
    for contract in catalog.contracts:
        if contract.key in negotiation.rolls:
            pairs.append((f'{GM_PREFIX}roll_{contract.key}', str(negotiation.rolls[contract.key])))
        if contract.key in negotiation.baselines:
            pairs.append(
                (f'{GM_PREFIX}base_{contract.key}', str(negotiation.baselines[contract.key]))
            )
    pairs += [
        (f'{GM_PREFIX}other_{key}', format_number(price))
        for key, price in negotiation.others.items()
        if key in design.others
    ]
    share = share_query(catalog, design)
    return '&'.join(q for q in (share, urlencode(pairs)) if q)


# --- display ------------------------------------------------------------------------------------


def format_number(value: float) -> str:
    """12.0 -> '12', 12.5 -> '12.5' (for form fields)."""
    return f'{value:.2f}'.rstrip('0').rstrip('.')


def format_koku(value: float) -> str:
    """Koku to the nearest bu: 12.43 -> '12 koku 4 bu', 0.3 -> '3 bu', -2.5 -> '-2 koku 5 bu'."""
    sign = '-' if value < 0 else ''
    bu_total = round(abs(value) * 10)
    koku, bu = divmod(bu_total, 10)
    parts = []
    if koku:
        parts.append(f'{koku:,} koku')
    if bu or not koku:
        parts.append(f'{bu} bu')
    return sign + ' '.join(parts)
