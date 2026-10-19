"""The price ledger: what things cost in Rokugan, every figure with a label and a source.

One JSON object per line of `data/ledger.jsonl`:

    {"item": ..., "low": sen, "high": sen, "per": "year", "label": "guess",
     "source": "lead:...", "notes": ..., "tags": [...]}

- `low`/`high` are whole sen (1 koku = 1,000 sen); equal for a point figure.
- `per` is what the figure buys: "item", "day", "year", "month", "night", ...
- `label` (the handoff's three): `historical` (history attests it), `deviation` (the setting
  departs from history on purpose, and says so), `guess` (reasoned, not attested). A canon figure
  nobody has checked against history is a `guess` with a `canon:` source; research moves it to
  `historical` or, if the GM keeps it against the history, `deviation`. `comparative` (GM ruling,
  diagram feature 391): a figure from another society (Regency England, medieval Lucca) kept as a
  yardstick players recognize. It is never a Rokugani price or wage and never sets the value of a
  koku; output marks it so.
- `source` is one of: an `https://` URL (a diagram question file once researched, or a canon file
  on GitHub), `canon:<file> "<section>"`, `lead:<file in the GM's money folder or notes>`, or
  `derived:<file>#<anchor>` (reasoned from other rows, the derivation written there; FR-012). A
  `historical` row whose source is still a lead is UNVERIFIED until a diagram question file
  replaces it.
- `id` marks a SYNTHESIS row: what the skill answers with, bound by every consistency rule
  (`rules.py`) that names it. A row without an `id` is a SOURCE row: what one source says, as
  found; source rows may disagree with each other (place, period, debased coin, unit) and no rule
  binds them. An answer never comes straight from a source row (spec 219 FR-011)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from l7r.money.readings import DATA

__all__ = ['LABELS', 'LEDGER', 'Row', 'load', 'problems', 'search']

LABELS = ('historical', 'deviation', 'guess', 'comparative')
LEDGER = DATA / 'ledger.jsonl'
DIAGRAM = 'https://github.com/EliAndrewC/diagram/'
_SOURCE_PREFIXES = ('https://', 'canon:', 'lead:', 'derived:')
_FIELDS = {'id', 'item', 'low', 'high', 'per', 'label', 'source', 'notes', 'tags'}


@dataclass(frozen=True, slots=True)
class Row:
    item: str
    low: int
    high: int
    per: str
    label: str
    source: str
    notes: str = ''
    tags: tuple[str, ...] = field(default=())
    id: str = ''

    @property
    def verified(self) -> bool:
        """Rests on a diagram question file or the canon, not a lead or a derivation."""
        return not self.source.startswith(('lead:', 'derived:'))

    @property
    def researched(self) -> bool:
        return self.source.startswith(DIAGRAM)


def problems(raw: dict[str, object]) -> list[str]:
    """Why a ledger line is not acceptable (empty when it is)."""
    out = []
    missing = {'item', 'low', 'high', 'per', 'label', 'source'} - raw.keys()
    if missing:
        out.append(f'missing {", ".join(sorted(missing))}')
    if extra := raw.keys() - _FIELDS:
        out.append(f'unknown {", ".join(sorted(extra))}')
    low, high = raw.get('low'), raw.get('high')
    if not (isinstance(low, int) and isinstance(high, int) and 0 <= low <= high):
        out.append('low/high must be whole sen with 0 <= low <= high')
    if raw.get('label') not in LABELS:
        out.append(f'label must be one of {", ".join(LABELS)}')
    source = raw.get('source')
    if not (isinstance(source, str) and source.startswith(_SOURCE_PREFIXES) and len(source) > 6):
        out.append('source must be an https:// URL, canon:..., lead:... or derived:...')
    if not str(raw.get('item', '')).strip() or not str(raw.get('per', '')).strip():
        out.append('item and per must be non-empty')
    return out


def load(path: Path = LEDGER) -> list[Row]:
    rows: list[Row] = []
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        raw = json.loads(line)
        if found := problems(raw):
            raise ValueError(f'{path.name} line {number}: {"; ".join(found)}')
        row = Row(**{**raw, 'tags': tuple(raw.get('tags', ()))})
        if row.id and any(r.id == row.id for r in rows):
            raise ValueError(f'{path.name} line {number}: duplicate id {row.id!r}')
        rows.append(row)
    return rows


def search(rows: list[Row], words: list[str]) -> list[Row]:
    """Rows whose item, notes or tags contain every word (case-insensitive)."""
    wanted = [w.lower() for w in words]
    return [
        r
        for r in rows
        if all(w in f'{r.item} {r.notes} {" ".join(r.tags)}'.lower() for w in wanted)
    ]
