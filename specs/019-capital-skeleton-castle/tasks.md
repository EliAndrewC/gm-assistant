# Tasks: The capital map skeleton and the castle

**Feature**: 019-capital-skeleton-castle | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

**Working directory**: `.claude/skills/diagram/`.

**Red-green TDD** (Principle X.4): each implementation task is preceded by its test task.

**The pool must stay byte-identical.** No existing map declares `capital`, so widening a scale predicate cannot change one - but T028 proves it rather than assuming it.

---

## Phase 1: Setup

- [ ] T001 Sync the clone and confirm a clean base: `scripts/sync-with-main.sh sync-in` then `git status --porcelain`
- [ ] T002 Re-read the settled decisions rather than working from memory: `settlements/capitals.md` (the tier rules, the blank-castle doctrine, the road/gate list) and `specs/018-capital-space-budget/research.md` (the Phase 0 findings the closing gate is judged against)

---

## Phase 2: Foundational - the tier runs (BLOCKING)

- [ ] T003 Write a failing test in `test_settlement.py` that a Settlement declaring `meta(scale="capital", ftpx=3)` gets `bscale == 1/3` and carries the scale into its manifest
- [ ] T004 Widen the 12 `scale == "city"` predicates in `settlement.py` to a shared membership test covering `capital`, checking EACH site individually and leaving a comment where a site is deliberately NOT widened
- [ ] T005 [P] Widen the equivalent scale predicates in `check_village.py` so a capital runs the city-tier checks it shares, again site by site
- [ ] T006 Run the pool sweep early as a canary - `python3 -m pytest test_villages.py -q -n auto --no-cov` - to prove the widening moved nothing before any new drawing exists

**Checkpoint**: a capital gen can run; nothing new is drawn yet.

---

## Phase 3: User Story 2 - the castle (Priority: P2, built FIRST) 🎯

Built ahead of US1's other features because it is the decision the feature exists to test.

- [ ] T007 Write failing tests in `test_settlement.py` for `s.castle(...)`: it records `M["castle"]`, draws an outer wall + moat + gate, and places NO entry in any building list
- [ ] T008 Implement `s.castle(...)` in `settlement.py` - outer enceinte, moat ring, gates - on the `manor`/`governor_mansion` lineage (walls + gate + empty court), with a docstring carrying the sync argument verbatim from `settlements/capitals.md`
- [ ] T009 Write a failing test in `test_settlement.py` that the castle reserves its WHOLE footprint in BOTH `block_polys` (center-tested, for urban packs) and `placed` (distance-tested) - FR-006, and the registries differ on purpose
- [ ] T010 Implement the dual reservation in `settlement.py`, with a comment naming the DRAW ORDER rule it satisfies
- [ ] T011 Write failing tests in `test_settlement.py` for the provisional internal works: bailey walls (concentric divisions), inner moats, and the masugata dogleg approach, all behind ONE knob so the verdict can be applied by flipping it
- [ ] T012 Implement the bailey walls, inner moats and masugata approach in `settlement.py` behind that single knob, defaulting ON per the GM's "try it and see"
- [ ] T013 [P] Classify `castle` in `check_village.py`'s `_OVERLAP_STRUCTS` and give it a caption group in `_LABEL_GROUP` - the KEEP-CLEAR CONTRACT, which gates it off all fifteen hazards at once
- [ ] T014 [P] Write a failing test in `test_checks.py` that `capital_castle_interior_empty` fires when any building stands inside the enceinte - the rule that is NOT a knob

**Checkpoint**: the castle exists and can be drawn.

---

## Phase 4: User Story 1 - the skeleton renders (Priority: P1)

- [ ] T015 Write `pool/capitals/shiro-daika.gen.py` header: the docstring stating the geography, the roads and their destinations, the castle seat, and what is deliberately NOT yet drawn (so a reader is not confused by an empty interior)
- [ ] T016 In the gen, declare the program and take the wall from `citybudget.plan_capital` - never a hand-picked RX/RY - and record `s.meta(budget=budget_to_manifest(budget))`
- [ ] T017 In the gen, draw the NE-SW river running off both map edges, and NO trunk road alongside it (the towpath is feature 020's)
- [ ] T018 In the gen, draw the wall with FOUR gates, its moat, and the ring road, per the recorded road list
- [ ] T019 In the gen, draw the Imperial road entering the SOUTH gate, running N-S through the city, and bending northwest beyond the north gate toward Shiro Kyo - labeled OUTSIDE the wall, as the only named way
- [ ] T020 In the gen, draw the two unlabeled trunk roads: east to the Fox lands, southwest into the domain
- [ ] T021 In the gen, place the castle with its ote-mon facing SOUTH onto the ceremonial approach from the south gate
- [ ] T022 In the gen, declare the quarters tiling the interior, and crop + title the map
- [ ] T023 Register the gen in `test_villages.py` with a CPU budget entry (~4x its solo measurement, per the calibration rule)
- [ ] T024 Render at the raised width and confirm legibility matches a provincial city's - the tier absorbs its extent by render WIDTH, never by shrinking the drawing (FR-011)

**Checkpoint**: there is a map to look at.

---

## Phase 5: User Story 3 - the ways are right (Priority: P3)

- [ ] T025 [P] Write failing tests in `test_checks.py` for the capital way rules: four gates, each with a way through it; the Imperial road the only labeled one; the river off both edges with no road alongside
- [ ] T026 [P] Implement those checks in `check_village.py`, scoped to `scale == "capital"`
- [ ] T027 Scope the emptiness/density checks so a deliberate skeleton does not fire them AND they are not weakened (FR-012) - state in each comment what defers them to feature 020, so the deferral is visible rather than silent

---

## Phase 6: The artifact gates - what no automated check can do

**These are the point of the feature. Do not compress them.**

- [ ] T028 Verify the byte-identity claim: `git status --porcelain -- pool/provincial-cities pool/towns pool/villages pool/hamlets` MUST be empty
- [ ] T029 **Launch `settlement-review` NOW**, scoped as `DELTA: a new capital-tier SKELETON map - wall, moat, river, roads, gates, castle. Housing, temples, wharf, aqueduct and lineage compounds are deliberately NOT drawn yet.` Launch it the moment the map is final, before the docs and the commit, since everything done while it runs is free
- [ ] T030 **Principle XII CLOSING GATE** (transferred from feature 018): examine the rendered PNG - the picture, not the code, not the intent - against the Phase 0 findings in `specs/018-capital-space-budget/research.md`. Confirm the castle reads at its researched scale, the roads leave where the geography puts their destinations, and no element depicts something that never existed. `check_village` proves internal consistency, never historical truth
- [ ] T031 **The bailey-wall VERDICT** (US2, the reason for the build order): look at the castle and answer one question - fortress, or enormous empty box? Record the verdict in `settlements/capitals.md` EITHER WAY, with its reasoning; if kept, record that the castle's future Mode A sheet inherits their geometry as a constraint
- [ ] T032 Act on the review's findings, then re-render if anything moved

---

## Phase 7: Close out

- [ ] T033 Run the cheap linters: `python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy`
- [ ] T034 Run the WHOLE affected test files: `python3 -m pytest test_settlement.py test_checks.py test_villages.py -q -n auto --no-cov` - never a `-k` subset
- [ ] T035 Run `make done` ONCE, backgrounded, as `cd <dir> && make done > /tmp/gate019.log 2>&1` and nothing more; act on the notification, never poll, and tail the log before believing green
- [ ] T036 Update `settlements/capitals.md` so the STATUS banner reflects what now ships and what is still 020's
- [ ] T037 Commit and run the stop-work ritual from the clone root; render-sync publishes the PNG into main where the GM browses renders

---

## Dependencies

```
Phase 1 -> Phase 2 (tier runs)  [BLOCKING]
             -> Phase 3 (the CASTLE - built first, deliberately)
                   -> Phase 4 (the skeleton renders)
                         -> Phase 5 (way checks)
                               -> Phase 6 (ARTIFACT GATES)  -> Phase 7
```

## Implementation strategy

**The build order is the feature's design.** The castle comes before the roads it stands among, because the GM's provisional decision about its internal walls is the thing this feature exists to answer, and answering it early is worth more than a tidy dependency order.

**Phase 6 is not paperwork.** Three separate things look at the picture - an independent reviewer, the historical-grounding gate, and the GM's own bailey-wall question - and none of them can be replaced by a green gate. A map can pass every automated check and still depict something that never existed.
