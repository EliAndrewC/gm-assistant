"""Shrine builder (feature 216): the catalog, a design read from a link, and the GM's ledger.

A player designs a small, remote, unstaffed shrine by picking one option per category; the whole
design lives in the page's query string, so the link IS the save. The GM opens the same link and
sees what it costs: each option carries GM-only price `lines`, grouped into the contracts a builder
would let, and the GM enters Tadashi's Commerce roll per contract to see what he saves and keeps.

Secrecy is structural: `catalog.yaml` sits outside `static/` and is never served, and the template
receives a `Ledger` only when the viewer is a GM. Nothing in this module decides who is a GM.

The why behind the prices and the negotiation formula is in `CLAUDE.md` next to this file.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import yaml

CATALOG_PATH = Path(__file__).with_name('catalog.yaml')

# Free-text fields, with their length caps (a hand-edited link cannot make the page arbitrarily
# large). Just the one, pre-filled from the catalog: the page never assigns homework (spec FR-017).
TEXT_FIELDS: dict[str, int] = {'shrine_name': 120}

GM_PREFIX = 'gm_'
DEFAULT_BASELINE = 25  # the Culture gift rule's "roll minus 25" (rules/02-skills.md)
ROLL_MAX = 200
BUDGET_MAX = 100_000.0


class CatalogError(ValueError):
    """The catalog file is inconsistent (an unknown contract, a reference that is no option...)."""


@dataclass(frozen=True, slots=True)
class Line:
    """One GM-only price line on an option."""

    contract: str
    koku: float
    heavy: float = 0.0
    per: str | None = None


@dataclass(frozen=True, slots=True)
class Option:
    key: str
    label: str
    text: str
    ja: str = ''
    romaji: str = ''
    lines: tuple[Line, ...] = ()
    voids: tuple[str, ...] = ()
    units: float = 1.0


@dataclass(frozen=True, slots=True)
class Category:
    key: str
    label: str
    prompt: str
    reference: str
    options: tuple[Option, ...]

    def option(self, key: str) -> Option | None:
        for option in self.options:
            if option.key == key:
                return option
        return None


@dataclass(frozen=True, slots=True)
class Group:
    key: str
    label: str
    intro: str
    categories: tuple[Category, ...]


@dataclass(frozen=True, slots=True)
class Contract:
    key: str
    label: str


@dataclass(frozen=True, slots=True)
class Remoteness:
    key: str
    label: str
    rate: float


@dataclass(frozen=True, slots=True)
class SiteLine:
    label: str
    contract: str
    koku: float


@dataclass(frozen=True, slots=True)
class Catalog:
    groups: tuple[Group, ...]
    contracts: tuple[Contract, ...]
    remoteness: tuple[Remoteness, ...]
    default_remoteness: str
    site_lines: tuple[SiteLine, ...]
    budget_padding: float
    default_name: str = ''

    @property
    def categories(self) -> tuple[Category, ...]:
        return tuple(c for g in self.groups for c in g.categories)

    def category(self, key: str) -> Category | None:
        for category in self.categories:
            if category.key == key:
                return category
        return None

    def remoteness_rate(self, key: str) -> float:
        return next(r.rate for r in self.remoteness if r.key == key)


# --- loading ------------------------------------------------------------------------------------


def _line(raw: Mapping[str, Any]) -> Line:
    per = raw.get('per')
    return Line(
        contract=str(raw['contract']),
        koku=float(raw['koku']),
        heavy=float(raw.get('heavy', 0)),
        per=None if per is None else str(per),
    )


def _option(raw: Mapping[str, Any]) -> Option:
    return Option(
        key=str(raw['key']),
        label=str(raw['label']),
        text=' '.join(str(raw['text']).split()),
        ja=str(raw.get('ja', '')),
        romaji=str(raw.get('romaji', '')),
        lines=tuple(_line(x) for x in raw.get('lines', ())),
        voids=tuple(str(x) for x in raw.get('voids', ())),
        units=float(raw.get('units', 1)),
    )


def _category(raw: Mapping[str, Any]) -> Category:
    return Category(
        key=str(raw['key']),
        label=str(raw['label']),
        prompt=str(raw['prompt']),
        reference=str(raw['reference']),
        options=tuple(_option(x) for x in raw['options']),
    )


def parse_catalog(data: Mapping[str, Any]) -> Catalog:
    """Build a Catalog from parsed YAML and check that it hangs together."""
    catalog = Catalog(
        groups=tuple(
            Group(
                key=str(g['key']),
                label=str(g['label']),
                intro=' '.join(str(g['intro']).split()),
                categories=tuple(_category(c) for c in g['categories']),
            )
            for g in data['groups']
        ),
        contracts=tuple(Contract(str(c['key']), str(c['label'])) for c in data['contracts']),
        remoteness=tuple(
            Remoteness(str(r['key']), str(r['label']), float(r['rate']))
            for r in data['remoteness']['options']
        ),
        default_remoteness=str(data['remoteness']['default']),
        site_lines=tuple(
            SiteLine(str(s['label']), str(s['contract']), float(s['koku']))
            for s in data['site_lines']
        ),
        budget_padding=float(data['budget_padding']),
        default_name=str(data.get('default_name', '')),
    )
    _validate(catalog)
    return catalog


def _validate(catalog: Catalog) -> None:
    contracts = {c.key for c in catalog.contracts}
    keys = [c.key for c in catalog.categories]
    if len(keys) != len(set(keys)):
        raise CatalogError('duplicate category key')
    if any(k.startswith(GM_PREFIX) for k in keys) or set(keys) & set(TEXT_FIELDS):
        raise CatalogError('a category key collides with a text field or the gm_ prefix')
    if 'porterage' not in contracts:
        raise CatalogError('the catalog needs a porterage contract for heavy lines')
    if catalog.default_remoteness not in {r.key for r in catalog.remoteness}:
        raise CatalogError(f'unknown default remoteness {catalog.default_remoteness!r}')
    for site in catalog.site_lines:
        if site.contract not in contracts:
            raise CatalogError(f'site line uses unknown contract {site.contract!r}')
    for category in catalog.categories:
        option_keys = {o.key for o in category.options}
        if category.reference not in option_keys:
            raise CatalogError(f'{category.key}: {category.reference!r} is not one of its options')
        for option in category.options:
            for void in option.voids:
                if void not in keys or void == category.key:
                    raise CatalogError(f'{category.key}.{option.key} voids unknown {void!r}')
            for line in option.lines:
                if line.contract not in contracts:
                    raise CatalogError(f'{category.key}.{option.key}: unknown contract')
                if line.per is not None and line.per not in keys:
                    raise CatalogError(f'{category.key}.{option.key}: per unknown {line.per!r}')


def load_catalog(path: Path = CATALOG_PATH) -> Catalog:
    with path.open(encoding='utf-8') as fh:
        return parse_catalog(yaml.safe_load(fh))


# --- the design (the player's half) -------------------------------------------------------------


def _first(value: object) -> str | None:
    """CherryPy hands a repeated query key over as a list; take its first value."""
    if isinstance(value, list):
        value = value[0] if value else None
    return value if isinstance(value, str) else None


@dataclass(frozen=True, slots=True)
class Design:
    """The player's selections. `choices` holds only categories that apply."""

    choices: dict[str, str]
    voided: frozenset[str]
    text: dict[str, str]
    dropped: tuple[str, ...] = ()


def parse_design(catalog: Catalog, params: Mapping[str, object]) -> Design:
    """Read a design from query parameters. Only real choices are kept: nothing is pre-selected
    (an option already picked on arrival biases the player - GM 2026-10-17), so a category the
    player has not reached yet is simply absent and costs nothing.

    `dropped` names categories whose value was present but not a current option (an old link, or a
    hand-edited one), so the page can say a choice could not be restored.
    """
    chosen: dict[str, str] = {}
    dropped: list[str] = []
    for category in catalog.categories:
        raw = _first(params.get(category.key))
        if raw is not None and category.option(raw) is not None:
            chosen[category.key] = raw
        elif raw is not None:
            dropped.append(category.key)
    voided = _voided(catalog, chosen)
    text = {}
    for name, cap in TEXT_FIELDS.items():
        raw = _first(params.get(name))
        if raw is not None and raw.strip():
            text[name] = raw.strip()[:cap]
    # A blank or missing name falls back to the catalog's, so the field is never empty.
    if 'shrine_name' not in text and catalog.default_name:
        text['shrine_name'] = catalog.default_name
    return Design(
        choices={k: v for k, v in chosen.items() if k not in voided},
        voided=voided,
        text=text,
        dropped=tuple(d for d in dropped if d not in voided),
    )


def _voided(catalog: Catalog, chosen: Mapping[str, str]) -> frozenset[str]:
    """Categories made moot by other choices, to a fixpoint: a voided category voids nothing."""
    voided: frozenset[str] = frozenset()
    while True:
        nxt = frozenset(
            v
            for category in catalog.categories
            if category.key not in voided and category.key in chosen
            for v in _chosen_option(category, chosen).voids
        )
        if nxt == voided:
            return voided
        voided = nxt


def _chosen_option(category: Category, chosen: Mapping[str, str]) -> Option:
    option = category.option(chosen[category.key])
    assert option is not None  # parse_design only stores real option keys
    return option


def voided_by(catalog: Catalog, design: Design) -> dict[str, str]:
    """For each moot category, the label of the category whose choice made it moot."""
    return {
        void: category.label
        for category in catalog.categories
        if category.key in design.choices
        for void in _chosen_option(category, design.choices).voids
    }


def share_query(catalog: Catalog, design: Design) -> str:
    """The query string that reproduces `design` and nothing else - never a GM figure."""
    pairs = [(c.key, design.choices[c.key]) for c in catalog.categories if c.key in design.choices]
    pairs += [(name, design.text[name]) for name in TEXT_FIELDS if name in design.text]
    return urlencode(pairs)


def reference_design(catalog: Catalog) -> Design:
    """The "fairly nice small forest shrine" the default budget is priced from."""
    return parse_design(catalog, {c.key: c.reference for c in catalog.categories})


# --- pricing (GM only) --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class LineItem:
    category: str
    option: str
    contract: str
    koku: float
    heavy: float


@dataclass(frozen=True, slots=True)
class Pricing:
    items: tuple[LineItem, ...]
    heavy: float
    rate: float
    by_contract: dict[str, float]

    @property
    def total(self) -> float:
        return sum(self.by_contract.values())


def price_design(catalog: Catalog, design: Design, remoteness: str) -> Pricing:
    """Fair price of every line in the design, by contract, with porterage on heavy lines."""
    items: list[LineItem] = [
        LineItem('Site preparation', s.label, s.contract, s.koku, 0.0) for s in catalog.site_lines
    ]
    for category in catalog.categories:
        if category.key not in design.choices:
            continue
        option = _chosen_option(category, design.choices)
        for line in option.lines:
            factor = 1.0
            if line.per is not None:
                per_category = catalog.category(line.per)
                assert per_category is not None  # _validate checked `per`
                factor = (
                    _chosen_option(per_category, design.choices).units
                    if line.per in design.choices
                    else 1.0
                )
            items.append(
                LineItem(
                    category.label,
                    option.label,
                    line.contract,
                    line.koku * factor,
                    line.heavy * factor,
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


def _int(value: object, low: int, high: int) -> int | None:
    raw = _first(value)
    if raw is None:
        return None
    try:
        number = int(raw.strip())
    except ValueError:
        return None
    return max(low, min(high, number))


def parse_negotiation(catalog: Catalog, params: Mapping[str, object]) -> Negotiation:
    """Read the GM's `gm_*` settings; anything missing or malformed takes its default."""
    budget = default_budget(catalog)
    raw_budget = _first(params.get(GM_PREFIX + 'budget'))
    if raw_budget is not None:
        try:
            parsed = float(raw_budget.strip())
        except ValueError:
            parsed = math.nan
        if math.isfinite(parsed):
            budget = max(0.0, min(BUDGET_MAX, parsed))
    remoteness = _first(params.get(GM_PREFIX + 'remote'))
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
    assert remoteness is not None
    return Negotiation(budget, remoteness, rolls, baselines)


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
    pricing = price_design(catalog, design, negotiation.remoteness)
    results = []
    for contract in catalog.contracts:
        fair = pricing.by_contract[contract.key]
        if fair <= 0:
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
