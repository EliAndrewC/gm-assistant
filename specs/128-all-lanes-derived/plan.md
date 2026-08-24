# Implementation Plan: Farmhouses Before Lanes

**Spec**: [spec.md](spec.md) - APPROVED, `spec-fidelity` FAITHFUL at round 2.
**Request**: [gm-request.md](gm-request.md) - verbatim. Not to be edited.

## Summary

    water, fields, drainage  ->  FARMHOUSES  ->  every lane, without exception

`stage_ways` runs at position 4 today and does TWO jobs. Splitting them is the whole feature.

## The one fact that made 126 unable to just reorder this

**`stage_ways` both SEATS the cluster and DRAWS the ways.** `seat_cluster()` sets `plan.seat`, and
`stage_homesteads` reads `seat["along"]`, `seat["anchor"]`, `seat["lat"]`, `seat["dep"]` on its first
lines (`homesteads.py:33-48`). So moving `stage_ways` wholesale after the houses is impossible - the
houses cannot be placed without it. Feature 126 hit this and worked around it by moving only the
skeleton, leaving the connector and spur where they were.

So: **split the stage, do not move it.**

| new stage | what it does | position |
|---|---|---|
| `stage_seat` | `seat_cluster()` -> `plan.seat`; builds `plan.watercourses`. Draws NOTHING. | 4, where `stage_ways` is now |
| `stage_track` | draws the connector and the field spur, both branches | after `stage_appurtenances`, before `stage_web` |

**`stage_track` is the name the code already expects.** `ways.py:377` carries a comment reading "the
connector out to the road, which `stage_track` has already drawn" - written by feature 126 for a
rename it planned (T008) and never did. The comment has been describing a function that does not
exist. This feature makes it true.

**Why `stage_track` goes before `stage_web` and not after**: `_lay_skeleton` reads `_net_segs` as the
network that already exists, and its comment says "at this moment `_net_segs` holds only the connector
and the field spur". The web threads around them. That relationship is unchanged by this feature.

## Technical Context

**Language/Version**: Python 3.14. **Testing**: pytest; `check_village` is the oracle.
**Primary change surface**: `hamletgen/ways.py`, `hamletgen/driver.py`, one new gate segment.

**Single-artifact target** (constitution VI): `pool/hamlets/inashiro.gen.py`, the reference hamlet,
seed 4. Rebuild ~24 s. **Every step is two steps** - reference settlement first, then the pool - and
the pool half is a task of its own, not an afterthought.

**Performance bookends**: `128-start` TAKEN (2026-08-24, before the first edit, total 394 s / median
73 s). `128-end` is taken by `make perf-gate` as a phase of `make done FULL=1`, which now REFUSES to
ship a feature whose `-start` is missing. This feature is the first to run under that.

## Constitution Check

- **I, II, VII, VIII, IX, XI**: no UI, no pool conventions, no generated in-world prose, no kanji. N/A.
- **III**: the reference map's manifest changes; no new pool data conventions.
- **IV, V**: no GM source touched. `gm-request.md` is a verbatim transcript and is not edited.
- **VI**: verification per task; reference first, then the pool; bookends both present.
- **X**: new Python is `mypy --strict` and 100% covered; the new check is a `check_village` segment.
- **XII**: the research question this feature COULD have asked - do field paths predate settlements -
  was raised in round 1 and settled the right way: the answer does not matter, because the reason
  carrying the change is ground reservation, not provenance. Recorded in the spec.
- **XIII**: baseline is the green gate at the pre-128 commit (3453 passed). Any failure the reorder
  produces is a regression, not a pre-existing.
- **XIV**: defects found in passing are fixed here.
- **XV**: no stopping points planned.
- **XVI**: spec reviewed, FAITHFUL at round 2. **Any exception discovered during implementation goes
  back to `spec-fidelity` in Mode 1 BEFORE it is written.** The connector rule especially: four
  carve-outs for that one way across two features is the base rate to assume about this author.
- **XVIII**: any new guard ships with its test companion, which `make hooks-test` runs.

**Gate: PASS.**

## Design

### 1. Split `stage_ways` (both branches)

`stage_seat` keeps: the drain lookup, `plan.watercourses`, `seat_cluster()`, the windward
reconciliation. It calls `s.lane` NOWHERE.

`stage_track` takes: the polder connector (`ways.py:1499` branch) and the valley connector + spur
(`1535`, `1555`). **Both branches, or polder hamlets keep reserving ground and the reference hamlet -
a valley map - never notices.** That is the fidelity review's finding and it is the most likely way
this feature ships half-done.

### 2. Derive each way from the placed houses (FR-002)

Today the connector's gateway comes from `skeleton_layout(plan.lane_skeleton, 0, 0, seat["lat"],
seat["dep"])` - the PREDICTED band - and the spur starts at the band's center point `to_screen((0,0))`.

Once `stage_track` runs after the houses, both take their origin from the placed cluster: the same
arc/stand extent `_lay_skeleton` already computes from `s.M["houses"]`. `skeleton_layout` is not
called before the houses exist (FR-002 is explicit), which is checkable by grep and by test.

### 3. The check (FR-003)

A `check_village` segment asserting no house center lies in a lane corridor or on a tread. Under the
new order it passes by construction - which is exactly what makes it a REGRESSION guard: it fails the
moment anything reintroduces a lane ahead of `stage_homesteads`. 126 regressed silently because
nothing measured this.

### 4. The walk-through page (FR-005)

`tools/placement_stages.py` re-plates and its captions are edited to match. **The captions are the
deliverable, not the plates**: a stale caption on this page is what made this feature necessary, and
plate 05 said the opposite of what the code did for five days.

## Project Structure

```
.claude/skills/diagram/l7r/diagram/
├── hamletgen/ways.py          stage_ways -> stage_seat + stage_track
├── hamletgen/driver.py        STAGES tuple AND its comment block (the DRAW ORDER authority)
├── check_village/segments_07c_moats_drains_and_edges.py   + the no-house-on-a-lane check
└── tools/placement_stages.py  captions

specs/126-derived-lanes-and-form/spec.md    FR-003 marked superseded
```

## Complexity Tracking

| concern | why accepted |
|---|---|
| Splitting a stage rather than moving it | The only option: `plan.seat` is a hard dependency of `stage_homesteads`. Moving wholesale is impossible, which is why 126 did not. |
| Two code paths for the connector | Inherent - the polder branch returns early. Named in FR-001 so it cannot be forgotten. |
| A check that passes by construction | Its value is as a regression guard, and 126 is the evidence that one was needed. |
