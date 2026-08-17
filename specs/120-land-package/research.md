# Phase 0 Research: feature 120

Every question this feature had to settle, and what settled it. Findings that were already known
from the lineage are recorded as such rather than re-derived, because re-deriving them is the cost
this file exists to avoid.

## R1 - Is `land.py` a CHAIN or a RESIDUE BUCKET? (it decides the partition axis)

**Finding: a residue bucket.** This is the first question every split in this lineage has to answer,
because it picks the axis. Feature 118 found `rolling.py` was a CHAIN - roll a village, generate
seats, shape a bundle, test it, place it, draw it - so its six modules are the chain's links in
order. Features 114 and 115 found `structures.py` and `civic_grounds.py` were residue buckets, so
theirs are grouped by what a session comes to change.

`land.py` is emphatically the second kind. Its 14 members cover four subjects that share no data
flow at all:

- a polder **perimeter dike** and the village on its crest
- **wet ground**: marsh, the contour band that sites it, the way-trim
- **dry cover**: the scrub scatter, the layout that lays it, the swept verge it skips
- **near-ring farmland**: two tilers for the ground outside a town wall

Plus three farmstead helpers with no land-surface content whatever. The only cross-subject call in
the whole file is `hinterland` reaching `toe_band` and `marsh` - one edge, in one direction. A chain
would have a path through most of the members; this has four islands and one bridge.

**Where the bucket came from**: feature 025 cut the 16,016-line `settlement.py` positionally. The
adjacency in `land.py` is where the knife fell, not a design.

## R2 - Does clause 12 (function size) require anything here?

**Finding: no, and saying so precisely matters.** The GM's instruction named "function and file
size", so the function half was measured rather than assumed. Clause 12 measures LOGIC UNITS, never
raw lines, so the measurement is an AST statement count:

| member | raw lines | statements |
|---|---|---|
| `near_ring_paddy` | 191 | 126 |
| `perimeter_dike` | 155 | 101 |
| `commons` | 168 | 71 |
| `near_ring_cropland` | 147 | 70 |
| `dike_top_houses` | 87 | 53 |
| `hinterland` | 136 | 51 |
| `marsh` | 93 | 48 |
| `_clear_ground` | 50 | 29 |
| everything else | <= 44 | <= 22 |

Clause 12's "suspect" line is *a few hundred* statements and its defect line is *roughly 1,000*. The
worst member here is 126, so nothing is even close. The clause also explicitly REJECTS the
10-line-function dogma and says a deep-but-cohesive engine function is legitimate at a scale a
utility function never is - which is exactly what `near_ring_paddy` is.

**So decomposing any body here would be acting against the constitution, not for it**, and would
also destroy the byte-identity oracle that makes the rest of this feature provably safe. Recorded
because "over a thousand lines" in the request could be read as licensing it.

## R3 - Where do the three farmstead helpers belong?

**Finding: `homestead_parts.py`, and the callee census is what proves it.**

| member | what it calls | where that lives |
|---|---|---|
| `_attach_grove` | `_draw_grove` | homestead_parts.py |
| `_find_appurtenances` | `_find_yard_spot`, `_farm_shed_rect`, `_find_garden_spot` | homestead_parts.py (all three) |
| `_farmstead_nudges` | nothing; the homestead solver is its only caller | - |

Four of four callees are in one sibling file whose stated subject is "the parts of a homestead that
are not the house". These three were never land surfaces.

**The alternative considered and rejected**: a 27-line `land/nudges.py`. It would satisfy clause 13
arithmetically while preserving the accident that caused the problem, and clause 13 warns in its own
text that over-fragmentation damages design more than length does. A module whose honest one-line
description is "three helpers that belong somewhere else" teaches a future reader nothing.

**The cost, stated**: `homestead_parts.py` grows 756 -> 786 raw lines, still well under the clause 13
line, and gains one import name (`Iterator`).

**Risk check**: both mixins are bases of the same `Settlement`, so moving a member between them
changes no call site and no MRO resolution (no name collides - the guard asserts it). Byte-identity
confirmed it empirically.

## R4 - Where does `surface_water_dist` go, and what does it break?

**Finding: `wet.py`, with `_geom/` priced and declined.**

It is the file's one MODULE-LEVEL member, defined after `class LandMixin` ends. Three consumers
import it from the `settlement` package surface, never from `land` directly:

- `hamletgen/homesteads.py`
- `check_village/segments_04_homesteads.py`
- `tests/settlement/test_core.py`

So as long as `land/__init__.py` re-exports it, `settlement/__init__.py`'s existing line keeps
working and no consumer changes.

**`_geom/` was the serious alternative.** It already holds the shared placer-and-check manifest
predicates (`way_beds`, `lane_through_gate`), and `_geom/village.py` is a 29-line precedent for a
small pure-manifest module. Declined because it buys nothing under clause 13 (17 lines), and it
would move the monkeypatch path twice in one feature. Recorded in spec.md's Out of Scope so it is
not reopened from scratch.

**What it DOES change**: the monkeypatch path is now
`settlement.land.wet.surface_water_dist`, one level deeper - the same shift feature 117 documented
for `_geom`. The package `CLAUDE.md` says so explicitly. No test in the suite patches it (the
consumer census confirms), so nothing needed updating.

## R5 - The transformer's three novel hazards

The slicing rule is inherited and unchanged (slice from the PREVIOUS member's end so decorators,
blank lines and comment banks travel with their member). Three things were genuinely new:

1. **A module-level TAIL.** Every predecessor split a file that ended with its class.
   `surface_water_dist` sits after it, so a class-body-only transformer drops it in silence and
   breaks three consumers at import. The transformer captures the tail explicitly and refuses if it
   does not contain the expected definition.
2. **Members leaving the package.** The relative-import rewrite (`from ._geom` -> `from .._geom`)
   must apply to the `land/` blocks ONLY - the relocated three stay at `settlement/` depth, and
   deepening them would point at a package that does not exist. Feature 113 hit exactly that class
   of bug with a lazy in-body import.
3. **A cross-module comment reference.** `marsh`'s bucketed-blades note says "see the note in
   `commons`" and the two now live in different modules. Re-pointed, and the rewrite is ASSERTED to
   fire exactly once - a silently-missed rewrite is the failure mode, since nothing downstream reads
   a comment. The other candidate (`hinterland`'s "see the comment at the marsh block") needed no
   change: that comment sits inside `hinterland`'s own `if marsh:` block and travels with it.

## R6 - Comment conservation, measured

Old `land.py`: **158** comment lines. New `land/*.py`: **158**. Delta in `homestead_parts.py`: **0**
(the three relocated members carry no standalone comment lines). Conserved exactly, so no researched
grounding was lost - the wei-tian dike sourcing, the sluice-gap ruling, the alluvial-fan toe
correction and the inward-only-bay argument all moved intact.

This is measured rather than asserted because a "pure move" that drops a why-comment is not pure,
and comments are the one thing no downstream test can notice.

## R7 - Verification strategy, and why no `settlement-review`

The oracle is **byte-identity over all 893 pool artifacts**, taken with `--no-cache --frozen-ok`
from a scratch copy at the pre-change commit and again after.

- `--frozen-ok` is REQUIRED. Without it the 19 frozen legacy maps print `FROZEN` and skip, and they
  are precisely the maps that exercise this file's headline members: `perimeter_dike`,
  `dike_top_houses` and `near_ring_paddy` are polder and city-tier features the scripted hamlet
  cohort barely touches. The sweep confirmed 28 maps REGENERATED and 0 CACHED, so the work was
  really done.
- **Read the LOG, not only the diff** (the trap feature 116 recorded): the scratch copy's unwritten
  files are the COPIED ones, which hash equal to a baseline that faithfully reproduced them, so a
  sweep that died early prints an empty diff and proves nothing. Regenerate count checked.
- The committed pool artifacts are NOT a valid baseline - they were produced by whatever engine
  shipped them, and the frozen ones deliberately predate current rules. Baseline captured by
  regeneration.
- **No `settlement-review` pass.** That agent judges what a green gate structurally cannot: glyph
  legibility, feature form, whether a map reads as a place. A byte-identical pool has no such
  residue - the maps are the same files. Feature 118 established this for the same reason, and
  feature 025's SeatMemo work states the general principle: an output-preserving change makes
  byte-identity a soundness oracle rather than a judgment call.

## R8 - Baseline hygiene, learned the hard way in this session

Two things went wrong while taking the baseline, both cheap and both worth recording:

1. **A bare copy of `.claude/skills/diagram/` cannot run `make done`.** The Makefile's lint phase
   shells out to `../../../scripts/check-duplicate-defs.py`, which only resolves when the skill dir
   sits inside the repo. The first baseline attempt reported `GATE FAILED: lint` for that reason
   alone, with every other phase green. **The scratch copy is for the SWEEP; the gate baseline is
   taken in the clone.**
2. **A baseline is only a baseline for the commit it was measured at.** Main moved under this clone
   mid-feature (a peer session pushed a `waterfields/frame.py` change), which invalidated the first
   baseline entirely. Re-taken at `56f6dfb` after sync-in, and that is the commit both halves of the
   oracle refer to.
