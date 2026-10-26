"""The price ledger: what things cost in Rokugan, every figure with a label and a source.

One JSON object per line of `data/ledger.jsonl`:

    {"item": ..., "low": sen, "high": sen, "per": "year", "label": "estimated",
     "source": "lead:...", "notes": ..., "tags": [...]}

- `low`/`high` are whole sen (1 koku = 1,000 sen); equal for a point figure.
- `per` is what the figure buys: "item", "day", "year", "month", "night", ...
- `label`: `historical` (shown "Researched": the record prices this good itself, possibly in a
  nearby place or period), `extrapolated` (no price for this exact item, but a researched price for
  a close relative carried over by a stated rule: a unit conversion, a ratio the research gives,
  scaling by size or distance, the same good in China; it must cite that research), `estimated`
  (built from the model - materials, labor-days, neighboring goods - with no researched price of
  its own kind), `deviation` (the setting departs from history on purpose, and says so). The GM
  split the old `guess` into the middle two (feature 227): even a true guess here is reasoned, and
  a carried-over research price is a different thing. A canon figure nobody has checked against
  history is `estimated` with a `canon:` source; research moves it to `historical` or, if the GM
  keeps it against the history, `deviation`. `comparative` (GM ruling,
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
  binds them. An answer never comes straight from a source row (spec 219 FR-011).

SWINGS (`data/swings.jsonl`, GM 2026-10-24, from diagram#15): one line a class of good, saying
whether its real-world price was steady, swung or (a wage) sticky across days, years, places and
periods, and why (salt: the state monopoly). A row takes the FIRST class sharing one of its tags,
so a specific class (salt, rice) is listed before the general one (food) its rows also carry. The
Rokugani range stays narrow on purpose; the note says how far history strayed from one number."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from l7r.money.readings import DATA

__all__ = [
    'LABELS',
    'LEDGER',
    'SWINGS',
    'Row',
    'Swing',
    'load',
    'load_swings',
    'problems',
    'search',
    'swing_for',
]

LABELS = ('historical', 'deviation', 'extrapolated', 'estimated', 'comparative')
# What an extrapolated row carries over: a research question as its source, or named in its notes.
_CITES_RESEARCH = re.compile(r'/research/questions/|\b0\d{3}\b')
LEDGER = DATA / 'ledger.jsonl'
SWINGS = DATA / 'swings.jsonl'
VERDICTS = ('steady', 'swung', 'sticky')
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
    if raw.get('label') == 'extrapolated' and not _CITES_RESEARCH.search(
        f'{raw.get("source", "")} {raw.get("notes", "")}'
    ):
        out.append(
            'an extrapolated row must cite the research it carries over: a diagram question as its '
            "source, or its number in the notes (e.g. '0279'); with no research of its kind it is "
            'estimated'
        )
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


@dataclass(frozen=True, slots=True)
class Swing:
    """How steady one class of good's real-world price was, and why (see the module docstring)."""

    cls: str
    tags: tuple[str, ...]
    verdict: str
    note: str
    source: str


def load_swings(path: Path = SWINGS) -> list[Swing]:
    swings: list[Swing] = []
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        raw = json.loads(line)
        if raw.keys() != {'class', 'tags', 'verdict', 'note', 'source'}:
            raise ValueError(f'{path.name} line {number}: needs class, tags, verdict, note, source')
        if (
            raw['verdict'] not in VERDICTS
            or not raw['tags']
            or not raw['source'].startswith(DIAGRAM)
        ):
            raise ValueError(
                f'{path.name} line {number}: verdict one of {", ".join(VERDICTS)}, '
                'at least one tag, and a diagram question as its source'
            )
        swings.append(
            Swing(raw['class'], tuple(raw['tags']), raw['verdict'], raw['note'], raw['source'])
        )
    return swings


def swing_for(row: Row, swings: list[Swing]) -> Swing | None:
    """The first class sharing one of the row's tags, or None (no class: nothing is claimed)."""
    return next((s for s in swings if set(s.tags) & set(row.tags)), None)
