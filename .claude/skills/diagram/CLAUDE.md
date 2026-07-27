# /diagram engine - dev loop

Guidance for *working on the diagram engine* (`settlement.py`, `check_village.py`, the pool
generators), as opposed to *invoking* `/diagram` to draw a map (that is `SKILL.md`). This file
auto-loads whenever a session edits files in this directory - which is exactly when it applies.

The project-wide iteration doctrine lives in the root [`CLAUDE.md`](../../../CLAUDE.md)
"Iteration-loop efficiency" section (batch recon into fewer bigger turns; iterate on the ONE
motivating artifact, then run the full test bed once at the end; background the final gate; never
cut the ritual/guardrail steps). Read that first; this file carries the concrete diagram numbers
and the DIAGRAM-SPECIFIC lessons that section does not cover - each earned by costing real
round-trips.

## Gate and sweep timings (the motivating-artifact loop, concretely)

The root "iterate on the motivating artifact, sweep once at the end" rule has these diagram
numbers. A single map's regen + gate is ~1-7s:

    DIAGRAM_SKIP_RENDER=1 python3 pool/<type>/<map>.gen.py && python3 check_village.py pool/<type>/<map>.json

The full pool sweep - `make done`, which runs `test_villages.py` to regenerate EVERY map and gate
it - is **~80 seconds**. (Measured 2026-07-25: it had drifted to 112-215s across six runs, well past
the "~1 minute" this file used to claim from 2026-07-20; indexing the two worst checks that same day
brought it back to 77s. Re-measure and update this number when it drifts again - a stale figure here
is what makes a session mis-plan its loop.) So run the red/green loop against the ONE map
(or fixture) that shows the defect, where cycles are near-free, and reserve the full sweep for AFTER
that map is green. The sweep is MANDATORY, though, whenever shared engine code changed
(`settlement.py`, `check_village.py`, `waterfields.py`): every pool map is a downstream artifact of
the engine, so the sweep is what proves "no other map regressed" instead of hoping it.
Anti-patterns on record: the scale-bar feature used the full suite as its FIRST check of an engine
change - a failure that would have surfaced in ~6s on one map surfaced 17 minutes in; the
swept-collar check (11m07s wall) is the feature the project-wide 78%-turn-latency profile was taken
from.

## NEVER re-run what `make done` just ran, and never run pytest without `-n auto`

The single biggest time sink ever measured on this skill (2026-07-25, a 69-minute feature profiled
from the session transcript): **13.2 minutes - 19% of the whole feature's wall clock - went to one
`python3 -m pytest test_regressions.py` that `make done` had already run, in parallel, minutes
earlier.** Two compounding mistakes, both cheap to avoid:

- **`make done` runs `pytest -n auto`** (see the Makefile), which is ~7x faster than serial on this
  box: the 695-manifest regression replay is ~2 min under the gate and **13.4 min serial**. If you
  ever invoke pytest directly, pass `-n auto`. There is no reason to run it serially.
- **A green `make done` already covers `test_regressions.py`, `test_villages.py`, and every unit
  test.** Re-running any of them "to be sure" buys nothing - the gate is the proof. Re-run only what
  actually changed since the gate went green, and if that is markdown, re-run nothing (root
  CLAUDE.md, "docs-only diffs skip the gate").

## NEVER poll a backgrounded command - and it is now ENFORCED

Backgrounding the gate and then *watching* it is worse than running it in the foreground. Profile of
a 31-minute feature (2026-07-25): **10.9 minutes - 35% of the whole task - went to polling two gates
that had already finished.** The gates took 97s and 98s; the waits took 351s and 401s, both running
their full iteration budget because of this:

    for i in $(seq 1 80); do if ! pgrep -f "make done" >/dev/null 2>&1; then break; fi; command sleep 5; done

`pgrep -f "make done"` **matches its own shell** - the pattern is an argument of the very command
line being searched - so the `break` can never fire. And the loop was pointless anyway: a
backgrounded Bash command NOTIFIES you when it exits. Background the gate, spend the turn on the
docs or the commit message, and act on the notification.

[`scripts/no-poll-hooks.sh`](../../../scripts/no-poll-hooks.sh) (tested by `test-no-poll-hooks.sh`)
now BLOCKS the pattern at PreToolUse: `pgrep -f` / `pkill -f` with a literal pattern, any loop
containing a `sleep`, and the `command sleep` / `/bin/sleep` / `env sleep` forms that exist only to
dodge the harness's own foreground-sleep guard. A genuine wait on EXTERNAL state (a server port)
passes by putting `POLL_OK` in the command with a note saying what it waits for. Same rationale as
the batching hook: "background the final gate" was already written down here, and the session
followed it and then blocked on the gate anyway.

## Before the gate, run the WHOLE affected test file - not a `-k` subset

That same profile paid an extra gate round trip (98s plus two turns) for a failure a local run would
have caught: the change altered geometry an existing test depended on, and the pre-gate check was
`pytest -k torii`, which did not include that test. The whole files for the modules you touched cost
~45s and reach every test the change can. So: cheap linters, then whole files, then the gate ONCE.

    python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy
    python3 -m pytest test_settlement.py test_checks.py -q -n auto --no-cov    # the files you touched, WHOLE
    make done                                                                  # once, backgrounded, not watched

## Ask the ENGINE where a feature fits - do not guess coordinates

When a map change ripples (an avenue shortens, ground frees, a pack seats more houses, a well goes
over its household cap), the fix needs a spot for one more feature. **Guessing coordinates and
regenerating is the most expensive loop in this skill**: 2026-07-25 spent three regenerate-and-check
cycles on two full batches of hand-picked well seats, every one refused. A scan of the MANIFEST
cannot predict `_fits` - those refusals came from a ward fence's 15px no-build corridor, which no
manifest records.

`s.open_seat(rect, w, h, clear_of=[...], well=True)` asks the engine's own `_fits`, at the point in
the gen where the feature would be placed, and returns the best clear seat (furthest from
`clear_of`, ties toward the rect center) or `None` if the ground is genuinely full. It found the
seat both hand-picked batches had missed, first try. Reach for it on any "this pocket needs one more
X" - and note the DRAW ORDER caveat: it can only see what has been drawn so far, so call it where
the feature belongs, not earlier.

## Siting a feature with interacting rules: adjudicate against the GATE, never a re-statement of it

`open_seat` (above) answers "does this fit here?" - geometry only. When a feature's placement is
governed by many INTERACTING rules, that is not enough: the justice works (feature 015) must be
outside the wall, on the way out, past the boundary stone, clear of the community's dead, off the
farmland, on the outcast side, clear of every structure, and inside the map's current view. Use
[`site_justice.py`](site_justice.py):

    python3 site_justice.py pool/provincial-cities/nagahara.json execution_ground --limit=25
    python3 site_justice.py pool/towns/hirameki.json boundary_marker --ground=1620,1900

It proposes seats **cheapest-on-the-frame first** (`frame_cost=0` means the crop is unchanged by
that seat) and adjudicates each one by building a trial manifest and running `check_village.gate()`
on it, reporting the checks that fail there but not with the feature absent.

**The lesson, which generalizes past this feature.** Its predecessor was a scratchpad script that
re-implemented every rule as its own predicate, and it drifted *within a single session*: a
relaxation made to satisfy one map silently persisted and put Nagahara's boundary stone in a field
off the highway. The gate accepted it because the rule it broke was not yet checked, and only the
rendered PNG showed the problem. So a siting tool must never restate a rule - it must ASK the gate.
New rules are then picked up for free, and the tool cannot disagree with the checker. This is the
same trap as "placement and its check must read the SAME manifest source" (below), one level up.
The cheap geometric pass in that file is a RANKING only: it orders candidates to keep the number of
gate runs small, and it never rejects, so a stale heuristic costs runtime rather than correctness.

**The second trap, found the same way (2026-07-26): "adds no new failure" is only HALF of legal.**
The tool's baseline is the gate with the feature ABSENT - so for a feature whose absence is itself a
failure, the very check that governs it is already IN the baseline, and a seat that leaves it
failing adds nothing new and scores as legal. Every candidate stone therefore looked equally good,
and the tool duly recommended the one that put Ubame's dosojin among the west-end shops. `propose`
now also requires a seat to CURE the checks the absence causes, with "curable" derived from the gate
(a check some adjudicated seat clears) rather than declared - so the tool still names no rule of its
own. The general lesson: when an oracle scores a candidate as a DELTA against a baseline, ask what
the baseline is already failing, because a delta cannot see a rule the empty case breaks too.

**Known limit:** label collisions cannot be judged from a manifest - a label box is produced at draw
time, not recorded for a hypothetical placement - so `labels_clear_of_other_buildings` and
`no_label_overlaps` still surface only on regeneration. That is why `punishment_spot` and
`execution_ground` both take `label_above` / `label_xy`.

## Read derived geometry from the MANIFEST, not by re-running the generators

Second-biggest sink in that same profile: **7.6 minutes across three runs of a throwaway analysis
script that re-ran all 17 generators** to compute where trees overlapped buildings. Every one of
those runs was answering a question the manifests could answer directly - the same analysis reading
`pool/*/*.json` takes **0.2 seconds**. The pool JSON is the artifact: outlines, footprints, clump
centers, `tree_crowns`, ditch polylines are all in there. Re-run a generator when you need to change
what it DRAWS; read the manifest when you need to know what it drew. If the geometry you need is not
recorded, that is usually a sign the CHECK needs it too - record it once and both problems go away.

## DRAW ORDER: read this BEFORE changing where anything is placed or drawn

Most of what a Mode B feature gets wrong is not geometry, it is ORDER. A drawing method sees only
what is in `self.M` at the moment it runs, and a placement method avoids only what is in the
registries at the moment it runs - so "tree not drawn on a roof" and "building not placed under a
canopy" are the SAME rule enforced from two different points in the sequence. This map cost four
fail-read-fix cycles to reconstruct on 2026-07-25; it is written down so nobody pays for it twice.

**The three registries, and who honors them:**

| registry | holds | consulted by |
|---|---|---|
| `block_polys` | no-build polygons (field envelopes, the wood, dry plots, the manor court) | `_rect_blocked` tests a whole FOOTPRINT (homestead bundles); `_fits` -> `_in_blocked` tests only the candidate's CENTER (urban packs) |
| `placed` | `(x,y,w,h)` of everything already standing | `_fits` keeps each candidate a half-diagonal + 4px clear |
| `grove_rects` | tree footprints, deliberately kept OUT of `placed` so adjacent groves may abut | `_fits` (same clearance rule), `_east_trees` (garden morning-sun) |

**That `_fits` asymmetry is the trap.** A block poly stops a farmstead whose footprint merely touches
it, but stops an urban building only when its CENTER lands inside - so a wide building can put half
its roof over blocked ground. If a feature must keep whole footprints out, `placed`/`grove_rects`
(distance-based) is the registry that does it; `block_polys` alone is not enough.

**The order a Mode B gen runs in** (Moritono is the clean example):

1. **terrain + water** - fields, channels, streams, pond, marsh
2. **big terrain features** - `forest()` / `forest_patch()`. EARLY, because the settlement is sited
   against them; their FLOOR draws here but their CANOPY is deferred (see 7)
3. **ways** - road, lanes, streets
4. **structures** - `manor()`, `farmsteads()`, urban packs, `place_wells()`, `draft_byres()`,
   `place_kosatsuba()`. Inside `farmsteads()` the bundle path records grove rects first (the garden
   relaxation needs them), then draws yards/gardens/houses, then draws the yashikirin arms LAST
5. **ground cover** - `hinterland()` scrub + marsh (skips structures via `_urban_keepouts`)
6. **communal vegetation** - `village_grove()`. LATE, so its per-crown filter sees every structure
7. **crop** - `crop_to_content()` / `crop_city()`, which first run `flush_stable_yards()` and
   `flush_tree_stands()`: the deferred yard furniture and every wood's canopy draw HERE, against the
   complete map. `finish()` re-runs the tree flush as a backstop for a gen that never crops
8. `title()`, `finish()`

**The two rules that fall out of it:**

- **Must not be drawn ON something?** Run AFTER it, or defer to the flush. Drawing early and letting
  the later feature paint over it hides the overlap instead of preventing it - which is exactly what
  the yashikirin used to do, leaving crowns geometrically under roofs while looking fine.
- **Must RESERVE ground?** Run BEFORE placement AND register in a registry that the placer in
  question actually honors (see the asymmetry above).

**Changing any of this deserves a design pass first.** Read the paths above and settle the ordering
on paper before editing - the failure mode is discovering the sequence one gate failure at a time,
which is what turned a small rule into four fix-fail-read cycles. If a change needs a feature to
move between phases, say so explicitly in the commit: phase moves are the changes most likely to
have effects far from the diff.

## CENTRE vs FOOTPRINT: the three ways placement and the checks disagree

The GM, 2026-07-26, after the overlap matrix kept finding things the placer had allowed: *"if
placement is only testing the house's centre while the matrix tests its footprint, then maybe the
placement test is wrong? Are there other placement checks which are only checking the centre? That
could explain a lot of overlap issues as well as a lot of inefficiencies."* Both halves were right,
and there turned out to be **three** distinct disagreements, not one. Know which you are looking at
before you touch anything.

**1. Centre-tested keep-outs (UNDER-restrictive -> overlaps).** `_fits` tested a candidate's CENTRE
against `block_polys` and the corridors, so a footprint could hang over blocked ground by up to half
its width. Fixed by SPLITTING the registry: `hard_polys` (crop, pond, bog, a field's own ditches) is
tested against the whole footprint; `block_polys` keeps the centre test. **Do not merge them back.**
Footprint-testing all of `block_polys` was tried once and reverted, because it also contains SOFT
reservations - caption bands, civic aprons, fence standoffs - that a footprint routinely overhangs
by a few px, and tightening those cost Nagahara a well and pushed Hoshizora's punishment ground off
its street. The split is the fix; the conflation was the bug.

**2. Circumscribed-circle collision (OVER-restrictive -> wasted ground).** Against `placed` and
`grove_rects`, `_fits` still uses half-diagonal circles, not real footprints. For a 46x28 house that
is r=26.9 against a true half-width of 23, so two such houses are forced >=57.8 px apart centre to
centre where true touching is 28. It never permits a real overlap - it just wastes up to ~2x the
spacing, which is a real cause of "the packer says the ground is full" when it is not. Replacing it
with a SAT footprint test would relax spacing on every dense map and re-roll their populations, so
it is a deliberate, separately-verified change, not a drive-by.

**3. Placement tests a DIFFERENT footprint than the one drawn (still open).** `_fits` is called with
a farmhouse's BASE rect, but the drawn steading can exceed it - a wealth render scale, an attached
shed, a rotation. So a candidate that genuinely cleared every keep-out at its placement size laps one
at its drawn size, and no amount of fixing (1) reaches it. Hoshizora's gen already works around this
by inflating its hem plots ~8 px (`grow_poly`), which treats the symptom locally. The real fix is for
the placer to test the size it is going to DRAW.

**The general lesson.** A point test is right for a SCATTER (each tuft is a point) and wrong for
anything with an extent. The same trap bit the ground-cover tiler: `near_ring_cropland` sampled a
cell's centre and four corners, which a small keep-out sitting against an edge MIDPOINT slips
between - that is how a wellhead ended up 1 px inside a hatake plot. Region-vs-region helpers
(`quad_hits_poly`, `quad_hits_seg`, `point_quad_dist`) exist now; use them rather than adding sample
points.

## Centres, footprints, and aggregates: which one a rule is allowed to use

The GM, 2026-07-27, after the boundary-stone defect: *"I'm not sure it EVER makes sense to use a
centre instead of a footprint... we've had a lot of bugs slip through because of using centres,
which makes me wonder whether we should just ban them."* An audit of all 42 centre-distance sites
and 29 `point_in_poly`-on-a-centre sites says: a blanket ban would break three things that are
right, and would still have missed the defect that prompted it. **Four families. Say which one your
rule is in, in a comment, at the point of the test.**

| family | measure | why | examples |
|---|---|---|---|
| **Gap VERDICT** - "N ft of clearance", "these must not overlap" | `edge_gap` / `within_edge_gap` / `sat_overlap` on real rotated corners. **Never** a centre, **never** a circumscribed radius | the answer is a distance you could pace out between two walls | `execution_ground_outside_the_settlement`, `town_has_cremation_ground`, `burakumin_quarter_segregated`, `execution_ground_clear_of_the_dead`, `wells_among_dwellings`, `farm_sheds_attached` |
| **CLASSIFICATION / counting** - "which ward", "how many inside the wall", "what share of this quarter is civic" | centre, deliberately | a building belongs to ONE ward; footprint-testing double-counts a building on a seam and the ward populations stop summing to the town | the 29 `point_in_poly(b["x"], b["y"], wall)` sites |
| **ASSOCIATION / reach** - "is there a well within reach", "do monk houses cluster at their temple", "is this yard on the water" | centre, deliberately | the tolerance (75-480 px) dwarfs the footprints and the question is neighbourhood membership, not clearance; converting them re-tunes ~21 calibrated constants to fix nothing | `settlement_dwellings_watered`, `city_monk_houses_by_their_temple`, `_ty_on_water` |
| **PREFILTER** in front of an exact test | circumscribed radius, deliberately | over-stating an extent can only ADMIT a pair the exact test then rejects - the index prunes, it never decides. Tightening these would start rejecting before the exact test runs | `fire_tower_standoff`, `no_structure_overlaps`, `city_house_doors_unblocked`, `within_edge_gap`'s own prefilter |

**The three conventions that were live before this, and what each cost.** Raw centre-to-centre
understates clearance by the sum of both half-extents, so a rule promising 120 ft delivered ~60;
`0.5 * math.hypot(w, h)` is the half-DIAGONAL, over by up to 41% on a square and more on a long
rect; `max(w, h) / 2` is the same error differently sized. The approximations' error **flips sign**
with the rule - subtracting too much makes a "must be far" rule strict and a "must be near" rule
lenient - so they are not even a uniform safety margin.

**The ratchet, not the doc.** `test_gap_verdicts_read_footprints_not_centers` plants two features at
exactly the offset where the conventions disagree and pins which verdict is right. Verified to have
teeth: reverting the helper to raw centres breaks three of its six entries, reverting it to
circumscribed radii breaks the other three. **Add an entry when you add a gap rule** - a rule that
lives only in this table has already been proven not to hold.

**And a fourth axis, which no footprint discipline reaches: AGGREGATE PROXIES.** The boundary-stone
defect was not a footprint bug. `dist(stone, centroid) < dist(ground, centroid)` would stay green
with perfect geometry on both sides, because the centroid - an average of every dwelling - was
standing in for the built EDGE, and a settlement is not a disc. **Never let an aggregate stand in
for the distributed thing a verdict is about.** Measure to the nearest member (or, where the
settlement has a rampart, to the wall - the edge it actually has). `execution_ground_on_the_outcast_
side` still dots against the centroid and that is correct: a BEARING is an aggregate question. A
DISTANCE is not.

**Known debt, recorded as debt rather than design:** `_fits` centre-testing `block_polys` (item 1
above). The honest reading is that those polygons are drawn wrong - keep-out plus slack baked in,
with the centre test handing the slack back - and the principled fix is to shrink them to the true
keep-out and footprint-test. That re-tunes margins pool-wide, so it is a separate pass.

## Adding a new map feature: the KEEP-CLEAR CONTRACT (read this before writing the glyph)

The GM's observation, 2026-07-25, after the martial hall shipped sitting on Tango's ring road:
*"every time we add a new type of thing, I end up looking at the map and saying 'oh, this new thing
should not overlap with X'."* That is now a solved problem, and this is the whole of what you have
to do.

**One registry, and everything follows from it.** A new footprint feature goes in
`_OVERLAP_STRUCTS` (check_village.py) - or, if it is MEANT to overlap something, in
`_OVERLAP_EXEMPT` with the reason. You cannot forget: `every_feature_classified_for_overlap` fires
when a generator emits a feature key nobody classified. Membership alone then gates the feature off
**fifteen hazards** - the wall, the moat, the road, streets and alleys, streams, channels, the
cargo canal, the pond, manor walls, religious halls, gate furniture, torii arches, the ring road,
every other solid structure, and the 14px government-office standoff - because every one of those
checks builds its footprints from the registry via `solid_structs(M)`.

**The failure mode this replaced.** The `no_structure_on_*` battery was always registry-driven, but
a handful of keep-clear checks predated it and hand-listed their own keys. A feature could be
correctly classified, correctly cleared of all thirteen battery hazards, and still sit on the ring
road - because `ring_road_kept_clear` was reading eight keys nobody had updated. A check that never
sees your feature looks exactly like a check that passes, so this was invisible until the GM looked
at a rendered map. Four such checks now read `solid_structs(M)`: `ring_road_kept_clear`,
`city_government_offices_dont_abut`, `city_wells_in_block_interiors`, and the merchant-estate
court test.

**The ratchet.** `test_checks.py::test_every_solid_struct_is_gated_off_every_hazard` plants one
instance of EVERY registered key squarely on EVERY hazard and demands the hazard's check fire. If a
keep-clear check ever falls back to a hand list, that test names both the key and the hazard.
Verified to have teeth: reverting `ring_road_kept_clear` to its old list fails it with 21 keys
listed. **Adding a hazard row to `_HAZARDS` extends the contract to every existing feature at
once** - that is the cheap way to answer the next "should not overlap with X".

**The same contract covers CAPTIONS** (GM 2026-07-26). A feature protected from every solid
neighbor is still not protected from a label dropped on top of it, and
`labels_clear_of_other_buildings` had its own hand-written list of ~22 keys that had already fallen
behind twice - `martial_halls`/`dojos` had to be remembered into it, and a day later
`punishment_spots`/`execution_grounds`/`boundary_markers` were absent, so a foreign caption over an
execution ground shipped green. `_LABEL_GROUP` now maps each manifest key to the caption GROUP a
label must name to be allowed over it, `_LABEL_EXEMPT` excuses the few that do not need protecting
(with the reason), and `every_solid_feature_classified_for_labels` fires when a key is in neither.
The permission side is derived from the same registry - a group's name IS its caption word
("brewery", "martial hall", "execution ground") - so a classified feature can caption itself with
no second list to remember. The named branches in `_label_allows` survive only for SYNONYMS: a
caption reads "Temple of Benten" or "Governor's Mansion", not "temple" or "governor".

**RECORD A FOOTPRINT THE EXTRACTOR CAN READ - classification is only half.** GM, 2026-07-27: *"in
general we always want overlap checks to use full footprints."* `matrix_extents` reads `x`+`w`/`vw`,
a `poly`/`outline` ring, a stroked polyline, or a `parts` list of rotated quads. A record matching
NONE of those is extracted as nothing, and a feature the extractor never reaches is invisible to
every matrix check in both directions no matter how carefully it is classified and mounted - which
looks exactly like a feature with nothing wrong. Three keys were in that state until an audit went
looking (`kido`, which records only a centre and its parts; `roads`, the multi-road list;
`flower_fields`, whose ring is called `outline`, not `poly`), and the ward gate had been hiding a
notice board sitting on its guard box and two guard boxes cut by their own ward fence. The audit is
cheap and worth re-running whenever a new key appears - per manifest, compare each classified key's
record count against `collections.Counter(k for k, *_ in matrix_extents(M))`; any key with records
and no extents is blind. And where one glyph draws SEVERAL rects, record them as `parts` (rotated
corner quads) rather than a bounding box, and split out any part that does not share the whole
feature's permissions - a gateway may stand on the fence it pierces, its watch box may not.

**So the checklist for a new feature is:** write the glyph; record it under a new manifest key; add
that key to `_OVERLAP_STRUCTS` and give it a caption group in `_LABEL_GROUP`; run the suite. If the
feature needs a keep-clear rule no existing hazard covers, add a hazard row rather than a bespoke
check with its own key list.

**The placement side, which the GM asked about next.** `_fits` tests an urban candidate's CENTER
against `s.bound`, `block_polys` and the corridors, and whole footprints only against `placed` /
`grove_rects` (see DRAW ORDER below). `open_seat` now closes the half of that gap that matters:
it verifies the whole FOOTPRINT against **the bound**, because a bound is a hard edge (the
ring-road loop, the wall) and a footprint crossing it is drawn on the patrol road at any overhang -
which is exactly how the martial hall got its seat. `block_polys` and corridors stay center-tested
even there, deliberately: those are soft RESERVATIONS (a label band, a civic apron, a fence
standoff) that a footprint routinely overhangs by a few px, and tightening them was tried and cost
Nagahara a well and pushed Hoshizora's punishment ground off its street. The bound-only rule
changes nothing in the pool. `footprint=False` gets the old center-only answer, i.e. what a pack
would take. (`test_open_seat_refuses_a_seat_whose_FOOTPRINT_crosses_the_bound` holds this.)

**Gap rules are in the table now, but one row each.** A clearance rule ("14px of daylight", not
"no overlap") is the other shape a keep-clear rule comes in, and it broke identically:
`city_government_offices_dont_abut` had never seen the martial hall or the dojo, so both shipped
inside its standoff. A `_HAZARDS` row expresses a gap simply by planting the struct NEAR the hazard
instead of on it, so the contract covers it - but unlike the overlap hazards, each new distance
rule still needs its own row. A row's fifth field lists keys the rule DELIBERATELY does not govern
(the funerary compounds are excluded from the office standoff: a clan crypt against the yamen is a
real adjacency), so a deliberate exclusion is visible in the contract rather than hidden in a
check.

## Declared overrides: a map may break a rule, but only IN WRITING

Every placement rule in this engine is a GENERALIZATION, and a specific place is allowed to have a
specific history that beats it. Tango's samurai take the southeast because the Emperor lies that
way, which pushes the outcast quarter opposite its own tanning yard. Hirameki's walls were thrown up
in a hurry when a war turned an interior county into a border one, which is why that town looks
non-standard in several ways. The GM's rule (2026-07-27): **rules and checks are overrideable - and
an override must carry a documented explanation.**

    s.meta(waivers={"tanning_yard_on_the_outcast_side": "The Emperor lies southeast of Tango ..."})

The gate then prints `WAIVE <check>` instead of `PASS`, lists every waiver again in a closing
summary, and keeps the name out of the failure list. Two meta-checks keep the hatch from rotting:

- **`waivers_are_documented`** - the value must be 60+ characters of actual REASON. "by design" and
  `True` both fail. The waiver text is the only record that the map broke the rule on purpose, so it
  states the place's history, not the fact of the exemption.
- **`waivers_are_live`** - the waiver must name a check that ACTUALLY FAILED on this map. A waiver
  whose defect was since fixed, whose check this scale never runs, or whose name is a typo is stale
  and fails. Waivers therefore rot loudly instead of accumulating into a map that is quietly exempt
  from rules nobody remembers it was breaking.

Neither meta-check is itself waivable, or the hatch would swallow its own guard
(`test_the_waiver_meta_checks_cannot_themselves_be_waived`).

**When NOT to reach for it.** A waiver is for a place with a REASON, never for a map that is simply
inconvenient to fix, and never as a way to ship a red gate. If you find yourself writing the reason
and it is really "another session owns this file" or "re-siting is a lot of work", the honest move is
to fix the map or ask the GM - the mechanism is built to make that distinction visible, so using it
to paper over the second kind turns the whole audit trail into noise. And when a rule genuinely
needs to bend for a whole CLASS of maps rather than one place, change the rule, not each map.

**Freeze the pre-waiver manifest as a regression fixture.** A waived map no longer fails, so the
check has no live map holding it honest. Drop the manifest as it stood BEFORE the waiver into
`pool/regressions/` with a `_regression` block (see
`tanning_yard_on_the_outcast_side_fires_on_the_pre_waiver_tango.json`) so a refactor that neuters
the check is still loud.

## When a check is slow, INDEX it - do not coarsen it

The gate's cost is dominated by a handful of checks that ask a local question with a global scan.
Profile before guessing (`cProfile` around `check_village.gate` on `tango.json`, the worst case):
2026-07-25 found `city_fan_heads_quilted` testing ~3,000 canal-side samples against EVERY plot
polygon and ditch (14M `seg_dist` calls, ~58% of a 17s city gate) and `structures_clear_of_dry_plots`
testing every structure against every dry plot (3.5M `segments_cross` calls). Both were fixed with
`GridIndex` (a uniform-grid spatial index at the top of `check_village.py`): insert each feature
under the cells its influence bbox touches, query the cell, then run the SAME exact test on the few
candidates. Result: Tango 17.3s -> 2.9s, whole-pool gate 34.1s -> 11.8s, `make done` ~2min -> 77s,
with **byte-identical verdicts on all 695 manifests** (pool + regression corpus).

The rule that matters: **the index prunes, it never decides.** It is always tempting to make a slow
check cheap by making it coarser - testing a bounding polygon instead of the real features, sampling
fewer points, raising a tolerance. That trades correctness for speed and the loss is invisible until
a real defect slips through. Indexing costs ~15 lines and changes no verdict, so there is no reason
to reach for coarsening first. (Concretely: `structures_clear_of_trees` must test the recorded
CROWNS, not the stand outline, because placement drops crowns individually - an outline test would
fire on trees that were deliberately never drawn.)

Verify an optimization the same way: capture `sorted(gate(M))` for every manifest in `pool/**` before
the change, re-run after, and diff. Anything but "NONE" means the optimization changed behavior.
Run that sweep with `-n auto`-style parallelism or in the background - serial it is ~13 minutes.

### A `GridIndex` box is a COST, so clamp it - on insert AND on query

`GridIndex` allocates a dict entry per 120 px cell of the box it is handed, in both axes. That is
fine for anything on the map and catastrophic for anything that is not: the regression fixture
`city_geometry_within_canvas_fires_on_a_stray_vertex.json` plants a wall vertex at **9,000,000** on a
3,200 px canvas, so the moment `wall` became a SOLID in `OVERLAP_CLASS` and got stroked into quads,
one feature asked for ~5.6 billion cells. The gate ate gigabytes of RAM and the GM had to kill it by
hand (2026-07-26). **Negative fixtures contain deliberately insane geometry - any new code that
consumes raw manifest coordinates will meet it.**

Two rules, and the second is the one that is easy to half-do:

1. **Clamp the index box to the canvas** (`meta.W`/`meta.H`, generously - a couple of canvases of
   slack). Clamping only shrinks, and a polygon's on-canvas part is always inside the clamped box, so
   no real overlap can be lost. Geometry wholly off the canvas is skipped; that is
   `city_geometry_within_canvas`'s business, not the overlap matrix's.
2. **Clamp the QUERY box too.** `near_rect` walks the cells of the box it is *given*. Clamping only
   the insert leaves the query iterating exactly the same billions of cells - which is precisely the
   half-fix that shipped first here and looked plausible for a whole turn.

`test_matrix_survives_geometry_far_off_the_canvas` in `test_checks.py` is the guard, timed rather
than structural on purpose: the failure mode is unbounded work, and the correct-vs-broken margin is
a fraction of a second against effectively forever.

## Batch the rendered-map inspection

Reading a map means: render -> crop the region(s) of interest -> Read the PNG. The turn-latency
killer is doing this serially, one crop per turn (`crop -> Read -> crop -> Read ...`). ~78% of
wall time is model-turn latency (root CLAUDE.md, 2026-07-20 profile), so each extra round-trip is
pure cost. Instead: in ONE Bash call, crop EVERY region you want to look at (all four viewports of
a defect, before/after of several maps, the toe + the top + a control), then Read them together in
the next turn. A footbridge review that touched 3 maps should be ~2 turns of imagery, not ~10.
**Use [`crop_map.py`](crop_map.py) rather than re-writing the arithmetic** - it reads the viewBox
itself and takes as many regions as you like in one invocation, which is the batching win made easy:

    python3 crop_map.py pool/towns/hoshizora 1600,900,220 1200,400,150   # x,y,radius (world coords)
    python3 crop_map.py pool/hamlets/moritono --box 2100,150,2418,760 --zoom 1.5
    python3 crop_map.py pool/villages/ueda --whole --zoom 0.4            # whole map, downscaled

It prints one path per line - feed them straight to Read, together. (The conversion is
`(coord - viewBox_origin) * (png_w / viewBox_w)`; it was hand-written five times in one session,
once wrong, which is why it is a script now.)

## Run the cheap linters BEFORE the full gate

`make done` runs lint -> format -> typecheck -> test+coverage and STOPS at the first failure, so a
trivial formatting or type slip makes you pay a full ~1-min gate run to discover it, fix, and pay
again - the failures surface one per gate run, not all at once. After writing engine code and
BEFORE `make done`, run the seconds-long prefix yourself:

    python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy

That catches format + lint + type errors in one cheap shot (a common one: a local variable name
like `a`/`ux` that collides with an existing binding in the huge `gate()` scope - mypy flags it,
the full gate would too but slower). Only then spend the gate run on tests + coverage.

## Update the predictably-affected tests in the SAME edit

Touching a `settlement.py` method breaks its unit tests deterministically - you know which ones
before you run anything. `channel_footbridges` has `test_settlement.py::test_channel_footbridges_*`
and the `test_checks.py::_footbridge_map` fixture; changing placement semantics (e.g. "a plank now
needs cultivation on both banks") means those setups need cultivated ground added. Update them in
the same turn as the engine change, don't discover the breakage via a failed pool sweep. Grep for
the method name in `test_*.py` before editing.

## Converge on a new rule with ONE pool-wide dry-run, not one variant per turn

When adding a placement rule or check, the pool IS the test bed: the right predicate is the one
that flags exactly the defective features and spares every good one across all 13+ maps. Don't
test candidate rules one-per-turn against one map. Write ONE script that loads every pool manifest
and, for each candidate predicate (marsh-only vs both-banks-cultivated vs cultivated+village+dike
...), prints what each would drop/keep per map - then read it once and pick the winner. This is how
the footbridge rule's edge cases (polder toe-planks cross onto the DIKE; village-edge planks cross
to houses; dry-to-wet crossings) surfaced in one pass instead of five.

## A check that never RUNS looks exactly like a check that passes

Three separate times in one feature (2026-07-25, the water-flow work) the defect was **not a bad map
but a check that was silently not running**, and each time the gate was green throughout. The shape is
always the same: a rule gated on an OPTIONAL declaration that almost nothing declares.

- `meta(down_deg)` gated the whole drainage-slope block, `downhill_direction_valid` and
  `marsh_on_low_ground`. The two provincial cities declared none, so they were never validated by any
  of them - the code even said so out loud: *"maps without the tag are exempt (slope unknown)"*.
- The legacy `meta(downhill)` gated `channels_flow_downhill`. Only **2 of 17** maps declared it, so 15
  skipped that check entirely.
- `moat_channels_flow_with_current` needed a stream END within 35px of the moat ring. Nagahara's river
  ends off-map (it is the MOAT's ends that meet the river), so it **never ran there at all** - and on
  Tango it ran only because the feeder happened to be drawn before the outfall.

**The cheap diagnostic.** Coverage does not catch this: the gated branch is exercised by SOME map, so
the lines are covered while other maps never reach them. What catches it is asking, per map, whether
the check appears in the output at all:

    python3 check_village.py pool/<type>/<map>.json | grep -c "<check_name>"     # 0 = never ran

Run that across the pool for any check whose body sits behind `if meta.get(...)` or
`if <thing> is not None:`. A `0` on a map that plainly has the feature is the bug.

**The ratchet.** When a rule needs a declaration to work, add a check that the DECLARATION EXISTS -
otherwise the rule is optional in practice no matter how firmly it is written.
`settlement_declares_a_land_fall` is the model: it demands a map-level `down_deg` or a per-field fall
on every paddy, and says in its own message that a map declaring nothing SKIPS every drainage rule
while still showing green. Prefer this to widening the gate quietly.

## Build check-test manifests with the fixture builders

`test_checks.py` hands `gate()` hand-built manifests carrying only the keys the check under test
reads. That focus is right, but it has a tax: a record often must carry a key some OTHER check
indexes unconditionally (a threshing yard's `of`, a grove's `face`), and omitting it does not fail
your test - it raises a `KeyError` from an unrelated check, costing a fix-and-rerun cycle to
diagnose. Use the builders at the top of the file (`manifest`, `house`, `yard`, `garden`, `well`,
`grove`, `vgrove`, `bldg`); they carry the required keys and take `**kw` overrides.
`test_fixture_builders_survive_every_check` runs every check against one of each and is what keeps
them complete - if a check starts indexing a new required key, it fails there once instead of
ambushing the next person to write a test.

## Placement and its check must read the SAME manifest source

A recurring engine trap (footbridges 2026-07-22; recorded in [`settlements.md`](settlements.md)
under "PLANK BRIDGES"): the generator in `settlement.py` and the validator in `check_village.py`
must classify terrain from the SAME data, or they disagree and a feature the generator dropped is
demanded by the check (or vice versa). Read the MANIFEST fields (`M["fields"]` outlines +
`M["dry_plots"]`), NOT engine-internal blocking lists like `self.field_polys` that some gens leave
empty. When a new check pairs with new placement logic, factor the shared predicate so both sides
provably use it.

## A dirty tracked manifest with no code change behind it: suspect the MEASUREMENT, not the generator

`title()` sizes its placard by measuring the name's glyphs with PIL (`_text_width`), and that
measurement is recorded in the manifest - so anything environmental that shifts it by a fraction of a
pixel rewrites every titled map's bytes with no code change in the diff. That is what a container
rebuild did on 2026-07-25: PIL picks its layout engine by what is installed (RAQM where libraqm is
present, BASIC where it is not) and the two disagree at the subpixel level, so all 16 titled
manifests came back dirty at once. The fix was to PIN the engine - see `_text_width`'s docstring and
`test_text_width_is_pinned_to_the_basic_layout_engine`, which holds the pin so it cannot come loose
silently - and the pool is byte-reproducible on any container again.

The transferable part is the DIAGNOSIS, because `render-sync` reports this and a genuinely
nondeterministic generator in the same words. Diff the manifests SEMANTICALLY, key by key
(`json.load` both sides and compare) - never as text, since these are single-line JSON files where a
text diff always shows the whole file and tells you nothing. Only `title`/`scalebar` moving, by a
hair, uniformly across every map, is a measurement-environment signature; a house, a ditch, a crown
or a count moving is a real bug. And when a recorded value depends on something git does not carry,
pin the dependency rather than re-recording the drift - re-recording just waits for the next rebuild.
