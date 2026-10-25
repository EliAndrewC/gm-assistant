# Plan: feature 224

Data first, then the one code change, then regenerate.

1. `webapp/l7r/money/data/goods.json`: add `miso` (kg) and `soy-sauce` (liter); reword Soybeans.
2. `specs/222-money-basket-and-section/measure/eras.py`: a Mitsui base for miso (15.43 monme for 10 kan) and soy
   sauce (91.06 monme a koku) in Kyoto 1745-54; Kyoto 1745 gains both goods (grams at the Genbun monme); the six
   other Mitsui eras gain both from 0303's cells; the declined cells and why, beside them. Run it.
3. Baskets: `standard.json` and `standard-no-housing.json` take the split (FR-002), with the basis in the
   description. The soy sauce quantity waits for the GM's ruling on its yield.
4. `basket.py` `load`: snapshots sorted by their `date`, not the file name (a "2026-10-25" file name sorts before
   "2026-10"); `reprice`'s help names both forms.
5. `data/snapshots/2026-10-25.json`: every 2026-10 option, plus miso, soy sauce and the alternatives (User Story 3).
6. `export`; tests (`test_money*.py`) updated where they pin the standard basket, the snapshot list or the headline;
   new tests for the basket split, the snapshot order and the new goods' periods.
7. Docs: the money skill's range, `l7r/money/CLAUDE.md`, memory. Gate, screenshots of the two new goods, deploy,
   diagram#18.
