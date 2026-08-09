# `wip/` - draft maps parked OUT of `pool/`

`test_villages.py` sweeps `pool/*/*.gen.py` and gates every manifest it finds, so a draft that
does not yet pass the gate cannot live in `pool/` - it would turn `make done` red for every
session in the repo, not just the one working on it. A draft therefore waits here until it is
green, then moves into its tier's pool directory. (Same precedent as Minami's map draft, which
was parked out of `pool/` while its temple-budget knobs landed first.)

## `shiro-daika.gen.py` - the domain capital, feature 019

A SKELETON: wall, moat, river, ways, gates and the castle. It renders, and its castle answered
the question it was built to answer (see `settlements/capitals.md`, the bailey-wall verdict).

**It fails exactly one check, and the failure is correct**: `imperial_road_town_has_farrier`. A
settlement on the Imperial road keeps a shoeing forge at its relay stables, and this one has no
stables because it has no fabric at all yet.

**Do not fix that by drawing the farrier.** That was tried: the forge then wanted its stables
(`farrier_serves_a_stables`), which then wanted wells (`wells_sized_to_buildings`). Each fix
pulled in the next, which is the engine correctly refusing to call a half-populated city
coherent. Feature 020 draws the fabric and the check passes on its own; until then this map is a
draft, not a pool member.


## Findings carried into feature 020 (settlement-review, 2026-08-09)

Two defects the review found that are NOT fixed here, because both are fabric-era work:

1. **Four of six way-over-water crossings have no bridge, and the CHECK is blind the same way.**
   `settlement.bridges()` carries `M["road"]` (the single Imperial polyline) but never `M["roads"]`,
   and its water list omits both `M["river"]` and the castle's own moat. `roads_bridge_water`
   mirrors those omissions exactly - so placement and check agree, and both are wrong. A sharp
   illustration of the "placement and its check must read the SAME source" rule guaranteeing
   AGREEMENT, not correctness. Unbridged: the east and southwest trunk roads over the city moat,
   and the east road over the river (off-crop, but real geometry).
2. **The declared civic quarter is in the wrong wedge.** `quarters[0]` marks NE "civic" and calls it
   the castle's ground, but the castle straddles all four wedges, and `capitals.md` puts the
   ministries OUTSIDE the ote-mon flanking the ote-suji - which, with the gate facing south, is the
   SOUTHERN wedges. Feature 020's packs zone against these, so settle it before packing.

Also at 020: this subject needs a `.notes.md` with a Review log before it moves into
`pool/capitals/` - every pool subject has one.
