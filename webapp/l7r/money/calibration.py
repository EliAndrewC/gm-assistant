"""The estimate log and how well calibrated the price model is (feature 220).

The GM (2026-10-18): estimate a price never priced before, log the guess, research it later, and
*"keep track of how in line with our research our estimates were, because that tells us how well
calibrated our model is"*. Three append-only files in `data/`:

- `estimates.jsonl` - one guess per line: id (E0001...), date, item, the GM's question, low/high in
  sen, per, category, method, the ledger rows it used, and the model inputs in force (basket
  snapshot, koku mass, wage, laborer's year). NEVER edited once committed: `rewritten()` and its
  test compare against git HEAD, so the log of guesses cannot be quietly improved after the
  research arrives.
- `requests.jsonl` - estimate id -> the diagram issue that asks for its research. Separate so
  filing an issue never touches the guess.
- `withdrawn.jsonl` - estimates that should never be graded, with the reason: an entry logged by
  mistake (e.g. figures that did not come from this model). The estimate line itself stays.
- `findings.jsonl` - what the research showed for an estimate: low/high in the estimate's unit, the
  diagram question file, the verdict. Only ATTESTED and ATTESTED ONLY FOR count as measurements;
  NOT ATTESTED and SILENT are recorded but grade nothing. A comparative source (spec 219 FR-014)
  can never be a finding: it cannot set a Rokugani price, so it cannot grade one.

THE MEASURES. Prices run from a sen to thousands of koku, so misses are compared as RATIOS of range
midpoints (estimate / finding), never as differences, and averaged in log space:

- bias = geometric mean of the ratios: 1.5 means we guess 1.5x too high, 0.67 means 1.5x too low.
- spread = median of |log ratio|, as a factor: 2.0 means a typical miss is a factor of two either
  way.
- hit rate = how often the finding's midpoint fell inside the estimate's range.

Declined: arithmetic means of sen differences - one koku-scale item would swamp every apple and
arrow.
"""

from __future__ import annotations

import json
import math
import re
import statistics
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from pathlib import Path

from l7r.money.readings import DATA

__all__ = [
    'CATEGORIES',
    'COUNTED',
    'ESTIMATES',
    'FINDINGS',
    'REQUESTS',
    'VERDICTS',
    'WITHDRAWN',
    'Estimate',
    'Finding',
    'Grade',
    'Link',
    'Withdrawal',
    'append',
    'grade',
    'load_estimates',
    'load_findings',
    'load_links',
    'load_withdrawn',
    'next_id',
    'rewritten',
]

ESTIMATES = DATA / 'estimates.jsonl'
REQUESTS = DATA / 'requests.jsonl'
FINDINGS = DATA / 'findings.jsonl'
WITHDRAWN = DATA / 'withdrawn.jsonl'

CATEGORIES = (
    'wages',
    'lodging',
    'transport',
    'weapons',
    'paper',
    'food',
    'offerings',
    'rentals',
    'clothing',
    'drink',
    'entertainment',
    'construction',
    'tools',
    'other',
)
COUNTED = ('ATTESTED', 'ATTESTED ONLY FOR')
VERDICTS = (*COUNTED, 'NOT ATTESTED', 'SILENT')
_ID = re.compile(r'E\d{4}$')


@dataclass(frozen=True, slots=True)
class Estimate:
    id: str
    date: str
    item: str
    question: str
    low: int
    high: int
    per: str
    category: str
    method: str
    rows: tuple[str, ...] = field(default=())
    model: dict[str, str] = field(default_factory=dict)

    @property
    def mid(self) -> float:
        return (self.low + self.high) / 2


@dataclass(frozen=True, slots=True)
class Link:
    estimate: str
    issue: str
    date: str


@dataclass(frozen=True, slots=True)
class Withdrawal:
    """An estimate that should not be graded (it was not a pre-research estimate of this model)."""

    estimate: str
    date: str
    reason: str


@dataclass(frozen=True, slots=True)
class Finding:
    estimate: str
    date: str
    low: int
    high: int
    source: str
    verdict: str
    notes: str = ''

    @property
    def mid(self) -> float:
        return (self.low + self.high) / 2

    @property
    def counts(self) -> bool:
        return self.verdict in COUNTED


def _lines(path: Path) -> Iterable[tuple[int, dict[str, object]]]:
    if not path.exists():
        return
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if line.strip():
            yield number, json.loads(line)


def _range_ok(raw: dict[str, object]) -> bool:
    low, high = raw.get('low'), raw.get('high')
    return isinstance(low, int) and isinstance(high, int) and 0 <= low <= high


def load_estimates(path: Path | None = None) -> list[Estimate]:
    path = path or ESTIMATES  # looked up at call time, so tests can point it elsewhere
    out: list[Estimate] = []
    for number, raw in _lines(path):
        where = f'{path.name} line {number}'
        if not _ID.match(str(raw.get('id', ''))):
            raise ValueError(f'{where}: id must look like E0001')
        if any(e.id == raw['id'] for e in out):
            raise ValueError(f'{where}: duplicate id {raw["id"]}')
        if not _range_ok(raw):
            raise ValueError(f'{where}: low/high must be whole sen with 0 <= low <= high')
        if raw.get('category') not in CATEGORIES:
            raise ValueError(f'{where}: category must be one of {", ".join(CATEGORIES)}')
        if not str(raw.get('method', '')).strip() or not str(raw.get('question', '')).strip():
            raise ValueError(f'{where}: question and method must be non-empty')
        rows, model = raw.get('rows') or [], raw.get('model') or {}
        if not isinstance(rows, list) or not isinstance(model, dict):
            raise ValueError(f'{where}: rows must be a list and model an object')
        clean = {
            **raw,
            'rows': tuple(str(r) for r in rows),
            'model': {str(k): str(v) for k, v in model.items()},
        }
        out.append(Estimate(**clean))  # type: ignore[arg-type]
    return out


def load_links(estimates: list[Estimate], path: Path | None = None) -> list[Link]:
    path = path or REQUESTS
    ids = {e.id for e in estimates}
    out = []
    for number, raw in _lines(path):
        if raw.get('estimate') not in ids:
            raise ValueError(f'{path.name} line {number}: no estimate {raw.get("estimate")}')
        if not str(raw.get('issue', '')).startswith(
            'https://github.com/EliAndrewC/diagram/issues/'
        ):
            raise ValueError(f'{path.name} line {number}: issue must be a diagram issue URL')
        out.append(Link(str(raw['estimate']), str(raw['issue']), str(raw['date'])))
    return out


def load_findings(estimates: list[Estimate], path: Path | None = None) -> list[Finding]:
    path = path or FINDINGS
    ids = {e.id for e in estimates}
    out = []
    for number, raw in _lines(path):
        where = f'{path.name} line {number}'
        if raw.get('estimate') not in ids:
            raise ValueError(f'{where}: no estimate {raw.get("estimate")}')
        if raw.get('verdict') not in VERDICTS:
            raise ValueError(f'{where}: verdict must be one of {", ".join(VERDICTS)}')
        if raw.pop('comparative', False):
            raise ValueError(f'{where}: a comparative source cannot grade a Rokugani estimate')
        if not str(raw.get('source', '')).startswith('https://'):
            raise ValueError(f'{where}: source must be the diagram question file URL')
        if not _range_ok(raw):
            raise ValueError(f'{where}: low/high must be whole sen with 0 <= low <= high')
        out.append(Finding(**raw))  # type: ignore[arg-type]
    return out


def load_withdrawn(estimates: list[Estimate], path: Path | None = None) -> list[Withdrawal]:
    path = path or WITHDRAWN
    ids = {e.id for e in estimates}
    out = []
    for number, raw in _lines(path):
        if raw.get('estimate') not in ids:
            raise ValueError(f'{path.name} line {number}: no estimate {raw.get("estimate")}')
        if not str(raw.get('reason', '')).strip():
            raise ValueError(f'{path.name} line {number}: a withdrawal needs a reason')
        out.append(Withdrawal(str(raw['estimate']), str(raw['date']), str(raw['reason'])))
    return out


def next_id(estimates: list[Estimate]) -> str:
    return f'E{max((int(e.id[1:]) for e in estimates), default=0) + 1:04d}'


def append(path: Path, record: Estimate | Link | Finding | Withdrawal) -> None:
    raw = asdict(record)
    raw.pop('mid', None)
    with path.open('a') as f:
        f.write(json.dumps(raw) + '\n')


def rewritten(committed: str, current: str) -> list[str]:
    """Committed estimate lines that the current file changed or dropped (it may only grow)."""
    old = [line for line in committed.splitlines() if line.strip()]
    new = [line for line in current.splitlines() if line.strip()]
    return [
        f'line {n}: {line[:60]}'
        for n, line in enumerate(old, 1)
        if n > len(new) or new[n - 1] != line
    ]


@dataclass(frozen=True, slots=True)
class Grade:
    group: str
    n: int
    bias: float
    spread: float
    hit_rate: float


def _grade(group: str, pairs: list[tuple[Estimate, Finding]]) -> Grade:
    logs = [math.log(e.mid / f.mid) for e, f in pairs]
    hits = sum(e.low <= f.mid <= e.high for e, f in pairs)
    return Grade(
        group,
        len(pairs),
        math.exp(statistics.fmean(logs)),
        math.exp(statistics.median(abs(x) for x in logs)),
        hits / len(pairs),
    )


def grade(
    estimates: list[Estimate], findings: list[Finding], withdrawn: Iterable[str] = ()
) -> list[Grade]:
    """Per category, then 'all'. The latest counted finding grades an estimate."""
    latest: dict[str, Finding] = {}
    for f in sorted(findings, key=lambda f: f.date):
        if f.counts:
            latest[f.estimate] = f
    gone = set(withdrawn)
    estimates = [e for e in estimates if e.id not in gone]
    pairs = [
        (e, latest[e.id])
        for e in estimates
        if e.id in latest and e.mid > 0 and latest[e.id].mid > 0
    ]
    out = [
        _grade(cat, [p for p in pairs if p[0].category == cat])
        for cat in CATEGORIES
        if any(p[0].category == cat for p in pairs)
    ]
    if pairs:
        out.append(_grade('all', pairs))
    return out
