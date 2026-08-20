# Where the hamlet reach work stands (2026-08-20)

**Load this if you are picking up the `farmhouses_reach_a_way` work, or wondering why
`.clones/diagram-architecture` has commits that never reached main.**

## The state in one line

Every reach seed passes; the work is committed in the clone and **deliberately not pushed**, because
one caption seed is red and the fix for it belongs to another session and had not landed when this
session stopped.

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
