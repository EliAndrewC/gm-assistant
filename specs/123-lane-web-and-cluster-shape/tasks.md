# Tasks: feature 123 - the lane web

**Baseline** (detached worktree at `ae1f94d`): 24-seed cohort **24/24**, pool gate green, and
**29 of the four pool hamlets' 66 farmhouses** more than 100 ft from any way.

That 29 is the corrected figure. It was first reported as 32, measured with the house's `x, y` read
as a top-left corner; they are the CENTER, which is how `rect_corners` reads them in the gate. The
same slip was in the first draft of the new check and in `stage_web`, where it shifted every house
rect by half its own size and laid two lanes straight over farmhouses.

## Done

- [x] T001 Research recorded in `.claude/skills/diagram/research/homesteads.md` - decisive on
      access, two-formed on shape.
- [x] T002 `farmhouses_reach_a_way` (`check_village/segments_07c_*.py`), registered in
      `tests/fixtures/gate_check_names.json`.
- [x] T003 **Proved red before anything was fixed**: 10/7/7/5 houses on the four pool maps, frozen
      as negative fixtures in `pool/regressions/farmhouses_reach_a_way_fires_on_*.json`.
- [x] T004 `web_cuts` in `settlement/_knobs.py` - the pure 1-D minimal cover both forms share.
- [x] T005 The `lane_web` knob: registered, rolled in `plan_site`, recorded as `meta.lane_web`.
- [x] T006 `stage_web` in `hamletgen/ways.py`, plus `_margin_frame` (outline coordinates and their
      inverse), `clear_runs` (every clear run, two obstacle families, a floor), `_homestead_polys`
      (owner-aware), `_serve_stragglers` (the footpath to an outlying steading).
- [x] T007 `STAGES` gains `stage_web` between `stage_homesteads` and `stage_appurtenances`.
- [x] T008 Unit tests: `web_cuts` (including a 300-row randomized coverage proof), `clear_runs`,
      `_margin_frame` round-trip, `_reach`; four check tests including one that pins the
      house-center convention.
- [x] T009 Docs: `hamletgen/CLAUDE.md` (the two-stage split and why), `dev/placement.md` (the DRAW
      ORDER map gains the fill-after-placement rule), `future-work.md` section C marked implemented.

## The redesign, and why the first attempt had to be thrown away

**Attempt 1 laid the web BEFORE the houses**, with every other lane, because that is the rule in
this engine: a lane is a no-build corridor the homesteads front. It cannot work, and the reason
generalizes past this feature. A lane laid first has to reserve its ground from a cluster that has
not been packed yet, so it competes with the very houses it exists to serve:

- with a normal 40 ft corridor the placer pushed the houses outward and the four clusters' long
  axes grew **808 -> 1220, 716 -> 1131, 994 -> 1144 and 518 -> 1022 ft** (+51%, +58%, +15%, +97%).
  **No check measures sprawl**, so this would have shipped silently; it was caught only by measuring
  the clusters' principal axes by hand.
- with a 12 ft corridor the cluster stayed compact and the houses collided with the lanes instead.
- 24 ft was the best point found and was green on one map of four. That is a calibration dead end,
  not a number needing another pass.

**Attempt 2 lays the web AFTER the houses.** Placement is untouched - the clusters come out at
**810 / 717 / 993 / 511 ft** against a baseline of 808 / 716 / 994 / 518 - and the web goes in the
room that is actually left. It is also the truer account of these ways: an alley IS the residual gap
between two plots, "colonised as semi private space by the adjoining house", not a corridor set
aside in advance. `research.md` R6 had rejected this on determinism grounds; placement is
deterministic, so the objection did not survive contact.

## The dead ends, each measured, so nobody re-walks them

| what was tried | what it cost | why it failed |
|---|---|---|
| straight lanes in the seat frame | back lanes clipped to 203 ft of an intended 1,400 | a field margin CURVES; a straight lane parallel to it runs into the crop at both ends |
| outline coordinates, lanes from standoff 0 | 26 of 27 arms clipped to zero points | a lane starting ON the field edge is fouled at its first sample; it must start where buildable ground does |
| `clip_to_clear` on a web lane | Inashiro's worst house went 362 -> 591 ft | it truncates at the first blockage, right for a radiating arm, wrong for a through-lane whose two ends are just its two ends |
| the whole field ring as the web's domain | 3,060 ft of "margin" for an 808 ft cluster | the along-axis test alone admits the vertices directly opposite; the arc snaked round the fan and back |
| lanes spanning the whole cluster | 13 of 24 seeds dangling | a lane must span the houses IT serves, not the cluster |
| excluding a steading's whole bundle from its own footpath | 7 seeds `lanes` vs `gardens`, then `lanes` vs `threshing_yards` | only the house itself may step aside; the dog-leg is what finds the way out |
| `CLUSTER_SPAN_FACTOR` as the frame's span | 4 seeds, ALL `shape=crescent`, worst 431 ft | a crescent wraps past the seat band; the span is measured off the placed houses instead |

## STATE: NOT SHIPPABLE. The check is right; the engine does not yet satisfy it.

**Three independent settlement-reviews (Sawada, Inashiro, Mizuguchi, and Kashikawa afterwards) found
the same defect, none of which the gate could see: THE WEB IS NOT A WEB.** It reached the houses and
joined nothing.

- Sawada: 4 of 6 web lanes touched no other way; **7 of 19 houses were "served" by an island** whose
  nearest real lane was still 136-296 ft off - exactly where it had been before the feature.
- Inashiro: the ways came out as **three disconnected components**, with a 110 ft gap between them,
  plus a footpath unattached at BOTH ends (24 ft of grass at one, 13 ft at the other) that renders as
  a floating chevron, and one that folded back 133 ft through the windbreak, costing the shelter belt
  six clumps.
- Mizuguchi: a **38 ft mark drawn 71 ft from the house it served, touching nothing, to cure a ONE
  FOOT violation** - a caret in a field.
- Kashikawa: a 29 ft lane drawn for a house that a lane two draws earlier had already served, because
  `_serve_stragglers` snapshotted the network once per pass; and a back lane laid a median 10 ft from
  a skeleton lane for 81% of its length, which reads as one lane drawn twice.

**The reviews also caught a real regression I had missed**: the web's corridor was reserving
courtyard ground before `stage_appurtenances` ran, exiling byres and wells by up to 210 ft and
erasing feature 121's byre-service fix (worst walk 165 -> 266 ft on Mizuguchi; a byre serving 8
households moved to serve 2 on Inashiro). Fixed by moving `stage_web` after `stage_appurtenances` -
the same "reserve before, fill after" rule that put it after the houses, applied consistently.

**`farmhouses_reach_a_way` is now TRANSITIVE**, and that is the important correction. It measures to
the connected component containing the connector, not to any polyline on the ground, because the
research the whole feature rests on says "the INTERCONNECTED system of narrow lanes and alleys" - a
check satisfiable by an island rewards drawing an island. It fires on three of the four shipped maps.
**The check is correct and should stay.**

**What is unfinished is the engine.** Requiring every web lane to join the network (refusing to draw
one that cannot, snapping the ones that can, and dog-legging the footpaths) is written and in place,
but it trades one residue for another rather than converging: forcing connectivity costs coverage,
and snapping ink onto the network reopens `features_do_not_overlap` / `houses_clear_of_lanes` on the
seeds where the connecting ground is tight. Best cohort state reached with the honest check is 0 of 4
in-gate seeds fully clean; with the earlier, dishonest check it was 20 of 24 with the pool green.

**Do not "fix" this by reverting the check.** That reading was measured and rejected: the pool maps
were green under it only because an island counts.

## THE CRESCENT FINDING (still true, still separate)

**Cohort: 20/24, and the ONLY check failing anywhere is the new one.** No pre-existing check fails on
any seed, so this is not a Principle XIII regression - it is the new rule finding real defects. The
four are seeds 1, 4, 5 and 8, and all four are `shape=crescent`, which is the whole story.

**What is actually wrong on those maps.** A crescent cluster wraps AROUND the paddy, and a few of
its houses end up on the far arm - across the field from the rest of the settlement. Probed
directly on seed 8's worst house (289 ft from any way): a straight footpath from it to the network
is blocked with the settlement fabric removed entirely, and blocked with everything removed except
the crop. **It is the paddy in the way, not a neighbor's yard.** Those houses are not behind
something; they are across something, and no lane the web can lay reaches them, because the web is
built in coordinates that follow the field margin and those houses are not on it.

**Three attempts at it, all measured, none of which moved the numbers by a single foot** (203 / 227
/ 289 on seed 8 was byte-identical across all three, which is itself the diagnostic):

1. deriving the frame's span from the placed houses instead of `CLUSTER_SPAN_FACTOR`;
2. replacing the half-plane side filter with a contiguous walk along the outline;
3. letting that walk bridge a houseless stretch, on the theory that the two arms of the crescent
   were separated by margin with no houses near it.

**Why it is not being forced.** The honest reading is that this is question B wearing a different
hat. A crescent that strands houses across its own paddy is a CLUSTER-SHAPE problem, not a lane
problem - the placer is scattering steadings the shape does not really call for, and the GM's
ruling B (the drawing must match the rolled knob) is exactly the work that would address it. Adding
a special case here to drag a path around the paddy would paper over that, and would be a lane rule
compensating for a placement defect - which is the shape of bug this project has spent two features
removing.

**Priced and declined**: waiving the check on crescent maps (rejected - a waiver says "this map may
break the rule", and the map should not); relaxing the threshold to the distance those houses happen
to sit at (rejected outright as goalpost-moving); measuring reach from the house's wall rather than
its center (rejected - it is arguably the better measurement, but it moves these houses by only ~31
ft and would be adopted for the wrong reason).

**So it is ledgered**: the pool's four maps are green, the rule ships, and the four crescent seeds
are a known, diagnosed, reproducible finding for the `cluster_shape` feature to pick up.

## Not done, and deliberately

- [ ] **US3 / GM ruling B - honor the rolled `cluster_shape`.** Untouched. `stage_homesteads` still
      seats by rows and frontage and records `meta.cluster_seeding`, which states in writing that
      the rolled knob went unhonored. This is the PRE-EXISTING state the ruling calls out, not
      something this feature introduced, and it is a placer change of its own size. Its own feature.
