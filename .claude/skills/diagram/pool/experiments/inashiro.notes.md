# Design notes: Inashiro (稲代, "rice-field") - the SCRIPTED hamlet

*The head-to-head map of the scripted-generation experiment (2026-08-11).*

**Subject**: a small outlying rice-farming community of ~15 households / ~75 inhabitants, belonging
to a village district whose headman lives in the main village. Like every hamlet it has no headman
of its own, no shrine, no tax-free plots and no burial ground.

**Kanji triangle**: 稲 *ina* "rice plant" + 代 *shiro* "paddy" (as in 苗代 *nawashiro*, a seedbed).
稲代 Inashiro, "the rice-field" - the plainest possible name for the plainest possible hamlet, which
is the point: this map exists to be ordinary.

## Why it exists

It is the deliverable of the experiment in [`../../hamletgen.py`](../../hamletgen.py): can a SCRIPT
do what a session currently does by hand? Inashiro was given deliberately the same brief as the
hand-authored [`../hamlets/ikegami.gen.py`](../hamlets/ikegami.gen.py) - ~15 households, land
falling due south, a brook off the northern high ground feeding one comb field, the field draining
at its low foot into a *tameike* - so the two maps can be read side by side.

The comparison is the evidence:

| | Ikegami (authored) | Inashiro (scripted) |
|---|---|---|
| generator | 239 lines, ~40 literal coordinates | 9 lines, no coordinates |
| paddy acreage | 15.3 acres against a stated target of ~20 | 18.4 acres against a computed 19.5 |
| households seated | 15 of 15 | 15 of 15 |
| gate | green | green |

## What the script decided, and from what

Every position on this sheet is derived from geometry already on the map. The order is the
pipeline's, and it is the same order a person follows:

1. **The fall and the drainage bearing** are declared (due south). Everything downstream reads them.
2. **The intake** sits at the head of the ground the field will occupy - gravity, not a knob. Its
   lateral position on that head margin is rolled.
3. **The field** is SOLVED rather than sized by eye: the comb is rebuilt at a bisected size
   multiplier until the drawn plot area lands within a few percent of ~1.3 gross acres per
   household. (Ikegami's own docstring asks for ~20 acres and its closing line reports 15.3; nothing
   catches that, because no check reads acreage and `field_fall` is a pixel length tuned by eye.)
4. **The tameike** walks downslope from the drain's own outfall until its rim is genuinely clear of
   the field envelope, and stops at the first position that is.
5. **The cluster** is seated on the field margin whose outward normal best faces the cold wind -
   背山面水, back to the hill and face to the water - excluding any margin below the drain (the wet
   toe is not building ground) and any whose back is already under the dry hem.
6. **The lanes** come before the houses, because a lane is a no-build corridor the homesteads front:
   a rolled skeleton in the cluster's own frame, a spur to the nearest reachable point of the field,
   and the connector track out to the frame, its bearing swung away from the crop until it clears.
7. **The homesteads** fill to the declared household count, widening the band and drawing more
   candidates when the placer refuses, rather than re-rolling the map.
8. **Wells and byres** drop into the courtyards the finished layout left.
9. **The hinterland**, then the **woodland patches** (found by scanning for ground still open), then
   the **windbreak belt**, shaped to the houses that actually landed.

## Known open

- The **bare comb floor** on the fan's shoulders - paddy-green ground inside the field envelope
  where the carve did not tessellate into plots - is inherited from the shared `build_comb` engine,
  not from the scripted pipeline; Ikegami shows the same thing at the foot of its fan.
- The wind is derived from the slope (cold air drains downhill off the high ground), which makes the
  windbreak's side a consequence of the terrain rather than an independent regional fact. A GM who
  knows the real prevailing wind for the province should pin it on the spec.
- **Dry hem plots run ~3.5x the size of Ikegami's** and chain single-file rather than packing two or
  three deep, so the hem reads as large fields rather than household strips (`settlement-review`,
  2026-08-11). Parcel size, not acreage - the total is comparable. It wants a researched constant of
  its own.
- The **lane stand-off** is wider than an authored map's, because `LANE_CLEARANCE` is set to work
  around the engine's "placement tests a different footprint than the one drawn" debt.
