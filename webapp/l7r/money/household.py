"""The household-work page, `/money/household` (feature 231).

The GM (2026-10-26): the work a household did for itself - cloth, food, fuel, straw goods, repairs,
care - relates to money and to the cost of goods even though no money changed hands, so the Money
section shows it: one counted farm year, the tasks and their time, his hypothesis that clothes took
more of one person's time than farming, homemade goods in days of work beside their market price,
what a city household bought instead, and why so much is missing. Women's household work was almost
never written down, and the page says so rather than leaving the gaps unexplained.

`data/household.json` holds every figure with the verdict the research gave it (diagram#21,
questions 0311-0317) and its question file; `load` refuses a figure without either, so nothing on
the page can pass for history without its basis. A homemade good's market price is read from the
ledger at request time, so a re-priced ledger row moves the comparison with it.
"""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from l7r.money.ledger import Row
from l7r.money.readings import DATA, LABORER_DAY_SEN

__all__ = [
    'HOUSEHOLD',
    'VERDICTS',
    'VERDICT_WORDS',
    'Homemade',
    'figures',
    'homemade',
    'load',
    'source_url',
]

HOUSEHOLD = DATA / 'household.json'
RESEARCH = 'https://github.com/EliAndrewC/diagram/blob/main/research/questions/'

# The research's verdicts, and how the page words them for a reader.
VERDICT_WORDS = {
    'ATTESTED': 'Attested',
    'ATTESTED ONLY FOR': 'Attested for one place',
    'ATTESTED ONLY AS AN ESTIMATE': "A historian's estimate",
    'NOT ATTESTED': 'Not borne out',
    'SILENT': 'Not recorded',
}
VERDICTS = tuple(VERDICT_WORDS)


def figures(node: object) -> Iterator[Mapping[str, Any]]:
    """Every figure in the data: any object that carries a verdict."""
    if isinstance(node, Mapping):
        if 'verdict' in node:
            yield node
        for value in node.values():
            yield from figures(value)
    elif isinstance(node, list):
        for value in node:
            yield from figures(value)


def load(path: Path | None = None) -> dict[str, Any]:
    path = path or HOUSEHOLD  # looked up at call time, so tests can point it elsewhere
    data: dict[str, Any] = json.loads(path.read_text())
    sources = data['sources']
    for fig in figures(data):
        name = fig.get('task') or fig.get('label') or fig.get('thing') or fig.get('who') or fig
        if fig['verdict'] not in VERDICTS:
            raise ValueError(f'{name}: verdict must be one of {", ".join(VERDICTS)}')
        if fig.get('source') not in sources:
            raise ValueError(f'{name}: source must be one of {", ".join(sources)}')
    return data


def source_url(data: Mapping[str, Any], key: str) -> str:
    return f'{RESEARCH}{data["sources"][key]}.html'


@dataclass(frozen=True, slots=True)
class Homemade:
    """A homemade good: the days it took, beside what the same thing cost at market."""

    label: str
    days: float
    market_low: float
    market_high: float
    laborer_sen: float
    woman_low: float
    woman_high: float
    scope: str
    verdict: str
    source: str


def homemade(data: Mapping[str, Any], rows: list[Row]) -> list[Homemade]:
    """Each homemade good in sen: its market price (the ledger row times the count), its days at
    the unskilled laborer's day wage, and at a woman day laborer's pay, which the research gives as
    a share of a man's (the Imai accounts, 1821)."""
    by_id = {r.id: r for r in rows if r.id}
    woman = data['woman_day']
    low_share, high_share = woman['low'] / woman['man'], woman['high'] / woman['man']
    out = []
    for good in data['homemade']:
        row = by_id[good['ledger']]
        days = good['days']
        out.append(
            Homemade(
                good['label'],
                days,
                row.low * good['count'],
                row.high * good['count'],
                days * LABORER_DAY_SEN,
                days * LABORER_DAY_SEN * low_share,
                days * LABORER_DAY_SEN * high_share,
                good['scope'],
                good['verdict'],
                good['source'],
            )
        )
    return out
