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
    'moot_note',
    'option_offered',
    'parse_design',
    'reference_design',
    'rules_json',
    'share_query',
]


def first(value: object) -> str | None:
    """CherryPy hands a repeated query key over as a list; take its first value."""
    if isinstance(value, list):
        value = value[0] if value else None
    return value if isinstance(value, str) else None


@dataclass(frozen=True, slots=True)
class Design:
    """The player's selections, resolved. `choices` holds only steps in play with real picks."""

    choices: dict[str, str]
    # Steps not in play, each with the first clause of its `when` that failed.
    inactive: dict[str, Clause]
    text: dict[str, str]
    dropped: tuple[str, ...] = ()
    # The named wording in force ('' = the plain wording), FR-030/FR-032/FR-037.
    wording: str = ''

    @property
    def voided(self) -> frozenset[str]:
        return frozenset(self.inactive)


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
        option = category.option(picked) if picked is not None else None
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
    dropped: list[str] = []
    for category in catalog.categories:
        raw = first(params.get(category.key))
        if raw is not None and category.option(raw) is not None:
            chosen[category.key] = raw
        elif raw is not None:
            dropped.append(category.key)
    choices, inactive = _resolve(catalog, chosen)
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
    # decision steps still to come after this one if it is picked
    remaining: int = 0

    @property
    def tag(self) -> str:
        """The label above the card - only on an option that makes something possible later:
        how many more steps there will be if it is picked, counted as the wizard's own "Step N of
        M" counts them (the final summary step included): 'If chosen: 17 more steps'."""
        if not (self.added or self.opens):
            return ''
        n = self.remaining + 1
        return f'If chosen: {n} more step{"s" if n != 1 else ""}'


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
    labels = {c.key: c.wording.get(w, {}).get('label', c.label) for c in catalog.categories}
    option_labels = {
        f'{c.key}.{o.key}': o.wording.get(w, {}).get('label', o.label)
        for c in catalog.categories
        for o in c.options
    }
    base_raw = {k: v for k, v in design.choices.items() if k != category.key}
    base_choices, base_inactive = _resolve(catalog, base_raw)
    base_offered = _offered(catalog, base_choices, base_inactive)
    later = [c.key for c in catalog.categories]
    later = later[later.index(category.key) + 1 :]
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
            remaining=sum(1 for k in later if k not in inactive),
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
    pairs = [(c.key, design.choices[c.key]) for c in catalog.categories if c.key in design.choices]
    pairs += [(name, design.text[name]) for name in TEXT_FIELDS if name in design.text]
    return urlencode(pairs)


def reference_design(catalog: Catalog) -> Design:
    """The "fairly nice small forest shrine" the default budget is priced from."""
    return parse_design(catalog, {c.key: c.reference for c in catalog.categories})
