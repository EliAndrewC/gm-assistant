# Design notes: Ueda ("upper paddy"), the LARGE-village variant

*Reconstructed 2026-08-08 from the generator's docstring and comments. Everything below is sourced
from `ueda.gen.py`.*

**Subject**: the first regular-village variant built on the Hoshigaoka foundation - the same single-
field nucleated form, deliberately varied along two axes.

**Why it exists**: to show the **upper end of the village band**. Its population is pinned to 425
(~85 households), above the ~350 mode, so the paddy, pond and cluster are all sized UP from
Hoshigaoka's 350. The GM's framing (2026-07-22): **70 farmhouses is the AVERAGE village, not the
maximum** - the band runs ~200-500 and Ueda occupies its top.

## GM decisions (settled)

| Decision | Value | What it drove |
|---|---|---|
| Fall | NE-high -> SW-low (`down_deg=135`) | deliberately opposite Hoshigaoka's NW-high, for variance |
| Population | 425 / ~85 households | everything scales up from it |
| Frame | TALLER than Hoshigaoka's landscape frame | a NE->SW field grows down-and-left, so the SW toe needs the height |

## Deliberate choices

- **The NE valley-head pond is nudged west, flush with the dry-field strip**, so it does not poke past
  the crop on the east. Its NORTH poke is the intrinsic cost of a valley-head reservoir and is
  **exempted automatically** by the crop advisory - a field-sourcing pond is hydrologically anchored,
  so it is allowed to sit where the water is rather than where the crop ends.
- **The head-race and inflow brook are CLIPPED to the pond edge** where they meet it, so they JOIN the
  water at its rim instead of being drawn over it.

## Review log

- **2026-08-08 RNG re-roll** (positional/scoped randomness, engine-wide). No fixes needed; the
  village tier came out fully isolated once a farmhouse's rake and kura became position-seeded.

## Known open

- **No `notes.md` existed for this map until 2026-08-08**, so anything settled between its authoring
  and that date lives only in gen comments and may not be recorded here. Treat gaps as unrecorded
  rather than as decided.
