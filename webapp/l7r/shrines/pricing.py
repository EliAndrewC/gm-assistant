"""GM-only money: the fair price of a design, by contract, with porterage and the GM's prices for
the player's own additions.

Nothing here is ever rendered for a viewer without ledger access (the route builds a ledger only for
the GM and, read-only, for a player whose character has Commerce). It is a breakdown, nothing more:
how the GM settles the contracts at the table is up to the GM (GM 2026-10-26 - the per-contract
Commerce rolls, the budget and "what Tadashi keeps" were taken out to keep the tool general).
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from urllib.parse import urlencode

from l7r.shrines.catalog import GM_PREFIX, Catalog
from l7r.shrines.design import Design, first, share_query

__all__ = [
    'KOKU_MAX',
    'OTHER_CONTRACT',
    'ContractTotal',
    'Ledger',
    'LedgerSettings',
    'LineItem',
    'Pricing',
    'build_ledger',
    'format_koku',
    'format_number',
    'gm_query',
    'parse_settings',
    'price_design',
]

KOKU_MAX = 100_000.0
# Feature 228 (FR-005): the contract every player's "Something else" is priced under.
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


# --- the ledger (GM, and Commerce players read-only) --------------------------------------------


@dataclass(frozen=True, slots=True)
class LedgerSettings:
    """The GM's `gm_*` inputs: how remote the site is (porterage) and their prices for the player's
    own additions (absent = unpriced). Links from before 2026-10-26 also carry `gm_budget`,
    `gm_roll_*` and `gm_base_*`; those are ignored, and the design in the link opens as it did."""

    remoteness: str
    others: dict[str, float] = field(default_factory=dict)


def _koku(value: object) -> float | None:
    """A koku figure from a field: None when missing, blank or not a finite number."""
    raw = first(value)
    if raw is None:
        return None
    try:
        parsed = float(raw.strip())
    except ValueError:
        return None
    return max(0.0, min(KOKU_MAX, parsed)) if math.isfinite(parsed) else None


def parse_settings(catalog: Catalog, params: Mapping[str, object]) -> LedgerSettings:
    """Read the GM's `gm_*` settings; anything missing or malformed takes its default."""
    remoteness = first(params.get(GM_PREFIX + 'remote'))
    if remoteness not in {r.key for r in catalog.remoteness}:
        remoteness = catalog.default_remoteness
    others = {}
    for category in catalog.categories:
        price = _koku(params.get(f'{GM_PREFIX}other_{category.key}'))
        if price is not None:
            others[category.key] = price
    assert remoteness is not None
    return LedgerSettings(remoteness, others)


@dataclass(frozen=True, slots=True)
class ContractTotal:
    key: str
    label: str
    fair: float
    items: tuple[LineItem, ...]

    @property
    def unpriced(self) -> int:
        return sum(1 for i in self.items if not i.priced)


@dataclass(frozen=True, slots=True)
class Ledger:
    contracts: tuple[ContractTotal, ...]
    pricing: Pricing

    @property
    def total(self) -> float:
        return sum(c.fair for c in self.contracts)


def build_ledger(catalog: Catalog, design: Design, settings: LedgerSettings) -> Ledger:
    """The design's fair price, contract by contract, each with its items."""
    pricing = price_design(catalog, design, settings.remoteness, settings.others)
    results = []
    for contract in catalog.contracts:
        fair = pricing.by_contract[contract.key]
        # Other work shows while there is a "Something else" to price, even at nothing yet.
        if fair <= 0 and not (contract.key == OTHER_CONTRACT and design.others):
            continue
        items = tuple(i for i in pricing.items if i.contract == contract.key)
        results.append(ContractTotal(contract.key, contract.label, fair, items))
    return Ledger(tuple(results), pricing)


def gm_query(catalog: Catalog, design: Design, settings: LedgerSettings) -> str:
    """The GM's own link: the design plus every `gm_*` setting."""
    pairs = [(GM_PREFIX + 'remote', settings.remoteness)]
    pairs += [
        (f'{GM_PREFIX}other_{key}', format_number(price))
        for key, price in settings.others.items()
        if key in design.others
    ]
    share = share_query(catalog, design)
    return '&'.join(q for q in (share, urlencode(pairs)) if q)


# --- display ------------------------------------------------------------------------------------


def format_number(value: float) -> str:
    """12.0 -> '12', 12.5 -> '12.5' (for form fields)."""
    return f'{value:.2f}'.rstrip('0').rstrip('.')


def format_koku(value: float) -> str:
    """Koku to the nearest bu: 12.43 -> '12 koku 4 bu', 0.3 -> '3 bu', -2.5 -> '-2 koku 5 bu'.
    A price that rounds to nothing is 'under 1 bu', never '0 bu', which reads as a missing price
    (review 2026-10-26: the bamboo box and the stream at 0.02 and 0.05 koku)."""
    sign = '-' if value < 0 else ''
    bu_total = round(abs(value) * 10)
    if bu_total == 0 and value > 0:
        return 'under 1 bu'
    koku, bu = divmod(bu_total, 10)
    parts = []
    if koku:
        parts.append(f'{koku:,} koku')
    if bu or not koku:
        parts.append(f'{bu} bu')
    return sign + ' '.join(parts)
