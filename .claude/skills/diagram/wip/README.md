# `wip/` - draft maps parked OUT of `pool/`

`tests/test_villages.py` sweeps `pool/*/*.gen.py` and gates every manifest it finds, so a draft that
does not yet pass the gate cannot live in `pool/` - it would turn `make done` red for every
session in the repo, not just the one working on it. A draft therefore waits here until it is
green, then moves into its tier's pool directory. (Same precedent as Minami's map draft, which
was parked out of `pool/` while its temple-budget knobs landed first.)

## `shiro-daika.gen.py` - the domain capital, features 019 + 020

The SKELETON (019: wall, moat, river, ways, gates, castle) plus the GROUND-RESERVING LAYER
(020): the government ward on the ote-suji, the Imperial Magistrate's compound, the eight
lineage compounds, the sovereign temples and the teramachi rim, the wharf with its two granary
complexes and brokers' row, the towpath, and the aqueduct. Everything that must be sited BEFORE
housing is now on the map and reserves its ground; feature 021's packs flow around it.

**It fails exactly one check, and the failure is correct**: `imperial_road_town_has_farrier`. A
settlement on the Imperial road keeps a shoeing forge at its relay stables, and this one has no
stables because it has no housing fabric yet.

**Do not fix that by drawing the farrier.** That was tried: the forge then wanted its stables
(`farrier_serves_a_stables`), which then wanted wells (`wells_sized_to_buildings`). Each fix
pulled in the next, which is the engine correctly refusing to call a half-populated city
coherent. Feature 021 draws the housing and the check passes on its own; until then this map is
a draft, not a pool member.

**Both findings the 019 review carried into 020 are CLEARED (2026-08-09):**

1. **The blind bridging** - fixed at the root: the carried-ways and crossed-waters sets are now
   derived ONCE (`settlement.bridge_carried_ways` / `bridge_crossed_waters`) and consumed by
   both `bridges()` and `roads_bridge_water`, so the old silent symmetry (two hand-kept lists
   that agreed and were both wrong) cannot recur by re-adding keys on one side. All six
   crossings are decked, including the east road over the river and the ote-suji over the
   castle's own moat; the aqueduct is in the same shared source, so any future way over it
   demands a deck automatically.
2. **The civic quarter re-zoned** - civic is now the ground the government actually occupies
   (the ote-suji band south of the ote-mon, ministries through chancellery); the four interior
   wedges split at the kagi-no-te junction and stay "mixed" until 021 packs them.

**Feature 021 still owes**: all housing, the public wells + the aqueduct's in-wall draw-basins,
fire towers, the kido mesh, the entertainment district beside the brokers' row, the relay
stables + farrier, the population fill and the rest of the capital check block - plus a
`.notes.md` with a Review log before the map moves into `pool/capitals/` (every pool subject
has one).
