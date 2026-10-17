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
    'enables',
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


def enables(catalog: Catalog, category: Category, option: Option) -> tuple[str, ...]:
    """Labels of later OPTIONS offered only if this option is chosen (FR-036), derived from the
    rules so a card's note cannot drift from what the wizard does."""
    return tuple(
        o.label
        for c in catalog.categories
        for o in c.options
        if any(
            cl.key == category.key and not cl.negate and option.key in cl.options for cl in o.when
        )
    )


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
