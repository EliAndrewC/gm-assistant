**Money research: the standard basket's prices in every era the record draws on**

Questions from gm-assistant feature 222 (`specs/222-money-basket-and-section/`, its `research.md`). The GM wants every
historical amount of money on the research site to carry a conversion: goods dollars (what it bought), wage dollars
(what share of a laborer's day it was) and Rokugani coin (sen, zeni, bu, koku). That needs one standard basket priced in
each era and place the record cites. The engine and the first two eras are built; these questions fill the rest.
An answer can land as an era file (`webapp/l7r/money/data/eras/<id>.json` in gm-assistant: place, years, coins in grams
of pure silver, each good's silver price with label and source, an unskilled day wage) or as figures in the question
files, which gm-assistant then types in. Japan-first for prices and wages (Tokugawa series are the richest); China
beside it.

**The standard basket**, per adult per year: rice 114 kg, soybeans 52 kg, barley and wheat 10 kg, buckwheat and millets
16 kg, other beans 4 L, fish 3.5 kg, edible (rapeseed) oil 1 L, cotton cloth 5 m (a ~36 cm bolt width), lamp oil 2.6 L
(Bassino & Ma 2005, Japan basket A), plus salt 7.3 kg, fuel 3 million BTU (Allen et al. 2011) and 3.31 m² of a back-
tenement room for a year.

### 1. Salt, fuel and a room in Kyoto, 1745-54

- **Question**: what did salt, firewood (or other cooking fuel) and a back-tenement room cost in Kyoto (or Osaka) in
  1745-1754, or the nearest dates found? And how much salt did a household use a year?
- **Figure needed**: grams of silver (or mon, with the rate) per kg of salt, per bundle or weight of firewood (with its
  weight, to reach a price per million BTU), and per month for a room of known size; salt per person per year.
- **Canon beside it**: the reference era's guesses, each labeled guess: salt 0.44 g/kg (Kashimo 1763-72, 0273), fuel
  11.2 g per million BTU (Allen's Beijing c. 1750), housing 13.8 g per m²-year (Edo back tenement 1804-30, 0265); salt
  7.3 kg a year (20 g a day).
- **Region order**: Japan first (the reference era IS Kyoto 1745-54); Qing beside it only as a cross-check.

### 2. The basket's cost in every era and place the record cites

- **Question**: which eras and places does the record's price research draw on (Edo/Osaka/Kyoto in the later Edo
  period, the Nakasendo post stations, Qing Beijing and the Lower Yangzi, Ming, Song where it has prices)? For each, what
  did the standard basket's goods cost, as many as the sources allow, in its own money?
- **Figure needed**: per era and place, a price per unit for each good found (at least rice), with its source; goods not
  found left out (the engine prices the basket over the goods found and names the rest; rice alone is the floor).
- **Canon beside it**: the two eras built: Kyoto 1745-54 (all goods, Bassino & Ma Table 3) and Tokyo 1882-86 (basket A
  only). Allen et al. 2011 Table 5 already has Beijing c. 1750 for most goods (with sorghum, not rice).
- **Region order**: both; list every era the record cites a price in.

### 3. An unskilled day wage in each of those eras and places

- **Question**: what did an unskilled laborer earn a day in each era and place of question 2?
- **Figure needed**: a day's wage in the era's money (and in silver), with source.
- **Canon beside it**: Kyoto 1745-54 2.82 g of silver a day; Tokyo 1882-86 4.5 g (Bassino & Ma); 0250 already holds more.
- **Region order**: both.

### 4. Coin rates in each era

- **Question**: what was each era's money worth in grams of pure silver: mon (and kanmon), monme, ryo and bu in
  Japan by decade; copper cash, strings and taels in Qing and earlier China?
- **Figure needed**: grams of pure silver per coin or unit, per era, with source (the market rate where it moved from
  the legal one).
- **Canon beside it**: built so far: monme 3.11 g (Bassino & Ma), mon 1/66 monme in 1766 Osaka, ryo 60 monme (the law of
  1700); yen 25 g in 1882-86. 0277 has Osaka 1787-1859 and Edo 1781-1842.
- **Region order**: both.
