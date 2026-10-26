"""Shizu's memorial to Shoda is priced in a player handout; this keeps the two from drifting apart.

The handout (`current/shoda-shrine.md` in the l7r repository) quotes each contract's fair price
for the design in `shrine_links.txt`, on a foot trail. When shrine prices change, this test fails,
and the fix is to re-price the handout in the same pass (the GM commits the l7r repository),
update the figures below, and redeploy. It replaced a Claude Code memory note (feature 229).
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

from l7r.shrines import load_catalog, parse_design, upgrade_params
from l7r.shrines.pricing import price_design

LINKS = Path(__file__).with_name('shrine_links.txt')
HANDOUT = Path('/host-l7r-repo/current/shoda-shrine.md')

# Fair price per contract on a foot trail, as the handout states them (2026-10-19 design).
PINNED = {
    'stonework': 5.15,
    'rites': 4.72,
    'earthwork': 3.24,
    'porterage': 1.70,
    'carpentry': 0.50,
    'metalwork': 0.39,
    'remains': 0.34,
    'finishing': 0.30,
}
# The handout's row names for the catalog's contract keys.
ROWS = {
    'Stonework': 'stonework',
    'Rites': 'rites',
    'Earthwork': 'earthwork',
    'Porterage': 'porterage',
    'Carpentry': 'carpentry',
    'Bell': 'metalwork',
    'Remains': 'remains',
    'Finishing': 'finishing',
}
FIX = (
    "Shrine prices moved, so Shizu's handout is out of date: re-price it "
    '(current/shoda-shrine.md in the l7r repo; the GM commits that repo), '
    'update PINNED here, and redeploy.'
)


def shoda_prices() -> dict[str, float]:
    catalog = load_catalog()
    link = next(
        ln.strip()
        for ln in LINKS.read_text(encoding='utf-8').splitlines()
        if 'Shoda' in ln and ln.startswith('http')
    )
    params = parse_qs(urlsplit(link).query)
    design = parse_design(catalog, upgrade_params(catalog, params) or params)
    return {k: v for k, v in price_design(catalog, design, 'trail').by_contract.items() if v}


def test_the_shoda_design_still_costs_what_the_handout_says() -> None:
    prices = shoda_prices()
    assert {k: round(v, 2) for k, v in prices.items()} == PINNED, FIX
    assert round(sum(prices.values()), 1) == 16.3, FIX


def test_the_handout_table_matches_the_pinned_prices() -> None:
    if not HANDOUT.exists():
        pytest.skip('the l7r repository is not mounted here; the pinned figures are still checked')
    rows = dict(
        re.findall(
            r'^\| \*\*(\w+)\*\* \|[^|]*\| ~([\d.]+) koku \|',
            HANDOUT.read_text(encoding='utf-8'),
            re.M,
        )
    )
    assert {ROWS[name]: float(koku) for name, koku in rows.items()} == {
        k: round(v, 1) for k, v in PINNED.items()
    }, FIX
