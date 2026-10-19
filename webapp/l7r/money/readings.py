"""The two dollar readings of a koku: what it BUYS (PPP) and how much it MATTERS ("big deal").

PPP: a dated snapshot re-prices a historical basket of goods (Bassino & Ma's Japan Basket A,
Kyoto 1745-54, in grams of silver) in current dollars. Silver becomes coin through rice: a koku
is a mass of rice, so `zeni per gram of silver = 100 / (koku_kg x rice silver price per kg)`.
Dollars per koku = basket dollars / basket zeni x 100.

WHY RE-PRICE, NEVER CPI-SCALE (handoff, 2026-10-18): rice and beans move differently from the
CPI, so scaling the 2017 figure would carry 2017's relative prices forward under a new date.
Each re-pricing is a new `data/baskets/YYYY-MM.json`; old snapshots are never edited.

THE KOKU'S RICE MASS IS AN INPUT, not a constant. Settled by research (diagram 0248), it stays an input so a
snapshot can be read at other masses: l7r.md says ~40
gallons, while budgets.md "Historical units" says ~180 L (~48 gallons) and ~150 kg brown; the 2017
sheet used 151.515 kg (its 2.257575 g silver per zeni is 1.49 g/kg x 151.515 kg / 100, i.e. 40
gallons read as if a liter of rice weighed a kilogram); 40 gallons of uncooked rice at ~0.8 kg/L is
~121 kg. Declined: hard-coding 2.257575, which hides the question.

"BIG DEAL": one koku is 1/3.32 of an unskilled laborer's year (the 2017 sheet, from Bassino &
Ma's ~2 kg rice/day), applied to a dated US unskilled full-time year. Declined: asserting the
GM's table figure of ~$10,000 - derived, it moves with the wage. Updating = re-taking the wage.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    'DATA',
    'KOKU_KG',
    'LABORER_KOKU_YEAR',
    'Good',
    'Snapshot',
    'Wage',
    'big_deal_per_koku',
    'laborer_days',
    'load_snapshots',
    'load_wages',
    'ppp_per_koku',
    'resolve_koku_kg',
]

DATA = Path(__file__).parent / 'data'

KOKU_KG = {
    'sheet-2017': 100 / 0.66,  # the 2017 spreadsheet's basis (rice 0.66 zeni/kg): ~151.5 kg
    # budgets.md "Historical units": 1 koku ~ 180 L (~48 gallons), ~150 kg as the brown rice the
    # kokudaka was assessed in ("the canonical figure"), ~136 kg polished, ~187 kg paddy
    'budgets-brown': 150.0,
    # 0248: ~136 kg is the MILLED YIELD of a koku of brown rice, not the weight of a koku-volume
    'budgets-polished': 136.0,
}
# diagram 0248 (2026-10-18): a koku is 180.39 L (ATTESTED), ~150 kg as brown rice (ATTESTED ONLY FOR modern
# reckoning, ~0.83 kg/L); the canon's "about 40 gallons" holds in IMPERIAL gallons (~180 L). The 40-US-gallon
# reading (~121 kg) is withdrawn, so the sheet's 151.5 kg stands.
# https://github.com/EliAndrewC/diagram/blob/main/research/questions/0248-how-much-rice-was-a-koku.html
DEFAULT_KOKU = 'sheet-2017'

# diagram 0250: ~1.9-2 kg of rice a day (Kyoto 1745-54) is ATTESTED; the 250-day year is a modern economists'
# convention, NOT ATTESTED. 3.32 = 2 kg x 250 days / ~150 kg.
LABORER_KOKU_YEAR = 3.32
WORKING_DAYS = 250  # the 2017 sheet's working year


def laborer_days(sen: int) -> float:
    """The internal-consistency yardstick: how many days an unskilled laborer works for this."""
    return sen / (LABORER_KOKU_YEAR * 1000 / WORKING_DAYS)


@dataclass(frozen=True, slots=True)
class Good:
    good: str
    unit: str
    quantity: float
    silver_g_per_unit: float
    dollars_per_unit: float
    link: str


@dataclass(frozen=True, slots=True)
class Snapshot:
    date: str
    priced_by: str
    source: str
    rice_silver_g_per_kg: float
    goods: tuple[Good, ...]

    @property
    def dollars(self) -> float:
        return sum(g.quantity * g.dollars_per_unit for g in self.goods)

    @property
    def silver_g(self) -> float:
        return sum(g.quantity * g.silver_g_per_unit for g in self.goods)

    def zeni(self, koku_kg: float) -> float:
        return self.silver_g * 100 / (koku_kg * self.rice_silver_g_per_kg)


@dataclass(frozen=True, slots=True)
class Wage:
    date: str
    hourly: float
    hours_per_year: float
    basis: str
    source: str

    @property
    def year(self) -> float:
        return self.hourly * self.hours_per_year


def load_snapshots(directory: Path = DATA / 'baskets') -> list[Snapshot]:
    """Every snapshot, oldest first; the last is the default."""
    out = []
    for path in sorted(directory.glob('*.json')):
        raw = json.loads(path.read_text())
        goods = tuple(
            Good(
                g['good'],
                g['unit'],
                g['quantity'],
                g['silver_g_per_unit'],
                g['dollars_per_unit'],
                g['link'],
            )
            for g in raw['goods']
        )
        out.append(
            Snapshot(
                raw['date'], raw['priced_by'], raw['source'], raw['rice_silver_g_per_kg'], goods
            )
        )
    if not out:
        raise FileNotFoundError(f'no basket snapshots in {directory}')
    return out


def load_wages(path: Path = DATA / 'wages.json') -> list[Wage]:
    """Every wage reading, oldest first; the last is the default."""
    rows = json.loads(path.read_text())
    return sorted((Wage(**r) for r in rows), key=lambda w: w.date)


def resolve_koku_kg(value: str | float | None) -> tuple[float, str]:
    """A name from KOKU_KG, a number of kg, or None for the default -> (kg, label)."""
    if value is None:
        value = DEFAULT_KOKU
    if isinstance(value, str) and value in KOKU_KG:
        return KOKU_KG[value], value
    kg = float(value)
    return kg, f'{kg:g} kg'


def ppp_per_koku(snapshot: Snapshot, koku_kg: float) -> float:
    return snapshot.dollars / snapshot.zeni(koku_kg) * 100


def big_deal_per_koku(wage: Wage, laborer_koku_year: float = LABORER_KOKU_YEAR) -> float:
    return wage.year / laborer_koku_year
