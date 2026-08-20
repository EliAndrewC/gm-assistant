# Where the hamlet reach work stands (2026-08-20)

**Load this if you are picking up the `farmhouses_reach_a_way` work, or wondering why
`.clones/diagram-architecture` has commits that never reached main.**

## The state in one line

Every reach seed passes, and all of it is **in main** (`38cb0c7`) at the GM's explicit instruction to
push even half-finished so the next session works from a common baseline. One caption seed is red and
its fix belongs to another session - that is the named regression the push waives, described below.

## What is DONE and committed (clone only, not in main)

Cohort **45/48** measured through the shipped path, with **zero `farmhouses_reach_a_way` failures** -
seeds 5, 8 and 25 all pass. That defect had survived seventeen prior attempts, all recorded in
[`future-work.md`](../future-work.md) 2b.

Four changes, and the GM's question about placement ORDER produced all of them:

1. **The skeleton follows the margin** (`hamletgen/ways.py`, `stage_ways`). It was mapped through
   `to_screen`, a LINEAR map through the seat band's fixed axes, so a "spine along the margin" came
   out as a straight chord: on a bent margin it leaves the margin and the far arm of the cluster gets
   no lane at all. `_margin_frame` exists for exactly this and says so in its own docstring; the lane
   web already obeyed it. Fixes seeds 8 and 25.
2. **`_pull_back` stops manufacturing the defect it cleans up** (`settlement/water_ways.py`). With no
   reaching end found it returned the floor-truncated run, whose end reaches nothing BY CONSTRUCTION.
   Seed 26: an end reaching a way at 31 ft and a house at 46 ft was pulled back to 59 ft / 156 ft.
3. **A map that strands a farmhouse is re-rolled with that ground forbidden** (`hamletgen/driver.py`
   `generate`, `hamletgen/homesteads.py` `_seat_allowed`, `settlement/rolling/place.py`). Scored by
   the GATE and steered by the coordinates the gate itself names. Seed 5 converges in two rounds. The
   avoid test applies to where the bundle ENDS UP, not the seat it started from - the slides move it,
   and testing the seed position let a house re-seat on identical ground three rounds running.
4. **`cohort_audit` calls `generate`, not `build`** (`tools/cohort_audit.py`, `Report.fail_lines`).
   The audit had been measuring a different code path from every shipped map, so a fix living in
   `generate` was invisible to it. **Every cohort number either session quoted before this fix was
   answering a slightly different question than we thought.**

Tests cover the re-roll loop, the "a re-roll that does not help is not kept" guard, and the seat gate.

## STATUS: PUSHED, at the GM's explicit instruction

The GM asked for this to go to main even if half-finished, so the next session works from a common
baseline rather than from a clone nobody else can see. That is the one sanctioned exit from Principle
XIII's no-regressions rule - an explicit waiver for a specific, named regression - and the regression
it waives is seed 37's caption, described below.

**The hamlets session's box-edges fix has since LANDED (`d2225c44`)**, so seed 37 may already be clear;
the cohort was re-run at push time and the number is in the push commit. If you are reading this later,
trust the cohort over this paragraph.

## THE LAST THING THAT LANDED: the re-roll was emitting invalid SVG

Read this before you touch `generate` in `hamletgen/driver.py`.

`finish()` MUTATES - it splices the shared water block into the record stream. The retry loop added
in this session finished a candidate settlement into a scratch directory in order to GATE it, then
let `generate` finish the SAME object again for real. Kashikawa came out with 436 group opens against
437 closes: the extra close ended the `<svg>` root early, `resvg` refused the file outright, and
render-sync could not draw the map at all.

Each roll now finishes exactly ONCE, straight to its final destination when it has one. A keeper that
was displaced by a rejected re-roll is put back by REBUILDING it - generation is deterministic, so
that reproduces it exactly - and that re-emit writes files only, keeping the verdict already chosen,
because taking the re-gate's answer would let a second opinion overwrite the selected one.

**The gate was green through all of this.** A malformed SVG passes every check that reads the
MANIFEST, and nothing in the suite looked at the emitted file until this was found by render-sync
failing at push time. `tests/hamletgen/test_driver.py` now asserts the emitted SVG has exactly one
`<svg>` root and balanced groups, so this specific shape cannot come back silently - but the general
hole is worth remembering: **the manifest is not the artifact.**

## SEED 37 IS STILL RED AFTER THE BOX-EDGES FIX - and that is itself a finding

Measured after pulling `d2225c44` and re-rolling all four pool hamlets from the merged engine:
**cohort 44/48**, and `captions_clear_the_ways_they_stand_on` still fails on seed 37.

The hamlets session's own reasoning was that a SECOND failure would mean the cause is neither of the
two things they fixed - not the corner sampling (a caption spanning a concave bend having all five
sample points clear while its middle edge crosses the arc) and not the box asymmetry (the sampled box
being symmetric +/-5 about the anchor while a caption runs from ascent 0.80 above to descender 0.25
below). So both of those are now ruled out by measurement, which is worth as much as a fix.

**Two hypotheses I did not get to test**, offered as questions since it is their code:

1. **Is it even the same caption?** If the board moved between runs, this may be a different board
   failing for a different reason, and "still red" would be misleading. Confirm the COORDINATE, not
   the seed. (Seed 37 is `shape=crescent lanes=T`, 16 households, fall 45, sink offmap. Before the
   fix it failed at (368, 1928) with a 5 ft lane.)
2. **Does the measure handle a tread curving around a caption on MORE THAN ONE side?** The edges fix
   answers a tread crossing one edge of the box. On a T skeleton whose arms now both follow the
   margin, a caption can sit in the crotch with tread on two sides - and then the
   least-distance-to-any-edge answer is CORRECT while the seat is simply bad, which puts it back in
   `place_kosatsuba`'s ranking rather than in the clearance measure.

Also note **seed 24 now fails `village_groves_visibly_stocked`**, the hamlets session's new gate 0618.
That is a new check finding a new instance rather than a regression, but it was not in the cohort they
last quoted and belongs on someone's list.

## THE REGRESSION THIS WAS PUSHED WITH

`captions_clear_the_ways_they_stand_on` fails on **cohort seed 37** at (368, 1928). It passes on the
hamlets session's tree and fails only here, because this branch's treads are CURVED and theirs are
not: `caption_lane_clearance` sampled the caption box's four corners plus its centre against each lane
segment, and a caption spanning a concave bend can have all five samples clear while its middle edge
crosses the arc.

That is their code. They diagnosed it, wrote the fix (measure the tread against the whole caption
RECTANGLE - zero if the tread enters the box, else the least distance to any of its four EDGES), and
asked for the failure back rather than have it worked around here. **Their fix was in verification and
not pushed when this session stopped.** They also flagged a second discrepancy in the same method: the
sampled box was symmetric +/-5 about the anchor, while a caption actually runs from ascent (0.80 x
size) above to descender (0.25 x size) below - which matters exactly when a tread curves above a
caption.

They cannot verify their own fix: seed 37 passes on their tree, so their cohort can only show they
broke nothing. **Only this branch can close it.**

## To resume

1. `git pull` in the clone and check whether the caption fix has landed (look for the box-EDGES
   measure in `caption_lane_clearance`).
2. Re-run `python3 -m l7r.diagram.tools.cohort_audit --count 48`. Expect **46/48 or better**, with the
   residue being seeds 12 and 39 (`paddy_bunds_do_not_stagger`), which are the Inashiro session's and
   are deliberately batched behind a GM ruling.
3. If seed 37 is still red, send the coordinates back to the hamlets session rather than assuming they
   aimed at the wrong thing - a second failure would mean the cause is neither the corner sampling nor
   the box asymmetry.
4. Then: `make done`, regenerate the four pool hamlets, run `settlement-review` on them (the skeleton
   change moves every scripted map, so this is a real review, not a formality), and push.

## The thing worth carrying out of this whole run

[`dev/gate.md`](gate.md) "MEASURE WHAT THE RULE MEASURES" - nine defects across three sessions in two
days, every one a correct measurement of a DIFFERENT QUANTITY than the rule it served. Centerline vs
tread edge, axis-aligned box vs rotated quad, a hand-rolled reach proxy vs the gate, net bearing change
vs accumulated turn, `build()` vs the shipped `generate()`. Four claims of this session's own were
retracted for it, including one - "the ground admits no servable arrangement" - that had declared the
whole problem impossible and was wrong.

Every one was caught the same way: run the instrument against the oracle, or against a case whose
answer is known. None was caught by reading the code more carefully.
