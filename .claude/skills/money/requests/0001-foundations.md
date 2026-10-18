**Money research: four foundation questions for the gm-assistant money skill**

The gm-assistant money skill (feature 219, `specs/219-money-skill/` on gm-assistant `main`) converts Rokugani prices
between coins and two dollar readings and keeps a price ledger in which every figure carries a label (historically
accurate / deliberate deviation / guess) and a source pointer. These four questions are what the GM's 2013-2017 notes
leave open, and every other price leans on them. They are the handoff's candidate requests 1-4
(`money/HANDOFF.md` in the GM's l7r repository).

For each: the question, the figure the skill needs, the canon it must sit beside, and the region order.

### 1. Land price against yield

- **Question**: what did farmland sell for, expressed in years of its net yield (to the buyer, after tax), in Tokugawa
  Japan and in Qing China? How did it vary between irrigated rice land and dry land, and between near-city and remote?
- **Figure needed**: years-of-net-yield multiple (a range is fine), plus any attested interest or rate of return on land.
- **Canon beside it**: `setting/l7r.md` "Money": a family plot is assessed at ~15 koku/yr, tax 1/3 (5 koku), rent cap 1/6
  (2.5 koku); a family farm is said to sell for ~50 koku, ~20x the landlord's 2.5 koku. The GM (2013): *"based largely on
  nothing"*. Interest canon: 15-20% in cities, ~25% countryside.
- **Region order**: Japan and China both; report each.

### 2. Unskilled day wages

- **Question**: what did an unskilled laborer earn per day and per year, in rice and in coin, in the city against the
  countryside (18th-century Japan first; Qing China as the comparison)? How many working days in a year?
- **Figure needed**: the unskilled laborer's year in koku of rice (the skill uses 3.32 koku as the "big deal" divisor,
  from Bassino & Ma via the GM's 2017 spreadsheet: ~2 kg rice/day, 250 days), and the city/country ratio.
- **Canon beside it**: none fixed; the 2017 working figure is 1.33 zeni/day unskilled, 3.32 koku/yr; farm labor 3.5
  koku/yr; a koku is "the rice to feed a man for a year".
- **Region order**: Japan first.

### 3. The koku of rice

- **Question**: what was the historical Japanese koku of rice in volume and in weight (polished and brown, and how much
  that varied by period and domain), and what weight of uncooked rice fills a given volume?
- **Figure needed**: kg per koku, and kg per liter of uncooked rice.
- **Canon beside it**: `setting/l7r.md` "Money": 1 koku ~ 40 gallons of rice (151.4 L), "the amount of rice needed to
  feed a man for a year". The 2017 spreadsheet used 151.5 kg (40 gallons read as if a liter weighed a kilogram); at
  ~0.8 kg/L, 40 gallons is ~120 kg. This changes the dollar value of a koku by ~20%; the GM decides the canon from your
  findings.
- **Region order**: Japan first (the koku is a Japanese measure); a note on the Chinese shi/dan is welcome.

### 4. The Kyoto basket

- **Question**: Bassino & Ma, "Japanese Unskilled Wages in International Perspective, 1741-1913" (Research in Economic
  History 23, 2005): what are Japan Basket A's quantities and its Kyoto 1745-54 prices in grams of silver, quoted
  verbatim? Are there Basket B or "respectability" variants, and what do they hold?
- **Figure needed**: each good's quantity per year and silver price per unit, verbatim, so the skill's 2017 snapshot can
  be checked against the source and future snapshots re-price the source basket, not a copy of a copy.
- **Canon beside it**: the 2017 snapshot (rice 114 kg at 1.49 g/kg, soybeans 52 kg at 1.49, adzuki 4 L at 0.99,
  barley/wheat 10 kg at 0.76, fish 3.5 kg at 2.18, buckwheat and others 16 kg at 0.61, edible oil 1 L at 5.66, cotton
  5 m at 5.83, lamp oil 2.6 L at 5.66; total 325.816 g). Chris worked from `Unskilled Labor Tokugawa..pdf` in the
  GM's money folder.
- **Region order**: Japan.

### What the skill needs back

Per question: the fragment FILE (`research/questions/NNNN-<slug>.html`), the verdict for each figure (ATTESTED /
ATTESTED ONLY FOR / NOT ATTESTED / SILENT), and what is still open. Where history contradicts the canon above, report the
history as found and flag it; the GM decides. I (gm-assistant) will verify against the files on diagram `main` and close
this issue.
