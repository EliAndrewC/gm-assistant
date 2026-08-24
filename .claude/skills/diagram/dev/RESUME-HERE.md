# Where feature 126 stands (2026-08-24)

**Load this if you are picking up the derived-lanes work, or wondering why the cohort ships red.**

## The state in one line

The ORDERING CHANGE IS DONE and all four pool hamlets are clean; the cohort ships at roughly 39/48
against a 44/48 baseline, **by an explicit GM waiver** (2026-08-24: *"literally just get the
reference settlement to 100% of checks passing and then push to main even if other maps and seeds
aren't working, just to get to a good stopping point"*).

## What changed, and why it was worth doing

Lanes used to be laid BEFORE the houses, and the houses were seated by fronting them. That is
backwards for an accretive settlement - a lane between farmsteads is trodden by the households who
already live there - and it was measurably expensive: the skeleton was sized on the seat band while
the houses spread wider, which is the root of the `farmhouses_reach_a_way` defect that survived
seventeen recorded attempts.

Now: **ways split by PROVENANCE.** The connector and the field spur genuinely predate the settlement
and are still laid first. The internal skeleton and the lane web are derived from where the houses
actually landed. Measured with straggler rescue disabled, so the derivation is judged alone, it
reaches MORE houses than HEAD on every seed tested: 14->6, 12->7, 8->7, 1->0.

`settlement_form` is a rolled knob (nucleated / dispersed / linear), currently **pinned to
nucleated** - see `SETTLEMENT_FORMS` in `hamletgen/consts.py` for the four measured blockers in the
per-house grove path and the exact tuple to restore.

## THE RESIDUE, and which of it is yours

| seed | check | whose |
|---|---|---|
| 8 | `farmhouses_reach_a_way` | this feature's |
| 18 | `lane_ends_front_different_houses` | this feature's |
| 23 | `village_windbreak_is_continuous` | this feature's - **read the note below first** |
| 42 | `lanes_reach_something` | this feature's |
| 47 | `lanes_reach_something`, `no_structure_on_channel` | this feature's |
| 12, 39 | `paddy_bunds_do_not_stagger` | PRE-EXISTING at HEAD, never mine |

Every one was checked against HEAD individually. Do not assume a failing seed is yours - seed 27's
caption failure sat in my regression count for a day before I measured it and found HEAD fails it too.

## SEED 23 IS A DESIGN LIMITATION, NOT A TUNING PROBLEM

Three attempts rotated it rather than fixing it. This is written down to stop a fourth.

The belt's footprint is derived PER COLUMN along the across-wind axis: each column stands off the
windward-most house near it. The obstruction is a two-dimensional FOOTPRINT - a whole steading, house
plus threshing yard plus gardens plus shed - and `village_grove` correctly skips every clump landing
on any of it. So clearing one column pushes the band onto whatever sits behind, and the hole MOVES.

Measured:

- seeds 33 and 37: holes of 78 and 84 ft, each with a whole homestead inside (house 57 ft from the
  hole centre, threshing yard 38-41, gardens 10-46). Fixed by widening the column's window to a full
  column each side, so a column clears its NEIGHBOURHOOD's windward-most house.
- seed 23: that same fix pushed its hole from 39+66 ft to **216 ft** - the band now straddles a
  different steading. Same defect, relocated.

**Two dead ends, do not repeat them.** Sampling the profile at 45 px per column instead of 90 rotated
the cohort failures (at 90: seeds 23/27/33/37; at 45: 22/23/28/39/46 - three closed, four opened,
total up). And the check ALREADY excludes the belt's ends by one clump radius, so "the gap is past
the end" is not the explanation; I checked.

**What would actually work**: derive the band from the cluster's OUTLINE rather than from per-column
frontrunners. Real design work, and its own feature.

## What was fixed, all structural rather than tuned

Several repaired bugs OLDER than this feature:

- **A caption seat is tested against the ways.** `label_blockers` walks the manifest for records with
  x/y/w/h; a lane is a polyline of `pts`, so no caption had ever been tested against a lane tread
  while `captions_clear_the_ways_they_stand_on` measures exactly that. Closed seeds 34, 35 AND 27
  (which fails at HEAD); the cohort jumped 32 -> 39 on this one change.
- **What gets DRAWN is clipped, not merely planned around.** Routing an arm round the fabric is a
  plan, and a plan can start inside a wall. Closed seeds 7, 19, 26, 41.
- **A copse records its PLANTED extent**, not the bounding box it asked for.
- **Bridges dedupe by place** - a crossing is a place, not a per-way entitlement.
- **gencache evicts a stale PNG** instead of skipping it. It had been blessing the previous roll's
  image as the new key's output, and three settlement-reviews judged the wrong picture.
- **Belt columns clear their neighbourhood** (closed 33, 37).
- **Two-point arms must serve at both ends** - the trim's `len(out) > 2` floor let a single-segment
  arm keep a dangling end.

## The tooling that came out of this

- **Three tiers**: reference map (~60 s) -> tripwire (~3 min) -> cohort (~25 min). `make maps` picks
  its own scope from how the last run went.
- **`cohort_audit` REFUSES to run while the reference settlement is red** (`--anyway` overrides).
  It exists because `make maps` gated on the reference and I ran `cohort_audit` directly six times in
  one sitting anyway - about two hours re-learning that a known-broken tree was broken. A guard on one
  door is not a guard.
- **Tripwire seeds chosen by measurement** (27, 33, 37, 41, 47 each failed 3 of 3 broken runs). Note
  the finding that motivated them: **Inashiro's own seed caught 0 of 3.** A good fix TARGET is not
  automatically a good DETECTOR.
- **Performance bookends** (`make perf`), one file per snapshot under `dev/perf-log/`.

## To resume

1. `make maps` - reference map first, widening only if it is clean.
2. Work ONE seed at a time from the residue table; each rebuilds in about a minute:
   `hg.generate(HamletSpec(name=f"Audit-{seed}", seed=seed, households=10 + (seed * 7) % 11), out_base=None, render=False)`
3. Earn the cohort once, at the end, as a closing check.
4. The method that worked, after roughly a dozen failed hypotheses: **measure the artifact, not the
   code path.** Ask WHICH lane and WHICH stage. Reasoning about which pass was probably responsible
   failed nearly every time; one probe printing the offending feature's kind and provenance found it
   first try, repeatedly.
