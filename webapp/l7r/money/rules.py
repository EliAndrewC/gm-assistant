"""Consistency rules between ledger rows: the GM's "these things should make sense relative to each
other".

The GM's example (2026-10-18): a kimono must not cost less than the undyed silk it is made from.
One JSON object per line of `data/rules.jsonl`:

    {"rule": "a plain cotton kimono costs at least its cloth", "row": "kimono-cotton",
     "at_least": [["cloth-cotton-kimono-length", 1]], "why": "..."}

The rule holds when the row's LOW figure is at least the sum of multiplier x LOW of the rows it
names: the cheapest kimono must cover the cheapest cloth. (Comparing lows is deliberate - the
dearest kimono need not use the dearest cloth.) `check` and the gate fail on a broken rule. When
two sources genuinely disagree (place, period, a debased coin, a different koku), widen the rows'
ranges or note the reason; never delete a rule to make the check pass."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from l7r.money.ledger import Row
from l7r.money.readings import DATA

__all__ = ['RULES', 'Rule', 'load_rules', 'violations']

RULES = DATA / 'rules.jsonl'


@dataclass(frozen=True, slots=True)
class Rule:
    rule: str
    row: str
    at_least: tuple[tuple[str, float], ...]
    why: str = ''


def load_rules(path: Path = RULES) -> list[Rule]:
    out = []
    for line in path.read_text().splitlines():
        if line.strip():
            raw = json.loads(line)
            terms = tuple((str(i), float(m)) for i, m in raw['at_least'])
            out.append(Rule(raw['rule'], raw['row'], terms, raw.get('why', '')))
    return out


def violations(rules: list[Rule], rows: list[Row]) -> list[str]:
    """One line per broken rule (or rule naming a row id that does not exist)."""
    by_id = {r.id: r for r in rows if r.id}
    out = []
    for rule in rules:
        missing = [i for i in (rule.row, *(i for i, _ in rule.at_least)) if i not in by_id]
        if missing:
            out.append(f'{rule.rule}: no row with id {", ".join(missing)}')
            continue
        floor = sum(m * by_id[i].low for i, m in rule.at_least)
        low = by_id[rule.row].low
        if low < floor:
            out.append(
                f'{rule.rule}: {rule.row} starts at {low} sen, below its floor of {floor:g} sen'
            )
    return out
