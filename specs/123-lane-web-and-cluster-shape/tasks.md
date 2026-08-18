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

## STATE: the check is honest and the engine satisfies it

**Four settlement-reviews found the same defect the gate could not see: THE WEB WAS NOT A WEB.** It
reached the houses and joined nothing - Sawada 4 of 6 lanes touching no other way and 7 of 19 houses
"served" by an island; Inashiro three components with a 110 ft gap, a footpath unattached at both
ends, and another folded 133 ft through the windbreak; Mizuguchi a 38 ft mark drawn 71 ft from its
house, touching nothing, to cure a one-foot violation; Kashikawa a redundant path traced to a
per-pass network snapshot, and a back lane laid a median 10 ft from a skeleton lane.

So the check was made TRANSITIVE - it measures each house to the connected component containing the
connector, not to any polyline on the ground, because the research says "the INTERCONNECTED system of
narrow lanes and alleys" and a check an island can satisfy rewards drawing an island. It fired on
three of the four shipped maps. **In-gate cohort is now 4 of 4 under the honest check.**

### What the rebuild changed, and why each was necessary

| change | the evidence that forced it |
|---|---|
| the `back_lane` form gained CROSS-TIES | **parallel lanes never meet** - that is arithmetic, and it is why the back-lane form came out as separate components while alleys did not. The source describes the planned form as back lanes "which, together with the main street itself, provides a rectangular FRAMEWORK". We were drawing only the parallels |
| connectivity decided over CANDIDATES, before any ink | a lane once drawn cannot be taken back, so judging each run as it was drawn refused runs merely for being early in the loop and admitted islands that happened to be laid first |
| orphaned EXISTING ways are linked too | the transitive check exposed a PRE-EXISTING defect: on a cohort hamlet the skeleton's own arms were clipped apart from the arm the connector leaves by, so every house they served counted as unreached. Fixed here rather than ledgered, per Principle XIV |
| a real lattice ROUTER replaced straight-plus-dog-leg | once everything else was fixed, every remaining unreachable house was `hard-clear` and `fabric-blocked` - the paddy was not in the way, other people's yards were. That is a routing problem and wants a router |
| diagonals may not cut a blocked corner | the classic grid-routing bug, and the last one standing: the planner "found" routes that were not walkable, so they failed their own acceptance a moment later |
| string-pull validates at the clearance it PLANNED with | validating shortcuts more strictly than the route was planned refused every shortcut and left a chain of lattice steps |
| `stage_web` moved AFTER `stage_appurtenances` | the reviews caught a real regression: the web's corridor reserved courtyard ground first and exiled byres up to 210 ft, erasing feature 121's byre-service fix |
| `MIN_WEB_GAP` derived from `WEB_FABRIC_GAP` | they contradicted - the cut solver offered 16 ft gaps a 9 ft margin needed 18 ft to thread |
| the crop margin cut from a copied 20 ft to 8 | 20 was never a rule; `fields_clear_of_road` allows w/2 + 2, about 3.5 ft for a 3 px tread. The copied default closed a corridor between crop, toe and marsh that no single one of them blocked |
| ground cover is not fabric | counting the grazing commons as an obstacle walled an outlying steading in behind its own commons |
| a footpath may cross a ditch | `stage_crossings` decks it, exactly as it already does for the spur and the connector |
| wells use their DRAWN radius (`vr`), not `r` | the obstacle was a diamond inside the glyph, and a lane clipped a wellhead |

### The second review round - what it confirmed, and the six defects it found

All four maps were re-rolled and handed back to the same reviewers with their own findings quoted.
**Every prior finding was confirmed fixed by independent measurement**, not by assertion:

- **connectivity**: each reviewer rebuilt the component graph from the manifest themselves. One
  component per map, and the joins measure **0.0 ft** - not "within tolerance", touching.
- **the byre/well regression**: byres and wells are **byte-identical to the pre-web manifest**,
  coordinate for coordinate, on all four maps. Three reviewers checked this independently against
  the git baseline. The stage reorder is exact, not approximate.
- **access**: Sawada median 91 -> 45 ft and max 268 -> 83; Inashiro max 229 -> 66; Mizuguchi median
  97.6 -> 44.1 with houses within 60 ft going 3/12 -> 8/12; Kashikawa median 82 -> 42, max 323 -> 93.
- **the caret, the unattached ends, the fold, the duplicated back lane**: all gone.

**Six new defects, all found by review and none visible to the gate:**

| found | cause | fixed by |
|---|---|---|
| a 158-178 deg **hairpin** on all four maps | the snap measured the run's two ENDS, so a run whose BODY had already arrived got a perpendicular drawn back to it | measure nearest approach over the WHOLE run; if it already arrives, do not snap, and trim the short tail |
| a back lane crossing the connector mid-run and sharing its corridor for 91% of its length | the shadow test used `MIN_WEB_GAP` (18 ft) - what a lane can squeeze THROUGH, not what a reader can separate | a `WEB_SHADOW_FT` of 30 ft, plus an ABSOLUTE clause: no unbroken shadowed stretch longer than one bundle pitch |
| a back lane laid **100% lengthwise inside the shelter belt**, cutting out 15 of its clumps | nothing tested a run against the windbreak | a web lane may cross a belt but not run its length |
| 32.6 ft of a footpath drawn **on top of** a back lane | the router has no cost term for travelling along an existing tread | a footpath stops at its FIRST contact with the network |
| the **notice board re-seated onto a 3 ft service lane** | `place_kosatsuba` falls back to the whole network when no way declares itself main - which a hamlet never does - so the web entered the candidate list on equal footing with the spine | web lanes are excluded from the board's candidates whenever a non-web lane exists. The function's own docstring already stated the rule it was breaking |
| `licence`, `colonised`, `maximises` in code prose | - | corrected; the project spelling rule covers comments and docstrings |

**One finding is ledgered rather than fixed**: Mizuguchi's east "crow's foot", where three ways leave
one node within 23 degrees and two end blunt. It is **skeleton-vs-skeleton**, laid by `stage_ways`
before the houses exist, so the web's shadow test structurally cannot see it; and
`lanes_reach_something` is silent because all three ends claim the same farmhouse within its 90 ft
bar. The reviewer named the missing rule precisely - *two lane ends may not front the same farmhouse
from the same side* - and that is a `stage_ways` change that would move every map. Deferred with its
mechanism, per Principle XIV's architectural exception.

**One question was answered by the reviewers rather than by me**: whether the `back_lane` form owes a
closed block. Kashikawa's reviewer found the quoted "rectangular framework" phrasing is the English
planned-village case, while the non-European warrant attests the back lane without the closed block -
and measured that Mizuguchi produces 4 circuits and Inashiro 1 on the same code, so the form encloses
blocks when the ground allows. **Do not force a cycle.**

## THE CRESCENT FINDING - RETRACTED, and the retraction is the lesson

An earlier draft of this file recorded, at length and with numbers, that four cohort seeds were
unfixable because they were all `shape=crescent`: the cluster wraps around the paddy, its far arm
sits across the field, and "it is the paddy in the way, not a neighbor's yard". Three fixes were
listed as tried and as having "moved the numbers by zero feet - byte-identical across all three,
which is itself the diagnostic".

**All of that was wrong, and the tell was the thing offered as evidence.** Byte-identical output
across three different code changes does not mean the changes were ineffective; it means the changes
were not running. They were applied with heredoc'd patch scripts that printed success and never
wrote to disk, and three cohort runs were then read as measurements of code that did not exist. The
project has a standing rule against exactly this - change files with `Edit`, not with Python that
rewrites them - and it exists because when a patch script fails it fails silently in the patcher.

Re-applied properly with `Edit`, the same three ideas plus a router took every crescent seed green.
The crescents were never the problem; the frame's half-plane filter cut their far arm out of the
web's coordinate space, and once the walk followed the outline instead of filtering it, they were
ordinary maps.

**What to take from it:** a diagnostic that reports identical numbers across supposedly-different
runs is evidence about the HARNESS before it is evidence about the code. Verify the edit landed -
`grep` the new symbol on disk - before you spend a run measuring it.

## Not done, and deliberately

- [ ] **US3 / GM ruling B - honor the rolled `cluster_shape`.** Untouched. `stage_homesteads` still
      seats by rows and frontage and records `meta.cluster_seeding`, which states in writing that
      the rolled knob went unhonored. This is the PRE-EXISTING state the ruling calls out, not
      something this feature introduced, and it is a placer change of its own size. Its own feature.
