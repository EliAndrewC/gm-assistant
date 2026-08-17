# Phase 0 Research: The placer tests the footprint it draws

Two jobs here. **D1-D3** are the Principle XII opening bookend - what reality determines each constant we propose to change, before any of it is implemented. **D4-D5** are the measurement: the Principle XIII baseline, and the refusal attribution re-taken on maps that still exist.

One of these findings has already changed the plan. See D2.

---

## D1. What determines the distance between a farmhouse and a village lane

**Decision**: `LANE_CLEARANCE` stops being the correctness guarantee and becomes a placement preference. Correctness moves to the drawn-footprint-versus-drawn-tread test that item 3 installs.

**What reality says** (China-first, Japan corroborating; the underlying sweep is recorded in [`settlements/ways.md`](../../.claude/skills/diagram/settlements/ways.md), researched and source-verified 2026-07):

- A village lane is a **narrow single track**, not a road. China deliberately built a network of narrow paths for the one-wheeled barrow, the carrying-pole porter, the packhorse and the litter; two-wheeled cart tracks predominated only in the flat northern plains, which is not our rice-south analog. Japan agrees. At our render that is a ~10 ft tread.
- Houses **front** the lane. They are not set back from it by custom - a *yashiki* lot's frontage stands hard against the track, which is what makes the lane read as a lane rather than as a clearing. So there is no historical setback distance to encode.
- What reality therefore determines is **not a spacing norm but a physical constraint**: the building's wall may not stand on the trodden surface. That is a gap verdict between two footprints, which is row 1 of the project's centers/footprints doctrine - *real rotated corners, never a center, never a circumscribed radius*.

**Does the current value match?** No, and it does not claim to. The constant's own comment says it stays wide "until then" - until the bundle path tests the rect it draws. It is a workaround wearing a constant's clothes.

**The honest arithmetic**, at hamlet scale (1 px = 1 ft). **Corrected after D6's measurement** - an earlier draft of this table mis-stated why the 32 px trial failed:

| quantity | value | source |
|---|---|---|
| lane tread width | ~10 ft -> half-tread 5 px | `settlements/ways.md`: `s.lane(width=5)` at 1 px = 2 ft, i.e. 10 ft |
| plain minka footprint | 46 x 28 ft -> half-diagonal **26.9 px** | the standard farmhouse rect |
| **longest nucleated minka, as DRAWN** | up to **62.1 x 30.8 ft** -> half-diagonal **34.7 px** | `houses.py::_try_place_bundle`: length factor `[0.85, 1.35]`, depth factor `[0.90, 1.10]` |
| longest actually observed in the pool | 60.5 x 29.4 ft -> half-diagonal 33.6 px | measured on `pool/hamlets/inashiro.json`, D6 |
| plain-house blanket clearance | 26.9 + 5 = ~32 px | |
| **honest blanket clearance for the DRAWN population** | 34.7 + 5 = **~40 px** | |
| **shipped value** | **48 px** | exceeds the honest blanket by ~8 ft, not the ~16 an earlier reading suggested |

**Why the 32 px trial failed, correctly stated.** Not because the drawn rect was a different size or in a different place - D6 measures both as identical to the cleared rect, to four decimal places. It failed because **32 is the PLAIN house's figure and the nucleated path jitters a minka's length up to 1.35x**: a minka grew by adding bays along the ridge, so the generator varies length a lot and depth only a little. A 62 ft house has a 34.7 px half-diagonal, which reaches past a 32 px corridor and onto the tread. The blanket was derived from the wrong member of the population.

That is a real defect and it is worth separating from the rotation one, because they have different fixes: this one is arithmetic (derive from the longest drawn house, not the base one), and D6's is geometric (test the rotated quad).

**What this means for the fix.** Once a bundle's drawn footprint is tested against the drawn tread, a blanket worst-case margin is no longer doing correctness work: any seat that would put a corner on the tread is refused on its own geometry, whatever the constant says. The constant then answers a different and much smaller question - *how far out do we offer seats, so houses front the lane rather than crowd it* - and it should be set to that, with the tread test as the guarantee behind it.

**Deliberate departure from literal reality, recorded**: real frontages stand closer to the track than any value we will ship, because a real lane's edge is negotiated house by house and ours is a uniform corridor. We keep a corridor because it is what lets lanes be laid before the houses so the houses pack around them. The corridor is a generation convenience; the tread test is the truth claim.

**Alternatives considered**: (a) keep 48 and skip the re-derivation - rejected, it banks the correctness fix and none of the density, and leaves the village tier calibrated on compensation; (b) drop straight to 32 - rejected as premature, since 32 is the *plain*-house figure and the drawn-footprint test, not a blanket, is what makes any value safe; the number must follow the post-fix measurement.

---

## D2. What determines the pitch between homesteads - and the finding that changed the plan

**Decision**: **`BUNDLE_PITCH` is NOT re-derived downward. It stays grounded where it is, and the deliverable becomes a measurement of achieved-versus-asked pitch rather than a new number.**

This reverses what the feature description assumed, so it is worth being precise about why.

**What reality says**: the spacing between farmsteads in a nucleated wet-rice village is set by the **threshing yard's sun**, not by how tightly buildings can be packed. Rice is dried on the *niwa*, so a yard needs clear ground to its south. A thatched (*kayabuki*) roof must be pitched 45 degrees or steeper to shed rain, which puts our 46x28 ft minka's ridge about 20 ft up; at 38 degrees north in the 10th month that throws 21 ft of shadow at noon and 39 ft by 9 am. A neighbor standing inside that shadow takes the drying day away.

**Does the current value match? Yes.** From [`research/homesteads.md`](../../.claude/skills/diagram/research/homesteads.md): house depth (28) + yard depth (~26) + 39 ft of sun comes to ~93 ft, against a `BUNDLE_PITCH_FT` of 92; it was raised to 100 when the sun-corridor rule actually landed. The number is derived from the thatch pitch and the solar geometry. **It is not circle inflation.**

**So where does the circle come in?** The constant's comment conflates two different things: the pitch the generator **asks** for, and the pitch the cluster **achieves**. The collision circle inflates the achieved pitch above the asked one - *"the placer then keeps bundles apart by circumscribed circles rather than real footprints, so the effective pitch is larger again"*. Fixing item 2 closes that gap, so the cluster finally lands at the pitch that was specified. Lowering the asked value on top of that would **double-count the fix** and would put houses inside each other's drying shadow - a defect against the historical rule, arriving disguised as a density win.

**What ships instead**: measure achieved nearest-neighbor pitch across the cohort before and after item 2. If achieved was above asked and converges toward ~100 ft, that is the win, recorded. The constant's comment is corrected to separate asked from achieved and to stop implying the value is padding.

**Recorded as grounding that led to REJECTING a design change**, per Principle XII. The design that was rejected: "both constants are compensation, so re-derive both downward."

**Noted for later, out of scope**: the same research observes that real *yashiki* lots resolved the sun problem by **staggering east-west** rather than by spacing rows apart, and that the placer is free to stagger. That is a genuine future density gain that costs no sunlight - and it is the honest way to get what shrinking the pitch would only appear to give. It belongs to the village tier's own work, not here.

---

## D3. The constraint the fix must not quietly break

More legal seats is not a license for a denser hamlet than the record supports. Both fixes remove **false** refusals - ground nothing occupies - so the packing they unlock is ground that was always legally buildable. Neither fix may be allowed to relax a rule that encodes a real-world constraint (the sun corridor, the yard's clear south, the lane's trodden surface, sanctioned grove abutment). The closing bookend re-reads the four rendered PNGs specifically for a cluster that has become denser than D2's solar arithmetic permits, since the gate cannot see that: `check_village` proves internal consistency, never historical truth.

---

## D4. The measured baseline (Principle XIII)

Taken on **unmodified code** in a detached worktree - `git worktree add --detach <scratchpad>/base121 HEAD` - never a stash, so no review agent reads a mutated tree.

Commands:

```bash
python3 -m l7r.diagram.tools.cohort_audit --count 24 --seed 1   # cohort pass rate + failure histogram
make done                                                        # ruff + format + mypy --strict + pytest + coverage floor
```

**Taken 2026-08-17 at `bf7574e`, before any source change.**

- **Cohort pass rate at HEAD: 22/24** passed the whole gate.
- **`make done` at HEAD: green.** Coverage TOTAL 95% (the `settlement/` package holds a ratchet floor rather than 100%, per the freeze decision; every other module is at 100%).
- **Per-seed failure histogram** - two seeds, one check each, no check failing twice:

| seed | check | message |
|---|---|---|
| 22 | `field_ringed` | 4 houses, need 5 |
| 24 | `paddy_bunds_clear_the_supply_channels` | 1 paddy bund vertex `[611, 1732]` drawn inside a supply channel's stroke |

**These two are PRE-EXISTING and are ledgered, not fixed here.** Principle XIII is explicit that a pre-existing failure is not a regression and is not this feature's to repair under someone else's flag - which is exactly why the baseline is mandatory. If either seed's check is still failing at merge, that is the baseline holding, not a regression. If a **third** appears, it blocks.

**Known measurement artifact, recorded so nobody re-diagnoses it**: in a detached worktree `.git` is a *file* rather than a directory, so `scripts/gate-stamp.py` raises `NotADirectoryError` when it writes its green-stamp. The gate itself completes and prints `gate green`; the traceback is worktree plumbing, not a gate failure.

---

## D6. Where drawn diverges from placed - and the ledger was wrong about it

**Decision**: the divergence is **ROTATION, and only rotation**. The fix is a rotated-quad test, not a re-derivation of size or position.

**What the ledger says** (`hamletgen.md` finding 2, `dev/placement.md` item 3, and the deferral comment in `consts.py`, all in the same words): *"the house inside it is offset from the seed point AND scaled by the wealth/length jitter - so the rect the placer clears is neither the size nor the position of the rect the map draws."*

**What is actually true**, measured on the recorded artifact `pool/hamlets/inashiro.json` (15 of 15 houses carry their `geom`):

| comparison | result |
|---|---|
| `max abs(geom["house"] position - rec position)` | **0.0000 px** |
| `max abs(geom["house"] size - rec size)` | **0.0000 px** |
| `rot` range across the map | **-4.96 to +2.55 degrees** |
| **corner bulge beyond the cleared axis-aligned rect** | **2.56 px** (a 60.5 x 29.4 house at -4.96 deg) |

The size and the position agree **exactly**. Reading the code confirms why: `hw`/`hh` are computed with their wealth and length jitter *before* `_place_bundle` is called, and `_bundle_geom` is rebuilt at the final slid position `(cx, cy)`, which is then used verbatim as `rec["x"], rec["y"], rec["w"], rec["h"]`. What the record adds afterward is `"rot": self._hjit(cx, cy, 11.0) * 10.0 - 5.0`, and **`_rect_corners` returns axis-aligned corners** - so the placer clears a square-on rect and the renderer draws it raked.

**The 2.56 px bulge matches the independently-recorded symptom exactly**: *"a corner ended 2.4 px from a track's centerline while its centre stood a legal 34 px off."* Two measurements taken years apart in different ways agreeing to a quarter of a pixel is the best evidence available that this is the whole of it.

**Why this makes the fix cleaner than the ledger implied.** The rake is `_hjit(cx, cy, 11.0) * 10 - 5` - **position-seeded**, a pure function of the candidate's coordinates, deliberately so that a house's rake never ripples other placement. It is therefore fully computable *at seat time*, before anything is committed. The placer can know the exact quad it will draw without any change to when rotation is decided. There is no ordering problem here at all, which is what a "the rect is a different size and in a different place" diagnosis would have implied.

**Consequence for the tasks**: T004's helper needs the rotation and nothing else; T008 routes the bundle's solid rects through a rotated-quad tread test. No re-derivation of bundle sizing is required, and the plan does not need a stage for one.

**Recorded for correction**: the "offset AND scaled" wording is wrong in three places and gets fixed under T030 rather than repeated.

---

## D7. The gate was rake-blind too - found by the fix, not by the plan

**Decision**: `houses_clear_of_lanes` reads `rect_corners`, the rake-aware helper already imported into its own file, instead of its private axis-aligned copy.

**How it surfaced.** With the placer fixed, the cohort at a 32 px clearance went from 10 failing maps to 4 - better, but not closed. Reproducing seed 16 and asking the placer directly about the offending seat gave the decisive answer:

```
offender: (1270.3,1421.0) 60.0x29.5 rot=-2.29  HAS_GEOM=True
_house_on_a_tread(...)  = False        <- the PLACER says this seat is clear
gate                    = houses_clear_of_lanes FAILS at (1270, 1421)
```

The placer and the check disagreed about the same house. Reading the check showed why: segment 493's `_house_pts` builds `(x +/- w/2, y +/- h/2)` - **axis-aligned**, ignoring `rot` - while `rect_corners`, defined in `common_01_geometry` and imported into the very same module, has applied `h["rot"]` all along and is what the overlap checks use.

**So the defect was in both halves.** The placer cleared a square-on rect; the gate that was supposed to catch it measured a square-on rect too. A rotation moves corners around the same circumscribed circle rather than uniformly outward, so the two square-on measurements were not even wrong in the same direction - which is why the residue looked like a partial fix rather than a second bug.

**This is contract C7 violated in the field**: *"`edge_gap` is the only exact footprint-gap helper... Two CORRECT helpers for one question is how the three wrong conventions got started."* A private duplicate of `rect_corners` is exactly that, and it drifted the moment houses started being drawn raked.

**What was NOT changed, deliberately.** The house CENTRE stays in the point list beside the four corners. A lane narrower than a house can otherwise thread between two corners without touching either - the same sampling trap that once let a wellhead sit 1 px inside a hatake plot. The corners answer "does a wall overhang the tread"; the centre answers "is the house sitting astride it".

**Method note worth keeping.** The diagnosis came from asking the ENGINE about the seat (`_house_on_a_tread` on the offender's own coordinates) rather than from re-deriving the geometry beside it. A re-derivation would have produced a number and an explanation from two different expressions - the failure mode this skill has on record twice.

---

## D5. Refusal attribution, re-taken on maps that still exist

**Decision**: re-measure on the live scripted cohort; treat the historical figures as motivation, not as evidence.

**Why**: the numbers every ledger entry quotes - 71,860 `_fits` calls, **38.7%** of refusals from the circle clause alone, **767** seats refused by nothing but the approximation, **+57.6%** more legal seats, and the "+21 houses / +20 buildings / +23 wells" trial - were all measured on **Tango**, which entered `LEGACY_FROZEN_GENS` on 2026-08-16 and is never regenerated. They are no longer reproducible. A feature judged against unreproducible numbers is judged against nothing.

**Method** (the one the project already validated, and the one its own diagnostics doctrine demands): compute the diagnostic **beside** the real verdict, in one wrapper, so the map generated is the real map and the value and its provenance come from a single expression. The skill has two recorded incidents of a probe that derived its number and its explanation separately and paired a true number with a false explanation; this method is what avoids repeating that.

**What is counted**, per refusal, on the four live scripted hamlets and the 24-seed cohort:

1. refusals where the exact rotated-quad test also says no (**real** occupancy - correct refusals);
2. refusals where only the circumscribed circle says no (**approximation-only** - the waste);
3. the resulting change in the pool of legal seats.

**Success is (2) reaching zero**, with (1) unchanged. A rise in (1) means the tightened verdict has started refusing things it should not.

**Alternatives considered**: (a) trust the Tango figures - rejected, unreproducible and taken on a map with a different tier, scale and building mix; (b) unfreeze Tango to re-measure - rejected outright, the freeze exists precisely so engine work stops paying rent on deprecated compositions, and the fix for a frozen map is conversion, never retrofit.
