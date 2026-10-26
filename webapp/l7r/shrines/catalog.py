"""The shrine catalog: what can be chosen, the rules for when it applies, and the GM-only prices.

The data lives in `data/catalog.yaml` (contracts, remoteness, site lines, the order of groups)
and one `data/groups/<key>.yaml` per wizard section. `load_raw` merges them into one dict and
`parse_catalog` turns that into frozen dataclasses and validates it; tests mutate the raw dict.

The one applicability rule is `when` (see `Condition` and `data/catalog.yaml`): every clause names
an EARLIER category, so `design.parse_design` resolves the whole wizard in one forward pass.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

__all__ = [
    'DATA_DIR',
    'GM_PREFIX',
    'INSTEAD_PREFIX',
    'OTHER_CAP',
    'OTHER_PREFIX',
    'TEXT_FIELDS',
    'Catalog',
    'CatalogError',
    'Category',
    'Clause',
    'Condition',
    'Contract',
    'Group',
    'Line',
    'Option',
    'Phase',
    'Remoteness',
    'SiteLine',
    'load_catalog',
    'load_raw',
    'holds_all',
    'parse_catalog',
]

DATA_DIR = Path(__file__).with_name('data')

# Free-text fields, with their length caps (a hand-edited link cannot make the page arbitrarily
# large). Just the one, pre-filled from the catalog: the page never assigns homework (FR-017).
TEXT_FIELDS: dict[str, int] = {'shrine_name': 120}

GM_PREFIX = 'gm_'

# Feature 228 (FR-003): a step's "Something else" rides in the link as `other_<step>=<text>`, and
# `instead_<step>=1` when it replaces the cards rather than adding to the pick. Optional, so the
# no-homework rule (FR-017) still holds: nothing makes the player type.
OTHER_PREFIX = 'other_'
INSTEAD_PREFIX = 'instead_'
OTHER_CAP = 300


class CatalogError(ValueError):
    """The catalog is inconsistent (an unknown contract, a rule pointing forward, ...)."""


@dataclass(frozen=True, slots=True)
class Clause:
    """One `when` clause: category `key` has one of `options` (or, if `negate`, none of them)."""

    key: str
    options: frozenset[str]
    negate: bool = False

    def holds(self, choices: Mapping[str, str]) -> bool:
        """An unchosen (or not-in-play) category is "no value": a plain clause fails, a negated
        one passes."""
        present = choices.get(self.key) in self.options
        return not present if self.negate else present


Condition = tuple[Clause, ...]


def holds_all(condition: Condition, choices: Mapping[str, str]) -> bool:
    return all(clause.holds(choices) for clause in condition)


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
    appeal: str = ''
    lines: tuple[Line, ...] = ()
    # Replacement text per named wording (FR-030/FR-032/FR-037): {wording: {field: text}}.
    wording: dict[str, dict[str, str]] = field(default_factory=dict)
    # Offered only when this holds (FR-036).
    when: Condition = ()
    units: float = 1.0
    # FR-043: what the Japanese term means, shown as a tooltip on the term.
    gloss: str = ''
    # FR-044: on a multi-select step, picking this one clears the others (and vice versa).
    exclusive: bool = False
    # Feature 228 (FR-007): what it looks like, for the image prompt ('' = nothing to see).
    look: str = ''


@dataclass(frozen=True, slots=True)
class Category:
    key: str
    label: str
    prompt: str
    reference: str
    options: tuple[Option, ...]
    # The step appears only when this holds.
    when: Condition = ()
    wording: dict[str, dict[str, str]] = field(default_factory=dict)
    # FR-036: one sentence saying which later choice this step's answer decides, if any.
    decides: str = ''
    # FR-044: several options may be chosen together (except an `exclusive` one).
    multi: bool = False

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
    wording: dict[str, dict[str, str]] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Phase:
    """A fixed stage of the wizard (FR-042): the progress counter counts these, not steps."""

    label: str
    groups: tuple[str, ...]


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
    default_name: str = ''
    # Named wordings, in priority order: the first whose condition holds is used.
    wordings: tuple[tuple[str, Condition], ...] = ()
    phases: tuple[Phase, ...] = ()
    # Feature 228 (FR-002): renamed link keys, old -> current (data/legacy.yaml).
    legacy_steps: dict[str, str] = field(default_factory=dict)
    legacy_options: dict[str, dict[str, str]] = field(default_factory=dict)

    def phase_number(self, group_key: str) -> int:
        """1-based phase of a group."""
        return next(i for i, p in enumerate(self.phases, 1) if group_key in p.groups)

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


def _squash(value: object) -> str:
    return ' '.join(str(value).split())


def _wording(raw: Mapping[str, Any], allowed: set[str]) -> dict[str, dict[str, str]]:
    wording: dict[str, dict[str, str]] = {}
    for name, fields in raw.get('wording', {}).items():
        texts = {str(k): _squash(v) for k, v in fields.items()}
        if set(texts) - allowed:
            raise CatalogError(
                f'wording may only replace {sorted(allowed)}, not {sorted(set(texts) - allowed)}'
            )
        wording[str(name)] = texts
    return wording


def _condition(raw: Mapping[str, Any] | None) -> Condition:
    clauses = []
    for key, value in (raw or {}).items():
        if isinstance(value, Mapping):
            clauses.append(Clause(str(key), frozenset(str(v) for v in value['not']), negate=True))
        else:
            clauses.append(Clause(str(key), frozenset(str(v) for v in value)))
    return tuple(clauses)


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
        text=_squash(raw['text']),
        ja=str(raw.get('ja', '')),
        romaji=str(raw.get('romaji', '')),
        appeal=_squash(raw.get('appeal', '')),
        lines=tuple(_line(x) for x in raw.get('lines', ())),
        wording=_wording(raw, {'label', 'text', 'appeal'}),
        when=_condition(raw.get('when')),
        units=float(raw.get('units', 1)),
        gloss=_squash(raw.get('gloss', '')),
        exclusive=bool(raw.get('exclusive', False)),
        look=_squash(raw.get('look', '')),
    )


def _category(raw: Mapping[str, Any]) -> Category:
    return Category(
        key=str(raw['key']),
        label=str(raw['label']),
        prompt=str(raw['prompt']),
        reference=str(raw['reference']),
        options=tuple(_option(x) for x in raw['options']),
        when=_condition(raw.get('when')),
        wording=_wording(raw, {'label', 'prompt'}),
        decides=_squash(raw.get('decides', '')),
        multi=bool(raw.get('multi', False)),
    )


def parse_catalog(data: Mapping[str, Any]) -> Catalog:
    """Build a Catalog from the merged raw data and check that it hangs together."""
    catalog = Catalog(
        groups=tuple(
            Group(
                key=str(g['key']),
                label=str(g['label']),
                intro=_squash(g['intro']),
                categories=tuple(_category(c) for c in g['categories']),
                wording=_wording(g, {'label', 'intro'}),
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
        default_name=str(data.get('default_name', '')),
        wordings=tuple((str(w['name']), _condition(w['when'])) for w in data.get('wordings', ())),
        phases=tuple(
            Phase(str(p['label']), tuple(str(g) for g in p['groups'])) for p in data['phases']
        ),
        legacy_steps={str(k): str(v) for k, v in (data.get('legacy_steps') or {}).items()},
        legacy_options={
            str(step): {str(k): str(v) for k, v in renames.items()}
            for step, renames in (data.get('legacy_options') or {}).items()
        },
    )
    _validate(catalog)
    return catalog


def _check_condition(
    catalog: Catalog, where: str, condition: Condition, earlier: list[str]
) -> None:
    """Every clause must name a category that comes EARLIER (one forward pass, no oscillation)
    and options that exist."""
    for clause in condition:
        target = catalog.category(clause.key)
        if target is None or clause.key not in earlier:
            raise CatalogError(f'{where}: when names {clause.key!r}, which is not an earlier step')
        missing = [o for o in clause.options if target.option(o) is None]
        if missing:
            raise CatalogError(f'{where}: when names unknown option(s) {sorted(missing)}')


def _validate(catalog: Catalog) -> None:
    contracts = {c.key for c in catalog.contracts}
    keys = [c.key for c in catalog.categories]
    if len(keys) != len(set(keys)):
        raise CatalogError('duplicate category key')
    prefixes = (GM_PREFIX, OTHER_PREFIX, INSTEAD_PREFIX)
    if any(k.startswith(prefixes) for k in keys) or set(keys) & set(TEXT_FIELDS):
        raise CatalogError('a category key collides with a text field or a reserved prefix')
    for old, new in catalog.legacy_steps.items():
        if new not in keys or old in keys:
            raise CatalogError(
                f'legacy step {old!r} -> {new!r}: must map a gone key to a current one'
            )
    for step, renames in catalog.legacy_options.items():
        target = catalog.category(step)
        if target is None:
            raise CatalogError(f'legacy options for unknown step {step!r}')
        for old, new in renames.items():
            if target.option(new) is None or target.option(old) is not None:
                raise CatalogError(
                    f'legacy option {step}.{old} -> {new}: must map a gone key to a current one'
                )
    in_order = [g for p in catalog.phases for g in p.groups]
    if in_order != [g.key for g in catalog.groups]:
        raise CatalogError('phases must list every group exactly once, in wizard order')
    if 'porterage' not in contracts:
        raise CatalogError('the catalog needs a porterage contract for heavy lines')
    if catalog.default_remoteness not in {r.key for r in catalog.remoteness}:
        raise CatalogError(f'unknown default remoteness {catalog.default_remoteness!r}')
    names = {name for name, _ in catalog.wordings}
    for name, condition in catalog.wordings:
        _check_condition(catalog, f'wording {name}', condition, keys)
    owners: list[Any] = [*catalog.groups, *catalog.categories]
    owners += [o for c in catalog.categories for o in c.options]
    for owner in owners:
        unknown = set(owner.wording) - names
        if unknown:
            raise CatalogError(f'{owner.key}: unknown wording {sorted(unknown)}')
    for site in catalog.site_lines:
        if site.contract not in contracts:
            raise CatalogError(f'site line uses unknown contract {site.contract!r}')
    for index, category in enumerate(catalog.categories):
        earlier = keys[:index]
        _check_condition(catalog, category.key, category.when, earlier)
        if category.option(category.reference) is None:
            raise CatalogError(f'{category.key}: {category.reference!r} is not one of its options')
        if category.multi and any(
            cl.key == category.key
            for c in catalog.categories
            for cl in (*c.when, *(x for o in c.options for x in o.when))
        ):
            raise CatalogError(f'{category.key}: a multi-select step cannot be named in a rule')
        for option in category.options:
            where = f'{category.key}.{option.key}'
            if option.exclusive and not category.multi:
                raise CatalogError(f'{where}: exclusive only makes sense on a multi-select step')
            if (option.ja or option.romaji) and not option.gloss:
                raise CatalogError(f'{where}: a Japanese term needs a gloss (FR-043)')
            _check_condition(catalog, where, option.when, earlier)
            for line in option.lines:
                if line.contract not in contracts:
                    raise CatalogError(f'{where}: unknown contract')
                if line.per is not None and line.per not in earlier:
                    raise CatalogError(f'{where}: per names {line.per!r}, not an earlier step')


def _read(path: Path) -> Any:
    with path.open(encoding='utf-8') as fh:
        return yaml.safe_load(fh)


def _merge_looks(groups: list[dict[str, Any]], looks: Mapping[str, Mapping[str, str]]) -> None:
    """Give every option its `look` from looks.yaml; a missing or stray entry is an error, so a new
    option cannot reach the image prompt silently blank (feature 228)."""
    seen = set()
    for group in groups:
        for category in group['categories']:
            for option in category['options']:
                where = f'{category["key"]}.{option["key"]}'
                entry = looks.get(category['key'], {})
                if option['key'] not in entry:
                    raise CatalogError(f'{where}: no look in data/looks.yaml')
                option['look'] = entry[option['key']]
                seen.add(where)
    stray = {f'{c}.{o}' for c, entry in looks.items() for o in entry} - seen
    if stray:
        raise CatalogError(f'data/looks.yaml names unknown options {sorted(stray)}')


def load_raw(data_dir: Path = DATA_DIR) -> dict[str, Any]:
    """`catalog.yaml` with its `groups` list of keys replaced by the group files' contents, each
    option's `look` merged from `looks.yaml`, and the renamed keys from `legacy.yaml`."""
    raw: dict[str, Any] = _read(data_dir / 'catalog.yaml')
    raw['groups'] = [_read(data_dir / 'groups' / f'{key}.yaml') for key in raw['groups']]
    _merge_looks(raw['groups'], _read(data_dir / 'looks.yaml'))
    legacy = _read(data_dir / 'legacy.yaml') or {}
    raw['legacy_steps'] = legacy.get('steps') or {}
    raw['legacy_options'] = legacy.get('options') or {}
    return raw


def load_catalog(data_dir: Path = DATA_DIR) -> Catalog:
    return parse_catalog(load_raw(data_dir))
