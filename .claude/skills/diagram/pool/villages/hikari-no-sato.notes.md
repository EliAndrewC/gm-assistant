# Design notes: Hikari no Sato, the SPLIT (multi-block) village

*Reconstructed 2026-08-08 from the generator's docstring and comments. Everything below is sourced
from `hikari-no-sato.gen.py`.*

**Subject**: the multi-block variant of the water-first family, against Hoshigaoka's single-field
base case. A low central SPUR of higher ground runs N->S down the valley, so the flat cultivable
ground falls into a **WEST block and an EAST block**, one on each flank, with the settlement and its
shrines strung along the dry spur between them.

**Why it exists**: to establish that **block count is TERRAIN-driven**. Two blocks split by a spur is
a normal, common pattern (Knapp), not an exotic one - which is the claim the map exists to make
visible, and the reason the single-field case is the base rather than the only case.

## Water

`down_deg=90` - north-high, south-low, water flows N->S. **Each block is its own `build_comb` fan**
with its own sluice and its own seed: a brook out of the northern hills is diverted into each block's
head-race at its north head, the comb distributes the water southward, and each block drains at its
low southern foot into a valley brook off-map, with the un-reclaimed low toes left as reed marsh.

An earlier version opened the V-field UPWARD with water entering from the top; it was reversed so the
water enters at the head and leaves at the foot, which is the way a fan actually works.

## Review log

- **2026-07-21: the headman routing fix was caught here.** The `headman()` guard used to test
  `_nucleated`, so a DISPERSED to-scale village's headman fell through to the legacy record path,
  which `_farmsteads_bundle` draws as a LONE house (the abandoned-ruin path) - the grandest farmstead
  in the village with no threshing yard and no garden. Both homestead styles route through the bundle
  path now. Hikari no Sato is the map that exposed it.
- **2026-08-08 RNG re-roll** (positional/scoped randomness, engine-wide). No fixes needed.

## Known open

- **No `notes.md` existed for this map until 2026-08-08**, so anything settled between its authoring
  and that date lives only in gen comments and may not be recorded here. Treat gaps as unrecorded
  rather than as decided.
