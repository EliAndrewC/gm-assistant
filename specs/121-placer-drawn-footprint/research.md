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

**The honest arithmetic**, at hamlet scale (1 px = 1 ft):

| quantity | value | source |
|---|---|---|
| lane tread width | ~10 ft -> half-tread 5 px | `settlements/ways.md`: `s.lane(width=5)` at 1 px = 2 ft, i.e. 10 ft |
| plain minka footprint | 46 x 28 ft -> half-diagonal **26.9 px** | the standard farmhouse rect |
| wealthy minka, as DRAWN | ~61 x 37 ft -> half-diagonal **~35.6 px** | the wealth render scale, per `consts.py`'s frontage note |
| plain-house blanket clearance | 26.9 + 5 = **~32 px** | |
| worst-case (wealthy) blanket clearance | 35.6 + 5 = **~41 px** | |
| **shipped value** | **48 px** | exceeds even the worst case by ~7 ft |

The 32 px that was tried on 2026-08-12 and reverted is exactly the plain-house blanket figure - it failed not because it was wrong about lanes but because the bundle path never tested the drawn rect at all, so the wealthy steadings it did not model walked onto the tread.

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
