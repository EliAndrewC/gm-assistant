"""The koku's rice mass, the US wage readings, and the laborer's year (features 219, 221).

GOODS DOLLARS (what a koku BUYS) moved to `basket.py` in feature 221, which splits the basket, its
dated dollar prices and the eras that price it in silver. This module keeps what both readings
share.

THE KOKU'S RICE MASS IS AN INPUT, not a constant, so a reading can be taken at other masses.
Settled by research (diagram 0248): a koku is 180.39 L and ~150 kg as brown rice; the canon's
"about 40 gallons" holds in imperial gallons. The 2017 sheet's 151.515 kg (its 2.257575 g silver
per zeni is 1.49 g/kg x 151.515 kg / 100) therefore stands. Declined: hard-coding 2.257575, which
would hide the mass inside a constant.

WAGE DOLLARS (how much a sum MATTERS; "big deal" dollars until feature 221 renamed them, GM
2026-10-24): one koku is 1/3.32 of an unskilled laborer's year (the 2017 sheet, from Bassino &
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
    'WORKING_DAYS',
    'Wage',
    'laborer_days',
    'load_wages',
    'resolve_koku_kg',
    'wage_dollars_per_koku',
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
# diagram 0248 (2026-10-18): a koku is 180.39 L (ATTESTED) and ~150 kg as brown rice (ATTESTED
# ONLY FOR modern reckoning, ~0.83 kg/L). The canon's "about 40 gallons" holds in IMPERIAL
# gallons (~180 L); the 40-US-gallon reading (~121 kg) is withdrawn, so 151.5 kg stands. Source:
# https://github.com/EliAndrewC/diagram/blob/main/research/questions/0248-how-much-rice-was-a-koku.html  # noqa: E501
DEFAULT_KOKU = 'sheet-2017'

# diagram 0250: ~1.9-2 kg of rice a day (Kyoto 1745-54) is ATTESTED; the 250-day year is a
# modern economists' convention, NOT ATTESTED. 3.32 = 2 kg x 250 days / ~150 kg.
LABORER_KOKU_YEAR = 3.32
WORKING_DAYS = 250  # the 2017 sheet's working year


def laborer_days(sen: int) -> float:
    """The internal-consistency yardstick: how many days an unskilled laborer works for this."""
    return sen / (LABORER_KOKU_YEAR * 1000 / WORKING_DAYS)


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

    @property
    def day(self) -> float:
        """A working day's pay, on the same 250-day year the laborer's koku-year uses."""
        return self.year / WORKING_DAYS


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


def wage_dollars_per_koku(wage: Wage, laborer_koku_year: float = LABORER_KOKU_YEAR) -> float:
    return wage.year / laborer_koku_year
