"""The player's design: read from a link, resolved against the rules, and written back to a link.

Resolution is ONE forward pass over the categories in wizard order (`resolve`): a step is in play
if its `when` holds against the choices already resolved; a chosen option is kept if its own
`when` holds. The catalog guarantees every clause looks backward, so nothing later can change an
earlier decision. `static/js/shrines.js` runs the same algorithm over the same rules, which reach
the browser as JSON (`rules_json`) - conditions only, never a price.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from urllib.parse import urlencode

from l7r.shrines.catalog import TEXT_FIELDS, Catalog, Category, Clause, Option, holds_all

__all__ = [
    'Design',
    'Effect',
    'option_effects',
    'first',
    'picks',
    'moot_note',
    'option_offered',
    'parse_design',
    'reference_design',
    'rules_json',
    'share_query',
]


def picks(value: object) -> list[str]:
    """Every string value of a query key (a multi-select step repeats its key)."""
    values = value if isinstance(value, list) else [value]
    return [v for v in values if isinstance(v, str)]


def first(value: object) -> str | None:
    """CherryPy hands a repeated query key over as a list; take its first value."""
    if isinstance(value, list):
        value = value[0] if value else None
    return value if isinstance(value, str) else None


@dataclass(frozen=True, slots=True)
class Design:
    """The player's selections, resolved. `choices` holds only steps in play with real picks."""

    choices: dict[str, str]
    # FR-044: multi-select steps, each with the options picked (an exclusive one stands alone).
    multi: dict[str, tuple[str, ...]]
    # Steps not in play, each with the first clause of its `when` that failed.
    inactive: dict[str, Clause]
    text: dict[str, str]
    dropped: tuple[str, ...] = ()
    # The named wording in force ('' = the plain wording), FR-030/FR-032/FR-037.
    wording: str = ''

    @property
    def voided(self) -> frozenset[str]:
        return frozenset(self.inactive)


def _resolve_multi(
    catalog: Catalog,
    picked: Mapping[str, list[str]],
    choices: Mapping[str, str],
    inactive: Mapping[str, Clause],
) -> dict[str, tuple[str, ...]]:
    """Multi-select steps (never named in a rule, so they can be settled after the single ones):
    keep options that exist and are offered; an exclusive pick stands alone."""
    multi: dict[str, tuple[str, ...]] = {}
    for category in catalog.categories:
        if not category.multi or category.key in inactive:
            continue
        options = [category.option(v) for v in picked.get(category.key, [])]
        kept = [o for o in options if o is not None and holds_all(o.when, choices)]
        exclusive = [o for o in kept if o.exclusive]
        kept = exclusive[:1] if exclusive else kept
        ordered = tuple(o.key for o in category.options if o in kept)
        if ordered:
            multi[category.key] = ordered
    return multi


def _resolve(
    catalog: Catalog, chosen: Mapping[str, str]
) -> tuple[dict[str, str], dict[str, Clause]]:
    choices: dict[str, str] = {}
    inactive: dict[str, Clause] = {}
    for category in catalog.categories:
        failing = next((c for c in category.when if not c.holds(choices)), None)
        if failing is not None:
            inactive[category.key] = failing
            continue
        picked = chosen.get(category.key)
        option = None if category.multi or picked is None else category.option(picked)
        # An option that needs an earlier choice it does not have is not chosen (FR-036):
        # changing the earlier step quietly takes it back.
        if option is not None and holds_all(option.when, choices):
            choices[category.key] = option.key
    return choices, inactive


def parse_design(catalog: Catalog, params: Mapping[str, object]) -> Design:
    """Read a design from query parameters. Nothing is pre-selected (an option picked on arrival
    biases the player - GM 2026-10-17), so a step not reached yet is absent and costs nothing.

    `dropped` names steps whose value was present but is not a current option (an old or
    hand-edited link), so the page can say a choice could not be restored.
    """
    chosen: dict[str, str] = {}
    picked: dict[str, list[str]] = {}
    dropped: list[str] = []
    for category in catalog.categories:
        if category.multi:
            values = picks(params.get(category.key))
            picked[category.key] = values
            if any(category.option(v) is None for v in values):
                dropped.append(category.key)
            continue
        raw = first(params.get(category.key))
        if raw is not None and category.option(raw) is not None:
            chosen[category.key] = raw
        elif raw is not None:
            dropped.append(category.key)
    choices, inactive = _resolve(catalog, chosen)
    multi = _resolve_multi(catalog, picked, choices, inactive)
    text = {}
    for name, cap in TEXT_FIELDS.items():
        raw = first(params.get(name))
        if raw is not None and raw.strip():
            text[name] = ' '.join(raw.split())[:cap]  # one line: the name box wraps, never breaks
    # A blank or missing name falls back to the catalog's, so the field is never empty.
    if 'shrine_name' not in text and catalog.default_name:
        text['shrine_name'] = catalog.default_name
    return Design(
        choices=choices,
        multi=multi,
        inactive=inactive,
        text=text,
        dropped=tuple(d for d in dropped if d not in inactive),
        wording=next((n for n, cond in catalog.wordings if holds_all(cond, choices)), ''),
    )


def option_offered(option: Option, design: Design) -> bool:
    return holds_all(option.when, design.choices)


def moot_note(catalog: Catalog, category: Category) -> str:
    """Why a step may not apply, from its rule: 'Only for "Open to the sky" (Form).'"""
    parts = []
    for clause in category.when:
        target = catalog.category(clause.key)
        assert target is not None  # the catalog validated every clause
        labels = ' or '.join(f'"{o.label}"' for o in target.options if o.key in clause.options)
        parts.append(f'{"not with" if clause.negate else "only for"} {labels} ({target.label})')
    note = '; '.join(parts)
    return note[:1].upper() + note[1:] + '.' if note else ''


@dataclass(frozen=True, slots=True)
class Effect:
    """What picking one option makes possible later, given the choices so far (FR-040)."""

    # steps that only appear if this option is picked, and later options only then offered
    added: tuple[str, ...] = ()
    opens: tuple[str, ...] = ()

    @property
    def tag(self) -> str:
        """The label above the card (FR-041): the choices that exist because of this option -
        '5 custom choices' for the steps it brings or, when it brings no step, the later options it
        makes possible, counted the same way. No tag on an option that makes nothing possible."""
        n = len(self.added) or len(self.opens)
        return f'{n} custom choice{"s" if n != 1 else ""}' if n else ''


def _offered(
    catalog: Catalog, choices: Mapping[str, str], inactive: Mapping[str, Clause]
) -> set[str]:
    return {
        f'{c.key}.{o.key}'
        for c in catalog.categories
        if c.key not in inactive
        for o in c.options
        if o.when and holds_all(o.when, choices)
    }


def option_effects(catalog: Catalog, design: Design, category: Category) -> dict[str, Effect]:
    """Simulate picking each option of `category` against the current choices, and compare with
    leaving it unanswered: which steps appear or disappear, which later options open. Derived from
    the rules, so a card's tag cannot drift from what the wizard does. shrines.js does the same."""
    w = design.wording
    if category.multi:
        return {}  # a multi-select step is never named in a rule, so it makes nothing possible
    labels = {c.key: c.wording.get(w, {}).get('label', c.label) for c in catalog.categories}
    option_labels = {
        f'{c.key}.{o.key}': o.wording.get(w, {}).get('label', o.label)
        for c in catalog.categories
        for o in c.options
    }
    base_raw = {k: v for k, v in design.choices.items() if k != category.key}
    base_choices, base_inactive = _resolve(catalog, base_raw)
    base_offered = _offered(catalog, base_choices, base_inactive)
    effects = {}
    for option in category.options:
        choices, inactive = _resolve(catalog, {**base_raw, category.key: option.key})
        offered = _offered(catalog, choices, inactive)
        effects[option.key] = Effect(
            added=tuple(labels[k] for k in labels if k in base_inactive and k not in inactive),
            # options inside steps that only now appear come with those steps; count the rest
            opens=tuple(
                option_labels[k]
                for k in option_labels
                if k in offered - base_offered and k.split('.')[0] not in base_inactive
            ),
        )
    return effects


def _clauses(condition: tuple[Clause, ...]) -> list[list[object]]:
    return [[c.key, sorted(c.options), c.negate] for c in condition]


def rules_json(catalog: Catalog) -> str:
    """The rules for shrines.js: conditions only (no labels, no lines, no prices), safe to inline
    in a <script type="application/json">."""
    rules = {
        'categories': {c.key: _clauses(c.when) for c in catalog.categories if c.when},
        'options': {
            c.key: {o.key: _clauses(o.when) for o in c.options if o.when}
            for c in catalog.categories
            if any(o.when for o in c.options)
        },
        'wordings': [[name, _clauses(cond)] for name, cond in catalog.wordings],
    }
    return json.dumps(rules, separators=(',', ':')).replace('</', '<\\/')


def share_query(catalog: Catalog, design: Design) -> str:
    """The query string that reproduces `design` and nothing else - never a GM figure."""
    pairs = []
    for c in catalog.categories:
        if c.key in design.choices:
            pairs.append((c.key, design.choices[c.key]))
        pairs += [(c.key, v) for v in design.multi.get(c.key, ())]
    pairs += [(name, design.text[name]) for name in TEXT_FIELDS if name in design.text]
    return urlencode(pairs)


def reference_design(catalog: Catalog) -> Design:
    """The "fairly nice small forest shrine" the default budget is priced from."""
    return parse_design(catalog, {c.key: c.reference for c in catalog.categories})
