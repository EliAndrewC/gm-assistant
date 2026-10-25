"""Write `webapp/l7r/money/data/eras/*.json` from diagram's answer to diagram#13 (its feature 412).

Run from the clone root: `python3 specs/222-money-basket-and-section/measure/eras.py`, then
`( cd webapp && python3 -m l7r.money export )`. Every figure below is diagram's, quoted from the
question page named beside it; the arithmetic is this script's.

How a good's grams are found (the why):
- **Chained, not converted.** A Japanese series (Mitsui, Kumon, Kimura) is divided by the SAME
  series' value in Kyoto 1745-1754 and multiplied by the reference era's grams for that good. A
  unit guess (a koku of salt's weight, a tan's length) then cancels, and only the reference era
  carries it. Where a series has no 1745-1754 value of its own, the base named in `BASE` is used.
- **Coin grams cancel in a conversion.** An era's goods and coins use the same grams a monme, so
  the goods-dollar, wage-dollar and Rokugani readings of an amount depend only on its prices in
  its own money; the grams a monme matter for the silver shown, not for the conversion. An era
  spanning recoinages takes the coinage that circulated longest in it, named in its confidence.
- **China is in grams already** (Allen et al. at 37 g a tael) or in taels, converted at the
  constants in `UNITS`.
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[3] / 'webapp/l7r/money/data/eras'
Q = 'https://github.com/EliAndrewC/diagram/blob/main/research/questions/'
SALT = Q + '0273-what-did-salt-cost.html'
FUEL = Q + '0279-what-did-charcoal-cost.html'
RENT = Q + '0265-what-did-it-cost-to-rent-a-room-or-a-house.html'
JAPAN = Q + '0286-what-did-a-years-necessities-cost-in-japan-era-by-era.html'
CHINA = Q + '0288-what-did-a-years-necessities-and-a-days-labor-cost-in-china-era-by-era.html'
WAGES = Q + '0250-what-did-an-unskilled-laborer-earn.html'
OSAKA_WAGE = Q + '0257-what-did-a-laborer-earn-in-osaka-in-the-1620s.html'
JCOINS = Q + '0287-how-much-silver-was-a-monme-a-ryo-and-a-bu-coinage-by-coinage.html'
CCOINS = Q + '0289-what-was-a-tael-a-string-of-cash-and-a-chinese-dollar-worth-in-silver.html'
BM = 'https://www.econhistdbm.com/uploads/8/1/9/7/81977286/reh_japanese_wages_bassino_and_ma.pdf'
UNITS_SRC = 'https://en.wikipedia.org/wiki/Chinese_units_of_measurement'

# Units (each named once). A koku of rice is 150 kg, Bassino & Ma's own figure (71.85 monme a koku
# of Mitsui rice at their 1.49 g a kg and 3.11 g a monme is 150 kg); its 180.39 L give 0.8315 kg a
# liter, used for every grain priced by volume so China and Japan are compared on one assumption.
KOKU_L = 180.39
RICE_KG_L = 150 / KOKU_L
SALT_KG_L = 1.1  # GUESS: diagram 0273 gives 1.0-1.2 kg a liter
KAN_KG = 3.75
MBTU_KG = 1055.06 / 15.5  # air-dry wood at FAO's 15.5 MJ a kg (diagram 0279): 68.07 kg
UNITS = {
    'ming_shi_l': 107.37,  # Ming sheng 1.0737 L
    'qing_shi_l': 103.55,  # Qing sheng 1.0355 L
    'jin_kg': 0.5968,  # the Ming and Qing jin
    'catty_kg': 0.6048,  # the treaty-port catty, 1 1/3 lb (Canton, Beijing 1900s)
    'sesame_oil_kg_l': 0.92,
}

# The reference era: Bassino & Ma's Table 3 grams (at their 3.11 g a monme) rescaled to the Genbun
# monme's 1.725 g of pure silver (diagram 0287). The rescale is uniform, so the reference's
# relative prices, and the 2017 sheet's $552 a koku, are unchanged.
GENBUN = 1.725
F = GENBUN / 3.11
BM_GRAMS = {
    'beans': 0.99,
    'soybeans': 1.49,
    'rice': 1.49,
    'barley-wheat': 0.76,
    'fish': 2.18,
    'buckwheat-others': 0.61,
    'edible-oil': 5.66,
    'cloth': 5.83,
    'lamp-oil': 5.66,
}
REF = {k: v * F for k, v in BM_GRAMS.items()}
REF['salt'] = 17.77 / (KOKU_L * SALT_KG_L) * GENBUN
REF['fuel'] = 2.64 / (10 * KAN_KG) * MBTU_KG * GENBUN
# Edo's 300-500 mon a month in 1804-1830 (0265, an unsourced popular page; Kyoto and Osaka SILENT),
# at Edo's 15.9 g a kanmon of the 1820s in Genbun silver (0287), over a 9.93 m2 room.
ROOM_M2 = 9.93
REF['housing'] = 400 * 12 * 0.0159 / ROOM_M2

# Each Japanese series' value in Kyoto 1745-1754 (monme), the base its chain divides by. Kumon's
# soybeans, edible oil and cloth are imputed there, so they chain off what Kumon imputes them
# from: soybeans off rice (the reference prices them alike a kg), edible oil off lamp oil (alike a
# liter), cloth off its imputation (13.93 x rice a kg, 5.557 a tan in 1745-1754).
BASE = {
    'mitsui': {'rice': 71.85, 'salt': 17.77, 'fuel': 2.64, 'lamp-oil': 327.49},
    'kumon': {
        'rice': 0.3989,
        'soybeans': 0.3989,
        'barley-wheat': 0.3011,
        'lamp-oil': 1.8104,
        'edible-oil': 1.8104,
        'cloth': 5.557,
    },
    # Kimura's 1620-1650 file, per koku (oil per koku from 2.41 a sho), chained to Mitsui's Kyoto.
    'kimura': {'rice': 71.85, 'salt': 17.77, 'lamp-oil': 327.49, 'edible-oil': 327.49},
}
SOURCE = {'mitsui': JAPAN, 'kumon': JAPAN, 'kimura': JAPAN}


def chain(series: str, good: str, value: float, grams_monme: float) -> float:
    return REF[good] * value / BASE[series][good] * grams_monme / GENBUN


def jgoods(grams_monme: float, figures: dict[str, tuple[str, float, str]]) -> dict[str, dict]:
    out = {}
    for good, (series, value, note) in figures.items():
        if good == 'soybeans' and series == 'kimura':
            # Kimura prices soybeans by the koku too: at rice's weight a koku, as the reference does.
            g = chain('kimura', 'rice', value, grams_monme)
        else:
            g = chain(series, good, value, grams_monme)
        out[good] = {'silver_g': round(g, 4), 'label': 'historical', 'source': SOURCE[series], 'note': note}
    return out


def jcoins(grams_monme: float, monme_a_ryo: float, mon_a_monme: float, note: str) -> dict[str, dict]:
    ryo = grams_monme * monme_a_ryo
    mon = grams_monme / mon_a_monme
    return {
        'monme': {'silver_g': round(grams_monme, 4), 'source': JCOINS, 'note': note},
        'mon': {'silver_g': round(mon, 6), 'source': JCOINS, 'note': f'{mon_a_monme:.1f} mon to the monme'},
        'kanmon': {'silver_g': round(mon * 1000, 3), 'source': JCOINS, 'note': '1,000 mon'},
        'ryo': {'silver_g': round(ryo, 2), 'source': JCOINS, 'note': f'{monme_a_ryo:.1f} monme to the ryo'},
        'bu': {'silver_g': round(ryo / 4, 3), 'source': JCOINS, 'note': 'A quarter of a ryo (the gold count: 4 bu a ryo)'},
        'shu': {'silver_g': round(ryo / 16, 4), 'source': JCOINS, 'note': 'A sixteenth of a ryo (16 shu a ryo)'},
    }


def wage(grams: float, source: str, note: str) -> dict:
    return {'silver_g_per_day': round(grams, 4), 'source': source, 'note': note}


def per_kg_of_shi(taels: float, shi_l: float, tael_g: float) -> float:
    return taels * tael_g / (shi_l * RICE_KG_L)


ERA_REF_WAGE = 2.82 * F
ERAS: dict[str, dict] = {}

ERAS['kyoto-1745'] = {
    'place': 'Kyoto',
    'years': '1745-1754',
    'reference': True,
    'confidence': (
        "The basket's food, cloth and lamp oil are Bassino & Ma's Table 3 (rice and lamp oil recorded "
        'in Kyoto; the rest reconstructed by the paper from price ratios), at the Genbun monme. Salt and '
        "firewood are Mitsui's Kyoto books (diagram 0273, 0279); only the weight of a koku of salt is "
        'guessed. Housing is a guess: no Kyoto or Osaka rent was found, so it borrows Edo 1804-1830.'
    ),
    'note': (
        "THE REFERENCE ERA: Rokugan's prices are this era's prices, through the rice anchor. Grams are of "
        'pure silver at the Genbun monme (1.725 g); Bassino & Ma priced at 3.11 g a monme, a figure whose '
        'basis their paper does not give (diagram 0287), so their grams are rescaled by 1.725 / 3.11.'
    ),
    'coins': jcoins(GENBUN, 61.3, 72.6, 'Genbun silver: 3.75 g at 46% fine, 1.725 g pure'),
    'goods': {
        **{
            k: {'silver_g': round(v, 6), 'label': 'historical', 'source': BM, 'note': f'{BM_GRAMS[k]} g at 3.11 g a monme, rescaled to 1.725'}
            for k, v in REF.items()
            if k in BM_GRAMS
        },
        'salt': {
            'silver_g': round(REF['salt'], 4),
            'label': 'guess',
            'source': SALT,
            'note': "17.77 monme a koku (Mitsui, Kyoto, mean of 20 seasons); the price is attested, only a koku's weight is guessed (1.1 kg a liter, of diagram's 1.0-1.2)",
        },
        'fuel': {
            'silver_g': round(REF['fuel'], 4),
            'label': 'historical',
            'source': FUEL,
            'note': "Firewood, 2.64 monme for 10 kan (37.5 kg) (Mitsui, Kyoto); a million BTU is 68 kg of air-dry wood at FAO's 15.5 MJ a kg",
        },
        'housing': {
            'silver_g': round(REF['housing'], 4),
            'label': 'guess',
            'source': RENT,
            'note': 'No Kyoto or Osaka rent was found. Edo back tenement, 300-500 mon a month in 1804-1830 (an unsourced popular page), at 15.9 g a kanmon, over a 9.93 m2 room',
        },
    },
    'wage': wage(2.82 * F, BM, "An unskilled laborer's day, Kyoto 1745-54 (Table 3): 0.907 monme; Mitsui's 0.91 agrees"),
}

ERAS['osaka-1620'] = {
    'place': 'Osaka and Kyoto',
    'years': '1620-1650',
    'confidence': (
        "Kimura's 1620-1650 file (Jacks, GPIH): named Osaka, but only some years are Osaka's and the rest "
        "chiefly Kyoto's. Cloth is left out (white cloth and bleached cotton differ by three times). The "
        'wage is the Osaka castle rebuilding of 1620-1628. Coins at the Keicho monme and the law of 1609.'
    ),
    'coins': jcoins(3.0, 50, 80, 'Keicho silver, 3.00 g pure; 50 monme a ryo and 80 mon a monme by the law of 1609 (an early market rate was about 43 monme a ryo; a copper market rate is SILENT)'),
    'goods': jgoods(3.0, {
        'rice': ('kimura', 33.51, '33.51 monme a koku, mean of 31 years'),
        'soybeans': ('kimura', 31.03, '31.03 monme a koku (17 years), at rice\'s weight a koku'),
        'salt': ('kimura', 10.8, '1.08 monme a to (5 years)'),
        'lamp-oil': ('kimura', 241, '2.41 monme a sho (14 years); lamp or edible not said'),
        'edible-oil': ('kimura', 241, '2.41 monme a sho (14 years); lamp or edible not said'),
    }),
    'wage': wage(1.0 * 3.0, OSAKA_WAGE, 'Osaka castle rebuilding, 1620-1628: 0.8-1.2 monme a day; the midpoint'),
}

ERAS['osaka-1700'] = {
    'place': 'Osaka',
    'years': '1690-1735',
    'confidence': (
        "Priced at the Kyoho coinage of 1722-1735, the era's longest single coinage: Kumon's rice and "
        'barley for those years. It is for the years of good silver, 1690-1694 and 1719-1735, whose '
        "rice stood within a fifth of Kyoho's (Iwahashi); 1695-1718 and 1736-1739 have eras of their "
        'own, at the baser coinages of those years. The wage is borrowed: none was found for these '
        "years, so it is the reference day chained back by Kumon's farm-servant wage."
    ),
    'coins': jcoins(3.0, 57.7, 82.8, 'Kyoho silver (1722-1735), 3.00 g pure; market rates of 1722-1735'),
    'goods': jgoods(3.0, {
        'rice': ('kumon', 0.2959, "0.296 monme a kg, Kumon's observed 1722-1735"),
        'barley-wheat': ('kumon', 0.2368, "0.237 monme a kg, Kumon's observed 1722-1735 (8 years)"),
    }),
    # Kumon's farm-servant year is observed in both spans: 51.2 Kyoho monme (1722-1735) and 113.9
    # Genbun monme (1745-1754); its ratio in grams carries the reference day back.
    'wage': wage(ERA_REF_WAGE * (51.17 * 3.0) / (113.9 * GENBUN), WAGES, "BORROWED: none found for these years; the reference day (0.907 monme) chained by Kumon's farm-servant year, 51.2 monme in 1722-1735 and 113.9 in 1745-1754, in grams of silver"),
}

# The split by coinage (GM 2026-10-24). Iwahashi's Osaka rice in nominal monme, against Kyoho's
# 1722-1735: 0.93x in 1690-1694, 1.37x in 1695-1705, 1.36x in 1706-1711, 2.75x in 1712-1718, 1.21x
# in 1719-1721, 1.48x in 1736-1739. The ryo and mon rates of 1706-1718 are Kusama Naokata's (三貨図彙,
# 1815), from diagram's 0287 "The market rates of 1705-1719" (its feature 418): each row's midpoint,
# averaged over the rows quoted in that era's silver.
def kumon_wage(farm_year: float, grams_monme: float, years: str) -> dict:
    """The reference day chained back by Kumon's farm-servant year, in grams of silver."""
    return wage(
        ERA_REF_WAGE * (farm_year * grams_monme) / (113.9 * GENBUN),
        WAGES,
        f"BORROWED: none found for these years; the reference day (0.907 monme) chained by Kumon's "
        f'farm-servant year, {farm_year:.1f} monme in {years} and 113.9 in 1745-1754, in grams of silver',
    )


ERAS['osaka-1695'] = {
    'place': 'Osaka',
    'years': '1695-1705',
    'confidence': (
        "Kumon's observed rice in nominal monme, 1695-1705, half again Kyoho's, in the Genroku silver "
        '(64%, 2.40 g a monme), at the market rates of 1700. The wage is borrowed.'
    ),
    'coins': jcoins(2.40, 47.5, 78.0, 'Genroku silver (1695-1705), 2.40 g pure; market rates of 1700 (47-48 monme a ryo, 3.71 kanmon a ryo)'),
    'goods': jgoods(2.40, {
        'rice': ('kumon', 0.4408, "0.441 monme a kg, Kumon's observed 1695-1705 (11 years)"),
    }),
    'wage': kumon_wage(84.899, 2.40, '1695-1705'),
}

# Rice in nominal monme stood where it had under Genroku (Iwahashi 1.36x Kyoho's, against 1.37x), but a
# ryo cost half again as many monme of the baser silver, so these years take an era of their own.
ERAS['osaka-1706'] = {
    'place': 'Osaka',
    'years': '1706-1711',
    'confidence': (
        "Kumon's observed rice in nominal monme, 1706-1711, in the Hoei silver (50%, 1.875 g a monme). "
        "The ryo and mon rates are one Osaka money-changer's, compiled a century later (Kusama, 1815), "
        'and name no city. The wage is borrowed.'
    ),
    'coins': jcoins(1.875, 71.5, 53.8, "Hoei silver (1706-1711), 1.875 g pure; Kusama's market rates in Hoei silver, late 1706-1710 (about 62-83 monme a ryo, 40-66 mon a monme), the mean of the rows' midpoints"),
    'goods': jgoods(1.875, {
        'rice': ('kumon', 0.473, "0.473 monme a kg, Kumon's observed 1706-1711 (6 years)"),
    }),
    'wage': kumon_wage(105.922, 1.875, '1706-1711'),
}

# The worst-overstated span at osaka-1700's prices: rice at 2.75x Kyoho's.
ERAS['osaka-1712'] = {
    'place': 'Osaka',
    'years': '1712-1718',
    'confidence': (
        "Kumon's observed rice in nominal monme, 1712-1718, nearly three times Kyoho's, in the "
        "\"current silver\" of Kusama's entries: the Hoei, Eiji, Mitsuho and Yotsuho silvers, dealt in "
        'as one with no rate of their own. Its grams are the 1714 law\'s (2 of current for 1 of Keicho); '
        "they cancel in a conversion. The ryo and mon rates are Kusama's (1815), and 1715-1716 are "
        'SILENT. The wage is borrowed.'
    ),
    'coins': jcoins(1.5, 77.6, 44.1, "Current silver (1712-1718), 1.50 g pure by the 1714 law's 2 for 1 of Keicho; Kusama's market rates of 1712-1714 and 1717 (about 65-93 monme a ryo, 40-59 mon a monme), the mean of the rows' midpoints"),
    'goods': jgoods(1.5, {
        'rice': ('kumon', 0.8396, "0.840 monme a kg, Kumon's observed 1712-1718 (7 years)"),
    }),
    'wage': kumon_wage(109.935, 1.5, '1712-1718'),
}

ERAS['osaka-1736'] = {
    'place': 'Osaka',
    'years': '1736-1739',
    'confidence': (
        "Kumon's observed rice and barley in the new Genbun silver, 1736-1739: the reference era's "
        'coinage, at the market rates of its first years, which differ from 1745-1754\'s. The wage is '
        'borrowed.'
    ),
    'coins': jcoins(GENBUN, 55.1, 53.0, 'Genbun silver, 1.725 g pure; market rates of 1736-1739'),
    'goods': jgoods(GENBUN, {
        'rice': ('kumon', 0.43, "0.430 monme a kg, Kumon's observed 1736-1739"),
        'barley-wheat': ('kumon', 0.4637, "0.464 monme a kg, Kumon's observed 1738-1739 (2 years)"),
    }),
    'wage': kumon_wage(92.35, GENBUN, '1736-1739'),
}

ERAS['osaka-1780'] = {
    'place': 'Osaka',
    'years': '1780-1789',
    'confidence': (
        "Kumon's observed prices a kg and a liter (rice, soybeans, barley, lamp oil). The wage is "
        "borrowed: the 1780s are SILENT, so it is Kyoto's 1790s day (Kyoto's was 0.80 in 1760-1762 and "
        '0.85 in the 1790s).'
    ),
    'coins': jcoins(GENBUN, 57.56, 103.8, 'Genbun silver, 1.725 g pure; market rates 1780-1786 (coin-walk) and 1787-1789 (Osaka), year-weighted'),
    'goods': jgoods(GENBUN, {
        'rice': ('kumon', 0.4555, '0.456 monme a kg'),
        'soybeans': ('kumon', 0.4662, '0.466 monme a kg'),
        'barley-wheat': ('kumon', 0.3693, '0.369 monme a kg'),
        'lamp-oil': ('kumon', 1.8888, '1.89 monme a liter'),
    }),
    'wage': wage(0.85 * GENBUN, WAGES, "BORROWED: Kyoto's 1790s, 0.85 monme a day (Mitsui)"),
}


def mitsui_era(place, years, grams, coins, mitsui, kumon, day, conf, extra=None):
    figures = {g: ('mitsui', v, n) for g, (v, n) in mitsui.items()}
    figures.update({g: ('kumon', v, n) for g, (v, n) in kumon.items()})
    goods = jgoods(grams, figures)
    goods.update(extra or {})
    return {
        'place': place,
        'years': years,
        'confidence': conf,
        'coins': coins,
        'goods': goods,
        'wage': wage(day[0] * grams, WAGES, day[1]),
    }


MIX = "Mitsui's books (rice, salt, lamp oil, firewood) with Kumon's soybeans, barley, edible oil and cloth, each chained to its own 1745-1754 level"

ERAS['kyoto-1790'] = mitsui_era(
    'Kyoto', '1790-1799', GENBUN,
    jcoins(GENBUN, 60.6, 106.8, 'Genbun silver, 1.725 g pure; Osaka market rates of the 1790s'),
    {'rice': (82.97, '82.97 monme a koku'), 'lamp-oil': (312.23, '312.23 monme a koku'), 'fuel': (2.79, 'firewood, 2.79 monme for 10 kan')},
    {'soybeans': (0.4509, "Kumon 1790-1799, 0.451 a kg"), 'barley-wheat': (0.3205, 'Kumon 1790-1799, 0.321 a kg')},
    (0.85, "Mitsui, Kyoto 1790s: 0.85 monme a day"),
    MIX + ". Salt is left out: Kyoto's salt from 1791 reads two-fifths to a sixth of Edo's and Osaka's (a unit or grade change, DOUBTFUL), and no Edo or Osaka salt was recorded in these years.",
)
ERAS['kyoto-1800'] = mitsui_era(
    'Kyoto', '1800-1817', GENBUN,
    jcoins(GENBUN, 64.4, 109.0, 'Genbun silver, 1.725 g pure; Osaka market rates of the 1800s and 1810s'),
    {'rice': (74.47, '74.47 monme a koku'), 'lamp-oil': (270.52, '270.52 monme a koku'), 'fuel': (2.81, 'firewood, 2.81 monme for 10 kan')},
    {'soybeans': (0.3680, 'Kumon, 0.368 a kg'), 'barley-wheat': (0.2945, 'Kumon, 0.295 a kg'), 'edible-oil': (1.4850, 'Kumon, 1.485 a liter'), 'cloth': (6.2062, 'Kumon, 6.21 a tan')},
    (0.86, 'Mitsui, Kyoto 1800-1817: 0.86 monme a day'),
    MIX + '. Salt is left out (DOUBTFUL in Kyoto after 1790; no Edo or Osaka salt in these years).',
)
ERAS['edo-1818'] = mitsui_era(
    'Edo', '1818-1829', 1.35,
    jcoins(1.35, 63.4, 6610 / 63.4, 'Bunsei silver (from 1820), 1.35 g pure; 63.4 monme a ryo (Osaka, 1820s), 6,610 mon a ryo (Edo, 1820s)'),
    {'rice': (70.69, '70.69 monme a koku'), 'salt': (15.24, '15.24 monme a koku'), 'lamp-oil': (283.79, '283.79 monme a koku'), 'fuel': (1.96, 'firewood, 1.96 monme for 10 kan')},
    {'soybeans': (0.4099, 'Kumon, 0.410 a kg'), 'barley-wheat': (0.2840, 'Kumon, 0.284 a kg'), 'edible-oil': (1.4447, 'Kumon, 1.445 a liter'), 'cloth': (6.0083, 'Kumon, 6.01 a tan')},
    (0.90, 'Mitsui, Edo 1818-1829: 0.90 monme a day'),
    MIX + '. Housing is the guess the reference era borrows (Edo 1804-1830, an unsourced page). Priced at the Bunsei monme; 1818-1819 were Genbun.',
    {'housing': {
        'silver_g': round(400 * 12 * 1.35 / (6610 / 63.4) / ROOM_M2, 4),
        'label': 'guess',
        'source': RENT,
        'note': 'Edo back tenement, 300-500 mon a month in 1804-1830 (an unsourced popular page), over a 9.93 m2 room',
    }},
)
ERAS['edo-1830'] = mitsui_era(
    'Edo', '1830-1844', 0.975,
    jcoins(0.975, 62.8, 108.1, 'Tenpo silver (from 1837), 0.975 g pure; Osaka market rates 1840-1843'),
    {'rice': (111.46, '111.46 monme a koku'), 'salt': (23.90, '23.90 monme a koku'), 'lamp-oil': (404.56, '404.56 monme a koku'), 'fuel': (1.99, 'firewood, 1.99 monme for 10 kan')},
    {'soybeans': (0.5623, 'Kumon, 0.562 a kg'), 'barley-wheat': (0.4189, 'Kumon, 0.419 a kg'), 'edible-oil': (1.8497, 'Kumon, 1.850 a liter'), 'cloth': (7.1667, 'Kumon, 7.17 a tan')},
    (0.91, 'Mitsui, Edo 1830-1844: 0.91 monme a day'),
    MIX + '. Priced at the Tenpo monme of 1837-1844; 1830-1836 were Bunsei (1.35 g).',
)
ERAS['edo-1850'] = mitsui_era(
    'Edo', '1850-1859', 0.975,
    jcoins(0.975, 67.5, 6725 / 67.5, 'Tenpo silver, 0.975 g pure; Osaka market rates 1850-1854 and 1855-1859, averaged'),
    {'rice': (117.22, '117.22 monme a koku'), 'salt': (35.67, '35.67 monme a koku'), 'lamp-oil': (461.38, '461.38 monme a koku'), 'fuel': (2.08, 'firewood, 2.08 monme for 10 kan')},
    {'soybeans': (0.6738, 'Kumon, 0.674 a kg'), 'barley-wheat': (0.4746, 'Kumon, 0.475 a kg (5 years)'), 'edible-oil': (2.36, 'Kumon, 2.36 a liter'), 'cloth': (7.85, 'Kumon, 7.85 a tan (2 years)')},
    (0.92, 'Mitsui, Edo 1850s: 0.92 monme a day'),
    MIX + ".",
)
ERAS['edo-1860'] = mitsui_era(
    'Edo', '1860-1867', 0.4875,
    jcoins(0.4875, 83.6, 83.7, 'Ansei silver (from 1859), 0.4875 g pure as prescribed (0.525 by a 14% assay); market rates 1860-1867'),
    {'rice': (283.17, '283.17 monme a koku'), 'salt': (82.15, '82.15 monme a koku'), 'lamp-oil': (873.52, '873.52 monme a koku'), 'fuel': (3.84, 'firewood, 3.84 monme for 10 kan')},
    {'soybeans': (2.2533, 'Kumon, 2.25 a kg'), 'barley-wheat': (0.9771, 'Kumon, 0.977 a kg (2 years)'), 'edible-oil': (6.3491, 'Kumon, 6.35 a liter')},
    (1.18, 'Mitsui, Edo 1860-1867: 1.18 monme a day'),
    MIX + ". The era's mean hides a several-fold rise in prices; cloth is left out (one year, 133 a tan).",
)


def cgood(g: float, source: str, note: str, label: str = 'historical') -> dict:
    return {'silver_g': round(g, 4), 'label': label, 'source': source, 'note': note}


def ccoins(tael_g: float, tael_note: str, cash_a_tael: float | None, cash_note: str, dollar: bool = False) -> dict:
    out = {'tael': {'silver_g': tael_g, 'source': CCOINS, 'note': tael_note}}
    if cash_a_tael:
        out['cash'] = {'silver_g': round(tael_g / cash_a_tael, 6), 'source': CCOINS, 'note': cash_note}
    if dollar:
        out['dollar'] = {
            'silver_g': round(0.72 * tael_g, 3),
            'source': CCOINS,
            'note': "0.72 tael (the GPIH files' rate, a later Beijing one); Canton's own 1835 figures bracket it at 0.71 and 0.75. Cents are hundredths",
        }
    return out


ALLEN = 'Allen et al. 2011 (GPIH), a modern reconstruction, at 37 g a tael'
ERAS['beijing-1500'] = {
    'place': 'Beijing',
    'years': '1490-1520',
    'confidence': (
        "Rice alone, from the official table of 1497 (an official price). The wage is borrowed: none "
        "was found, so it is the Lower Yangzi's of 1573-1620."
    ),
    'coins': ccoins(36.9, 'The Ming treasury tael of the 1500s, 36.9 g', 700, '700 cash to the tael (Hongzhi; 1508)'),
    'goods': {'rice': cgood(per_kg_of_shi(25 / 80, UNITS['ming_shi_l'], 36.9), CHINA, '25 guan of paper notes a shi at 80 guan a tael (1497, official); a Ming shi of 107.4 L')},
    'wage': wage(0.0415 * 36.9, CHINA, "BORROWED: the Lower Yangzi's 0.040-0.043 tael a day of 1573-1620"),
}
ERAS['beijing-1615'] = {
    'place': 'Beijing',
    'years': '1573-1627',
    'confidence': (
        "Empire-wide rice by reign (a modern silver conversion) with Beijing's official prices of 1615 "
        'for salt, sesame oil and firewood. The wage is the Lower Yangzi market wage.'
    ),
    'coins': ccoins(36.9, 'The Ming treasury tael of the 1500s, 36.9 g', 800, "About 800 standard cash to the tael in Beijing (the late 1500s' official rate)"),
    'goods': {
        'rice': cgood(per_kg_of_shi((0.638 * 48 + 0.927 * 7) / 55, UNITS['ming_shi_l'], 36.9), CHINA, '0.638 tael a shi (1573-1620) and 0.927 (1621-1627), year-weighted'),
        'salt': cgood(0.0065 * 36.9 / UNITS['jin_kg'], CHINA, '0.006-0.007 tael a jin (Beijing official, 1615)'),
        'edible-oil': cgood(0.028 * 36.9 / UNITS['jin_kg'] * UNITS['sesame_oil_kg_l'], CHINA, 'Sesame oil, 0.028 tael a jin (Beijing official, 1615), at 0.92 kg a liter'),
        'fuel': cgood(0.2375 * 36.9 / (100 * UNITS['jin_kg']) * MBTU_KG, CHINA, 'Firewood, 0.125-0.35 tael a 100 jin (Beijing official, 1615), the midpoint'),
    },
    'wage': wage(0.0415 * 36.9, CHINA, 'Lower Yangzi, 0.040-0.043 tael a day'),
}
ERAS['songjiang-1680'] = {
    'place': 'Songjiang',
    'years': '1670-1690',
    'confidence': (
        "Ye Mengzhu's Songjiang: rice and soybeans by the shi, salt by the jin, at the Qing treasury tael. "
        'The wage is borrowed: SILENT for Songjiang, so the Lower Yangzi\'s.'
    ),
    'coins': ccoins(37.3, 'The Qing treasury tael, 37.3 g (the tael these prices were counted in is not stated)', 1090, 'About 1,090 cash to the tael (Songjiang 1671-1690, 971-1,182)'),
    'goods': {
        'rice': cgood(per_kg_of_shi(0.875, UNITS['qing_shi_l'], 37.3), CHINA, '0.85-0.9 tael a shi (1682-1684); 0.63 in 1672 and 2.0 in 1680 are the ends of the range'),
        'soybeans': cgood(per_kg_of_shi(0.8, UNITS['qing_shi_l'], 37.3), CHINA, "0.6-1.0 tael a shi, at rice's weight a shi"),
        'salt': cgood(0.019 * 37.3 / UNITS['jin_kg'], CHINA, '0.006-0.032 tael a jin, the midpoint'),
    },
    'wage': wage(0.055 * 37.3, CHINA, 'BORROWED: the Lower Yangzi, 0.055 tael a day'),
}
ERAS['beijing-1736'] = {
    'place': 'Beijing',
    'years': '1736-1760',
    'confidence': ALLEN + " (rice, millet, oils, fuel). Beans, cloth and flour are left out: priced a kg, a square meter and as flour, not as the basket's liter, length of bolt and grain.",
    'coins': ccoins(37.0, "Allen et al.'s 37 g (the standard is not named)", 800, "800 standard cash to the tael (1737). Beijing's capital cash passed two for one: a sum in capital cash is worth about half"),
    'goods': {
        'rice': cgood(1.322, CHINA, ALLEN + ', grams a kg (1738-1760)'),
        'buckwheat-others': cgood(1.044, CHINA, 'Millet, ' + ALLEN),
        'edible-oil': cgood(4.082, CHINA, ALLEN),
        'lamp-oil': cgood(3.368, CHINA, ALLEN),
        'fuel': cgood(11.2, CHINA, ALLEN),
    },
    'wage': wage(3.255, CHINA, "Allen et al.'s Beijing day, 1738-1760 (the official 75 cash of 1736 is 3.47 g)"),
}
ERAS['suzhou-1750'] = {
    'place': 'Suzhou',
    'years': '1750-1799',
    'confidence': "Rice alone, from Qian Yong's Lower Yangzi in normal years of the mid-Qianlong. After 1785 rice and the cash rate both rose (rice 1.9-2.7 taels a shi at 1,300-1,400 cash a tael), so a later amount reads high.",
    'coins': ccoins(37.0, '37 g (the standard is not stated)', 800, "About 800 cash to the tael (Jiangnan, 760-840 in the mid-Qianlong; 1,300-1,400 by 1796)"),
    'goods': {'rice': cgood(per_kg_of_shi(1.85, UNITS['qing_shi_l'], 37.0), CHINA, '14-15 cash a sheng at 760-840 cash a tael: 1.7-2.0 taels a shi')},
    'wage': wage(0.071 * 37.0, CHINA, "Lower Yangzi, 0.071 tael a day (Liu); Allen et al.'s are about 30% higher"),
}
ERAS['beijing-1820'] = {
    'place': 'Beijing',
    'years': '1820-1830',
    'confidence': ALLEN + ' (rice, millet, oils, fuel), with the rural Beijing fuel store\'s cash rate.',
    'coins': ccoins(37.0, "Allen et al.'s 37 g", 1243, "1,243 cash to the tael (rural Beijing 1820-1830, 1,159-1,329, at face count: the store's 95-99 cash a day then match Allen's 2.8 g). Beijing's capital cash passed two for one"),
    'goods': {
        'rice': cgood(1.781, CHINA, ALLEN),
        'buckwheat-others': cgood(1.477, CHINA, 'Millet, ' + ALLEN),
        'edible-oil': cgood(5.684, CHINA, ALLEN),
        'lamp-oil': cgood(4.689, CHINA, ALLEN),
        'fuel': cgood(9.499, CHINA, ALLEN),
    },
    'wage': wage(2.805, CHINA, "Allen et al.'s Beijing day, 1820-1830"),
}
ERAS['canton-1835'] = {
    'place': 'Canton',
    'years': '1830-1839',
    'confidence': (
        "The Chinese Repository's Canton of 1835. Rice is the top of its range. The cash rate is "
        "BORROWED from rural Beijing's 1835 (no Canton rate was found)."
    ),
    'coins': ccoins(37.0, '37 g (the standard is not stated)', 1251, 'BORROWED: 1,251 cash to the tael, rural Beijing 1835', dollar=True),
    'goods': {
        'rice': cgood(3 * 37.0 / (100 * UNITS['catty_kg']), CHINA, 'Up to 3 taels a picul (100 catties of 0.6048 kg)'),
        'fish': cgood(0.105 * 37.0 / UNITS['catty_kg'], CHINA, 'Salted fish, 0.05-0.16 tael a catty, the midpoint'),
        'salt': cgood(0.03 * 37.0 / UNITS['catty_kg'], CHINA, '0.02-0.04 tael a catty, the midpoint'),
        'fuel': cgood(0.14 * 37.0 / (100 * UNITS['catty_kg']) * MBTU_KG, CHINA, 'Firewood, 0.1-0.18 tael a picul, the midpoint'),
    },
    'wage': wage(3.7, CHINA, 'One mace (0.1 tael, about 14 cents) a day'),
}
DOLLAR_G = 0.72 * 37.0
ERAS['beijing-1900'] = {
    'place': 'Beijing',
    'years': '1900-1919',
    'confidence': "Meng and Gamble's Beijing retail prices in dollars (rice and millet); rent and fuel are left out (a family's, of unknown size).",
    'coins': ccoins(37.0, '37 g (a dollar at 0.72 tael)', 1380 / 0.72, '136-140 coppers of 10 cash to the dollar (1918-1919, the end of the era)', dollar=True),
    'goods': {
        'rice': cgood(5.763 * DOLLAR_G / (100 * UNITS['catty_kg']), CHINA, '$5.76 a 100 catties (1910s)'),
        'buckwheat-others': cgood((4.462 + 4.923) / 2 * DOLLAR_G / (100 * UNITS['catty_kg']), CHINA, 'Millet, $4.46 (1900s) and $4.92 (1910s) a 100 catties'),
    },
    'wage': wage(0.2281 * DOLLAR_G, CHINA, 'Unskilled construction, 22.8 cents a day with food (Meng and Gamble)'),
}

# Kept by hand, outside this script: Bassino & Ma's own Tokyo, at 25 g a yen.
HAND = {'tokyo-1882'}


def text(era: dict) -> str:
    return json.dumps(era, indent=2, ensure_ascii=False) + '\n'


if __name__ == '__main__':
    for era_id, era in ERAS.items():
        (OUT / f'{era_id}.json').write_text(text(era))
        print(era_id, {k: v['silver_g'] for k, v in era['goods'].items()})
