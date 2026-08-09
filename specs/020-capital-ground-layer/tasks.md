# Tasks: The capital's ground-reserving layer

**Feature**: 020-capital-ground-layer | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

**Working directory**: `.claude/skills/diagram/`. **Red-green TDD** (Principle X.4): the test task precedes its implementation task.

**EVERY new manifest key is a LIST of dicts.** Feature 019's lesson: a bare dict made the largest structure on the map invisible to three independent guardrails at once, silently. This layer adds many keys, so the mistake is available many times.

**Most of this layer is REUSE** (see plan.md's table) - `manor`, `ministry`, `granary`, `dock`, `jetty`, `shrine_hall`, `frontage`. Only the towpath and the aqueduct are new glyphs.

---

## Phase 1: Setup

- [x] T001 Sync the clone; confirm clean: `scripts/sync-with-main.sh sync-in && git status --porcelain`
- [x] T002 Re-read the settled decisions: `settlements/capitals.md`, `research/cities/capitals.md`, `wip/README.md` (which carries the two deferred defects)

---

## Phase 2: Foundational - fix what is already blind (BLOCKING)

Done first because this layer ADDS water crossings, and adding them over a known-blind check compounds the defect.

- [x] T003 Write failing tests in `test_checks.py` that a road in `M["roads"]` crossing the city moat, a way crossing `M["river"]`, and a way crossing the castle's own moat are each reported as unbridged
- [x] T004 Factor the carried-ways and crossed-waters sets into ONE shared source in `check_village.py`, consumed by both `roads_bridge_water` and `settlement.bridges()`, with a comment recording WHY: the previous mirror guaranteed agreement rather than correctness, and re-adding the keys on both sides separately would reproduce the same silent symmetry
- [x] T005 Make `settlement.bridges()` consume that shared source so it bridges the crossings the check now demands
- [x] T006 Re-zone the declared quarters in `wip/shiro-daika.gen.py` so the civic quarter is the ground the government actually occupies (south of the ote-mon), not the NE wedge

**Checkpoint**: the map's existing water crossings are bridged and its quarters are honest.

---

## Phase 3: User Story 1 - the seat of government (P1) 🎯 MVP

- [x] T007 In the gen, draw the ote-suji ceremonial avenue from the castle's front gate south to the Imperial road
- [x] T008 In the gen, site the six domain ministries fronting that avenue, each labeled with its office, each standing clear of its neighbors
- [x] T009 In the gen, add the House Chancellery and the domain school (hanko) on the same axis
- [x] T010 [P] Write failing tests in `test_checks.py` for the capital government rules: six ministries present, each fronting the avenue, none abutting another
- [x] T011 [P] Implement those checks in `check_village.py`, scoped to `scale == "capital"`

**Checkpoint**: the map reads as a seat of government. This is the MVP.

---

## Phase 4: User Story 2 - a SPECIFIC domain's seat (P2)

- [x] T012 Write a failing test in `test_settlement.py` that the Imperial Magistrate's compound is drawn in ink distinct from the ministries' state violet - it is foreign sovereign ground and must not read as another domain office
- [x] T013 Add the distinct-ink parameter to the compound glyph in `settlement.py` and draw the Imperial Magistrate's compound in the gen
- [x] T014 In the gen, draw the Emperor's granaries at the declared `imperial_granary_seat` ("wharf" for Shiro Daika), separate from the domain's own store
- [x] T015 In the gen, draw the eight labeled lineage compounds in four size bands tracking the chargen weights - hazama/utsuro/tokiwa/anzu grand, kurogi smaller, yodo/nio/seki modest - and give the ruling daika lineage NO compound, because its seat is the castle
- [x] T016 [P] Write failing tests in `test_checks.py` that a capital's lineage compounds are labeled, that no compound is drawn for the ruling lineage, and that the size bands are visibly distinct rather than merely numerically different (SC-002)
- [x] T017 [P] Implement those checks in `check_village.py`
- [x] T018 In the gen, draw the two sovereign temples (Benten and Jurojin, the Scorpion patrons) and belt the remaining temples along the inner face of the rampart as the teramachi rim

**Checkpoint**: the map names its lineages and reads as Daika's seat specifically.

---

## Phase 5: User Story 3 - waterfront and water supply (P3)

- [x] T019 Write failing tests in `test_settlement.py` for `s.towpath(...)`: it records a list, draws WITHOUT a roadbed or a dashed centerline (it is not a road), and reserves its ground
- [x] T020 Implement `s.towpath(...)` in `settlement.py`, with the qiandao grounding in its docstring - it exists for upstream haulage, so it supplements the boats rather than replacing them, and it runs to the wharf and no further
- [x] T021 Write failing tests in `test_settlement.py` for `s.aqueduct(...)`: an open channel with intake works, terminating at a point, recording a list - and NO arcade geometry anywhere
- [x] T022 Implement `s.aqueduct(...)` in `settlement.py`, its docstring carrying the open-outside/buried-inside finding and the explicit negative that no East Asian arcaded aqueduct exists
- [x] T023 In the gen, draw the wharf: dock, jetties, quay frontage, the domain granary behind it, and the merchant brokers' row in front
- [x] T024 In the gen, draw the towpath on the wharf's own bank, running to the wharf and stopping
- [x] T025 In the gen, draw the aqueduct: intake on the river, open channel to a gate; nothing inside the wall
- [x] T026 [P] Write failing tests in `test_checks.py` that no road parallels the river, that the aqueduct terminates at a gate, and that no open watercourse threads the walled interior
- [x] T027 [P] Implement those checks in `check_village.py`

---

## Phase 6: The keep-clear contract, for EVERY new key

- [x] T028 For each new manifest key: add to `_OVERLAP_STRUCTS`, give an `OVERLAP_CLASS`, give a `_LABEL_GROUP` caption group, and add to the canopy roofed/open-air registry - with a documented reason for any permitted overlap
- [x] T029 Run the classification ratchets and fix what they name: `every_feature_classified_for_overlap`, `every_feature_classified_for_matrix`, `every_solid_feature_classified_for_labels`, `test_every_roofed_feature_is_a_canopy_keepout`
- [x] T030 Confirm each new key is EXTRACTABLE: per the manifest, compare each classified key's record count against `matrix_extents`; any key with records and no extents is blind (the audit CLAUDE.md recommends re-running whenever a new key appears)

---

## Phase 7: The artifact gates

- [x] T031 Verify pool byte-identity: `git status --porcelain -- .claude/skills/diagram/pool/` MUST be empty
- [x] T032 **Launch `settlement-review` NOW**, scoped `DELTA: the ground-reserving layer added to the capital skeleton - government ward and ote-suji, Imperial Magistrate, granaries, eight lineage compounds, sovereign temples and teramachi rim, wharf works, towpath, aqueduct. Housing, wells, fire towers and the kido mesh are still deliberately absent.` Launch before the docs and the commit
- [x] T033 **Principle XII CLOSING GATE**: examine the rendered PNG against `specs/018-capital-space-budget/research.md` - the picture, not the code
- [x] T034 Act on the review's findings; re-render if anything moved

---

## Phase 8: Close out

- [x] T035 `python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy`
- [x] T036 Whole affected test files: `python3 -m pytest test_settlement.py test_checks.py test_villages.py -q -n auto --no-cov` - never `-k`
- [x] T037 `make done` ONCE, backgrounded, `cd <dir> && make done > /tmp/gate020.log 2>&1` and nothing more; read the log tail before believing green
- [x] T038 Update `settlements/capitals.md`'s STATUS banner and `wip/README.md` (what now ships; what 021 still owes; which review findings are cleared)
- [x] T039 Commit and run the stop-work ritual from the clone root

---

## Dependencies

```
Phase 1 -> Phase 2 (fix the blind bridging FIRST, before adding water)  [BLOCKING]
              -> Phase 3 (government ward)  [MVP]
                    -> Phase 4 (lineages, magistrate, temples)
                    -> Phase 5 (waterfront + aqueduct)   } 4 and 5 are independent
                          -> Phase 6 (contract) -> Phase 7 (artifact gates) -> Phase 8
```

Phases 4 and 5 touch different ground and can proceed in either order once Phase 3 lands.

## Implementation strategy

**Phase 2 first is deliberate.** This layer adds a wharf, a towpath and an aqueduct - all water-adjacent - and adding them on top of a bridging check that is known to be blind would compound the defect and make it harder to see.

**Phase 6 is not bookkeeping.** It is the phase that makes every feature above visible to the guardrails at all; feature 019 shipped a road through a castle because one record skipped it.

**The map ends this feature NOT GREEN**, and that is expected: population cannot pass until 021's housing. It stays a draft in `wip/`.
