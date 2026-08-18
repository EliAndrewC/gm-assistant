# Feature 125: a way does not stop and resume across empty ground

## Why

`settlement-review` on Sawada reported two lane ends "terminating in rounded caps in bare grass with
a wellhead and a tree clump between them, in the centre of the built-up frontage" - one street drawn
as two, with a 110 ft hole in it. The gate could not see it: every existing way rule measures whether
a lane REACHES something or whether a house is reached BY something, and both were satisfied. A hole
in the middle of a run satisfies every distance rule on the map while being the most visible defect
on the sheet.

## What ships

- **`lanes_do_not_break_mid_run`** (gate segment 0612, `segments_07c`). Two non-connector lane ends
  between 40 and 150 ft apart, each heading within 15 degrees of the other, with a corridor a way
  could pass through, and no third way already spanning them, is one way drawn as two.
- **`_bridge_collinear_breaks`** in `hamletgen/ways.py`, which heals them: 12 passes, skipping pairs
  already spanned.
- The frozen negative fixture
  `pool/regressions/lanes_do_not_break_mid_run_fires_on_sawadas_broken_spine.json`.

## Three things this got wrong first, all recorded at the point of change

1. **"Do the ends point at each other?" is not "are their headings similar?"** Two ends facing across
   a gap have OPPOSITE outward headings, so comparing the headings for similarity selected parallel
   arms and excluded the collinear break the rule is named for. The test is each end's heading
   against the bearing to the other end (`_aim_off`), in the generator and the check alike.
2. **"Something is near the gap" is not "something is in it", and "something is in it" is not "no way
   could pass".** Proximity excused nearly every gap once the field outline was in the list, since
   these lanes run along the field margin. Occupancy of the straight line then excused the motivating
   defect, because a wellhead sat on it - and a lane goes ROUND a wellhead. Three parallel corridors
   are tested and the break is honest only if all three are blocked.
3. **Ground COVER is not an obstacle.** Groves and open commons were in the blocking list, and the
   motivating gap lies inside a homestead grove, so the check passed on the very defect it was
   written for while looking fully covered. Crop, water, marsh and anything built stop a way; a copse
   does not, and a *yashikirin* belt is planted around a lane rather than across it.

## The fixture had to be built by removing the repair

By the time the check existed the generator closed that hole two independent ways
(`_bridge_collinear_breaks`, and `_join_orphan_ways` even with the bridge pass disabled), so a
re-roll of seed 6 is a green map and cannot be the fixture. The manifest first frozen under this name
was a REPAIRED one, which is how the check spent its first day silently passing. The fixture is now
that re-roll with the single link way deleted, and its `_regression` block records the deletion and
both healers. Doctrine written up in `dev/gate.md`.

## Verification

- The fixture fires, naming the reported break: `(1729, 2321, 110)`.
- All four live scripted hamlets pass.
- `tests/test_regressions.py` green across the whole corpus; `tests/check_village/test_segments_07_water.py` green.
- 48-seed sweep: no `lanes_do_not_break_mid_run` failures.
