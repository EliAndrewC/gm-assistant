"""US average retail prices from the Bureau of Labor Statistics, read through FRED (feature 221).

Two jobs: `reprice` fills the snapshot options tied to a series, and `crosscheck` sets each other
option of the same good beside the national average, so a stale or mistyped price shows.

WHY FRED AND NOT THE BLS API: api.bls.gov answers this container with a 503 "website is busy"
page (2026-10-24, with and without a user agent); FRED republishes the same series as a keyless
CSV (`fredgraph.csv?id=<series>`). The series are averages of supermarket packs in US cities, so
a household bulk pack runs below them: crosscheck flags only a price under half or over twice the
average.
"""

from __future__ import annotations

import csv
import io
import urllib.request
from collections.abc import Mapping

from l7r.money.basket import Snapshot

__all__ = ['SERIES', 'crosscheck', 'fetch', 'latest']

# series -> (good, what it is, this good's units per the series' pound: kg for rice; liters of
# dried beans at about 0.8 kg a liter, the density the snapshots assume)
SERIES = {
    'APU0000701312': ('rice', 'rice, white, long grain, uncooked, per lb', 2.20462),
    'APU0000714233': ('beans', 'dried beans, per lb', 2.20462 * 0.8),
}
LOW, HIGH = 0.5, 2.0


def fetch(series: str) -> str:  # pragma: no cover - the HTTP boundary
    url = f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}'
    req = urllib.request.Request(url, headers={'User-Agent': 'gm-assistant money crosscheck'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        body: bytes = resp.read()
    return body.decode()


def latest(text: str) -> tuple[str, float]:
    """The newest (YYYY-MM, dollars a pound) in a FRED CSV; FRED writes '.' for a missing month."""
    rows = [r for r in csv.reader(io.StringIO(text)) if r]
    good = [(d[:7], float(v)) for d, v in rows[1:] if v not in ('', '.')]
    if not good:
        raise ValueError('no observations in the FRED file')
    return good[-1]


def crosscheck(snapshot: Snapshot, csvs: Mapping[str, str]) -> list[str]:
    """One line per option of a good with a series, against that series' newest month."""
    out = []
    for series, text in csvs.items():
        good, what, factor = SERIES[series]
        month, per_lb = latest(text)
        for opt in snapshot.options.get(good, ()):
            if opt.series == series or opt.dollars_per_unit is None:
                continue
            average = per_lb * factor
            ratio = opt.dollars_per_unit / average
            flag = '' if LOW <= ratio <= HIGH else '  <- check this price'
            out.append(
                f'{good}: {opt.priced_as} ${opt.dollars_per_unit:,.2f} = {ratio:.2f}x the BLS '
                f'average for {what} ({month}, ${average:,.2f}){flag}'
            )
    return out
