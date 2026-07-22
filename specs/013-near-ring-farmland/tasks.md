---
description: "Task list for Near-Ring Farmland Density"
---

# Tasks: Near-Ring Farmland Density (towns and provincial cities)

**Input**: Design documents from `specs/013-near-ring-farmland/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md (all present)

**Tests**: INCLUDED - Principle X (NON-NEGOTIABLE) mandates red-green TDD for new non-trivial behavior, and FR-010 requires a saved negative regression fixture. Test tasks are therefore not optional here.

**Working location**: the session clone `.clones/diagram-town`, inside `.claude/skills/diagram/`. Never run generators or tests against main `/gm-assistant`. All paths below are relative to `.claude/skills/diagram/` unless noted.

**Format**: `[ID] [P?] [Story?] Description with file path` - `[P]` = parallelizable (different files, no incomplete-task dependency).

**Note on line numbers**: a large diagram-engine change from another session merged after the plan was written, so the plan's approximate line refs (e.g. `~:1336`) have shifted. T004 re-locates the real anchors before any engine edit.

---

## Phase 1: Setup (doctrine + why) - docs-only, no gate

**Purpose**: record the near-ring-density rule and its historical grounding first (the GM emphasized "starting with the documentation of these findings"). Independent of all code; blocks nothing but is the canonical home for the Principle XII "why."

- [X] T001 Add the near-ring-density doctrine to `settlements.md`: the rule (fill the flat near ring with cultivated cover; scrub retreats to frame margins + non-arable ground; quilt not monoculture; topography governs; tunable, dense default) in the Towns and Provincial-cities sections, plus a "Historical grounding: near-ring farmland" subsection carrying research.md Part A (site selection, von Thünen intensity gradient, labor-limited fallow relocation, the polycultural quilt, topography) and the calibrated-liberty disclosure on the *degree* of density.
- [X] T002 In `settlements.md`, revise the existing "We do not draw all the farmland. A town's fields are a representative sample; the rest is implied off-map" line so it is narrowed to the FAR countryside: the near-ring flat ground now reads as packed cultivation, while the far countryside is implied off-map and at least one field still runs off the edge. Keep the off-edge-field requirement intact.

**Checkpoint**: the "why" exists in its canonical home before any rule references it.

---

## Phase 2: Foundational (shared engine) - BLOCKS all user stories

**Purpose**: the tunable knob, the derived near-ring band, the channel-free fill method, the coverage check, and the dry-plot hill guard - the machinery every map redesign consumes. No map redesign may begin until this phase is green and 100%-covered.

**CRITICAL**: US1/US2/US3 cannot start until Phase 2 completes.

- [X] T003 [P] Write the failing check test + negative fixture (RED): add `test_near_ring_cultivated_fraction_fires_on_sparse_town` (and a city case) to `test_checks.py`, and save the current undensified Hirameki manifest as `pool/regressions/near_ring_cultivated_fraction_fires_on_sparse_hirameki.json` (regenerate Hirameki's manifest as-is first). Assert the (not-yet-existing) check FIRES on the sparse `"dense"`-declared manifest. Confirm it fails/errors before T008 lands.
- [X] T004 Re-locate the current engine anchors after the upstream merge: grep `settlement.py` for `comb_base_fill`, the `meta(` reader, `_urban_keepouts`, `in_ellipse(...,`, `M["hill"]`; grep `waterfields.py` for `_dry_fields`; grep `check_village.py` for `town_margins_clothed` / `margins_form_continuous_ring` / `no_field_on_hill`. Record the real line numbers in a scratch note for T005-T009 (no file edit).
- [X] T005 Implement the flat near-ring band derivation as a pure helper in `settlement.py` (frame minus inflated hill `in_ellipse(x,y,M["hill"],1.45)`, minus wet-toe/marsh + watercourse `block_polys`, minus moat/streams/channels, minus wall interior on a walled map, minus the 30-ft urban halo `_urban_keepouts`, minus existing field envelopes/corridors). Returns the sampleable region used by both the fill and the check. Decide here whether an explicit radius clamp is needed or the in-frame flat complement suffices (data-model.md leans to the latter).
- [X] T006 Implement `s.near_ring_cropland(density=..., *, ring_farms=..., seed=..., avoid=())` in `settlement.py` (near the relocated `comb_base_fill`), tiling channel-free dry-field + garden plots over the T005 band, honoring the "~1 in 6" `DRY_CROPS` mix, skipping every keep-out, recording each plot into `M["dry_plots"]` + `s.dry_polys`; optional farmstead ringing via existing `ring()`/`try_place`. Draws NO water. Reuse/lift the `_dry_fields` tiling from `waterfields.py` as a channel-free bbox-driven variant if cleaner than inlining.
- [X] T007 Add the `meta(near_ring_density=<tier>)` read (via `meta.get("near_ring_density", "dense")`) and the tier->threshold mapping (`dense`/`medium`/`thin`) in `settlement.py` / `check_village.py` as appropriate; unknown value fails loud. Put a record-the-why comment beside the default and the threshold constant pointing at research.md Part A + the calibrated-liberty disclosure.
- [X] T008 Implement the `near_ring_cultivated_fraction` check in `check_village.py` (GREEN for T003): clone the `town_margins_clothed` 25px grid-sampler, restrict the sampled cells to the T005 near-ring band, count only CULTIVATED cover (paddy + vegetable `fields`, `dry_plots`, `gardens`), require cultivated-fraction >= `threshold(near_ring_density)`; town+city scope only; failure detail reports measured fraction, threshold, declared tier, and the fix. Confirm T003 now passes on a synthetic dense manifest and still fires on the sparse fixture.
- [X] T009 Close the dry-plot hill gap flagged in the recon: `no_field_on_hill` currently checks only `M["fields"]`; add/extend a guard (e.g. `dry_plots_off_hill`) so tiled dry plots also stay off `in_ellipse(x,y,M["hill"])`, with its own negative fixture in `pool/regressions/`.
- [X] T010 [P] Unit-test the T005 band geometry and the T006 tiler in `test_settlement.py` (behavior-named, parametrized: keep-outs respected, hill/water/wall/urban-halo excluded, density tiers yield monotonically different coverage) to restore 100% line coverage on the touched pure-logic paths.

**Checkpoint**: `pytest` + 100% cov green on the diagram package; the check fires on sparse and passes on dense synthetic manifests; no map redesigned yet.

---

## Phase 3: User Story 1 - Well-sited TOWN reads as packed farmland (Priority: P1) 🎯 MVP

**Goal**: Hirameki (town) renders embedded in packed near-ring farmland; scrub only at margins/hill/wet-toe; the full gate green.

**Independent Test**: regenerate Hirameki; by eye it reads "town embedded in farmland"; `near_ring_cultivated_fraction` + every existing check pass; town + water + roads + caste layout unchanged.

- [X] T011 [US1] Redesign `pool/towns/hirameki.gen.py`: drop the near-ring `s.commons([...])` grazing polys (keep only true frame-margin scrub), call `s.near_ring_cropland(...)` after the five paddy combs, optionally ring the new fill with farmsteads. Leave paddy combs, water, roads, manor, monasteries, and caste packs intact.
- [X] T012 [US1] Iterate single-map regen + gate on Hirameki until packed AND green: `near_ring_cultivated_fraction`, `town_margins_clothed`, `scrub_clear_of_urban_fabric`, all overlap/water/off-edge checks. Fix collisions via the band keep-outs, not by re-adding scrub.
- [X] T013 [US1] Re-reconcile town population: if T011 added farmhouses, adjust `meta(population=...)` in `hirameki.gen.py` so `town_caste_count` / `households_consistent` / `town_farmers_plurality` stay in band (plurality is only helped). Dry fields + gardens house no one and do not affect the figure.
- [X] T014 [US1] Principle XII spot-review of the rendered `pool/towns/hirameki.png` (the PNG, not the code): confirm Element 1 (near ring reads cultivated), Element 2 (scrub only at margins/hill/wet-toe), Element 3 (quilt: paddy + dry fields + gardens, not monoculture), Element 4 (no paddy/field on a slope). Record the outcome in Hirameki's review log.

**Checkpoint**: MVP - a well-sited town reads packed and passes every check; the machinery is proven on a real map.

---

## Phase 4: User Story 2 - Well-sited provincial CITY reads the same way (Priority: P2)

**Goal**: Tango (walled city) renders with a packed near ring OUTSIDE the wall; walls/moat/bridges/gates/ward-fences/compounds unchanged; the city gate green.

**Independent Test**: regenerate Tango; the flat ground outside the wall reads predominantly cultivated; no field/farmstead/cover crosses the wall or moat; every gate approach still bridges the moat; city gate green.

- [X] T015 [US2] Redesign `pool/provincial-cities/tango.gen.py`: apply `s.near_ring_cropland(...)` to the flat ground OUTSIDE the wall, drop/trim the outside near-ring scrub, respect the moat/wall/gates/ward fences and the segregated burakumin quarter + gate market outside the wall. Leave the in-wall agricultural district and the government compounds intact.
- [X] T016 [US2] Iterate single-map regen + gate on Tango until packed AND green: `near_ring_cultivated_fraction` (city scope) plus `city_has_outside_farmland`, `city_fields_close_to_city`, `roads_bridge_water`, wall/moat overlap checks, and the city caste/density checks. City farmhouses do NOT touch the population figure, so ring as densely as the view needs.
- [X] T017 [US2] Principle XII spot-review of the rendered `pool/provincial-cities/tango.png`: confirm Elements 1-4 hold outside the wall and nothing crosses the wall/moat. Record the outcome in Tango's review log.

**Checkpoint**: both a town and a city read packed and pass independently.

---

## Phase 5: User Story 3 - Hinterland intensity is tunable per map (Priority: P3)

**Goal**: a map declaring `meta(near_ring_density="thin")` renders a visibly thinner, scrubbier near ring than the dense default, and both pass the gate.

**Independent Test**: generate one dense-default and one thin map; the thin near ring is visibly less cultivated; both pass `near_ring_cultivated_fraction` at their respective thresholds.

- [X] T018 [US3] Choose the dial-down demonstrator: either add a small `meta(near_ring_density="thin")` variant/gen for a dry-locale town, or set the tier on a suitable existing dry map. Confirm the thin threshold lets a genuinely marginal near ring pass while the dense threshold would have failed it.
- [X] T019 [US3] Iterate regen + gate on the thin map until green, and confirm the dense default (Hirameki/Tango) still passes - i.e. the knob moves the requirement in both directions and a `"dense"`-declared map cannot pass while sparse (the check's teeth).
- [X] T020 [US3] Principle XII spot-review: the thin map's near ring reads visibly thinner/scrubbier than the dense default (Element 5). Record the outcome.

**Checkpoint**: all three stories independently functional; the calibrated-liberty range is represented in the product.

---

## Phase 6: Polish & Cross-Cutting (MANDATORY for a shared-engine change)

**Purpose**: prove the engine change is safe across the whole pool and close the Principle XII gate.

- [X] T021 Full-pool sweep (MANDATORY): from `.claude/skills/diagram/`, run `make done` (regenerate every pool map + ruff + `ruff format --check` + `mypy --strict` + `pytest` + `--cov-fail-under=100` + the full `check_village` gate over every map). Background it if long; report done only when green.
- [X] T022 Verify scope isolation (SC-005): confirm village + hamlet maps are behavior-unchanged (they never call the new method and are out of scope) - their tracked `.json` manifests must not move. Spot-check Hoshizora (2nd town) and Nagahara (2nd city) either stayed clean or were intentionally adjusted, and fix any downstream map the engine change disturbed.
- [X] T023 Principle XII CLOSING gate (full pass, before "done"): review the rendered PNGs of Hirameki, Tango, the thin map, Hoshizora, and Nagahara against research.md Elements 1-5 (this is separate from the automated gate - a map can pass every check and still depict something ahistorical). If any picture contradicts an element, fix the MAP, do not rationalize the code. Record each review outcome in the map review logs.
- [X] T024 Confirm SC-006: the "why" is present in `settlements.md` (Historical grounding) AND beside the threshold constant / knob default in code; verify with a grep.
- [X] T025 Stop-work ritual: commit all clone work with a descriptive message; run `bash scripts/sync-with-main.sh done` from the clone root (locked pull+push back to main + render-sync). Do NOT re-run the gate for any docs-only follow-up.

---

## Dependencies & Execution Order

- **Phase 1 (Setup / doctrine)**: no dependencies; docs-only; can be done anytime, ideally first.
- **Phase 2 (Foundational)**: T003 (RED test + fixture) and T004 (anchor recon) first; T005 before T006 and T008 (both consume the band); T007 before/with T008 (threshold); T006/T008/T009 land GREEN; T010 restores coverage. **Blocks all user stories.**
- **Phase 3 (US1, P1 / MVP)**: after Phase 2. T011 -> T012 -> T013 -> T014.
- **Phase 4 (US2, P2)**: after Phase 2 (independent of US1, but sequenced after it for a clean MVP-first path). T015 -> T016 -> T017.
- **Phase 5 (US3, P3)**: after Phase 2 (independent). T018 -> T019 -> T020.
- **Phase 6 (Polish)**: after all desired user stories. T021 -> T022 -> T023 -> T024 -> T025.

### Within a user story

Redesign gen -> iterate regen+gate to green -> (town only) reconcile population -> Principle XII spot-review of the PNG.

### Parallel opportunities

- T003 and T004 are parallel (`[P]`): different concerns (test/fixture vs read-only recon).
- T010 (`[P]`) unit tests can be written alongside T006/T008 once their signatures are fixed.
- The three user stories are technically independent once Phase 2 is done, so US1/US2/US3 could be staffed in parallel - but the single-map red/green loop is cheap, so the recommended path is sequential MVP-first (US1 fully green before US2).

---

## Implementation Strategy

**MVP = Phase 1 + Phase 2 + Phase 3 (US1).** That delivers the GM's core ask - a well-sited town embedded in packed farmland - on a real, gated, historically-reviewed map. Stop and validate there before US2/US3.

**Incremental**: US1 (town) -> US2 (city) -> US3 (tunability) -> Polish (full-pool sweep + XII closing gate). Each map redesign is an independently gated increment; the shared engine is built once in Phase 2.

**Iteration discipline** (per quickstart.md + the repo's iteration-efficiency doctrine): iterate the red/green loop on the ONE motivating map (single-map regen + gate ~1-7s); reserve the full-pool `make done` sweep for Phase 6, where it is MANDATORY because shared engine code changed. Do not use the full suite as the first verification of an engine change.

---

## Notes

- `[P]` = different files, no incomplete-task dependency.
- Tests precede implementation (T003 before T008); verify RED before GREEN.
- The Principle XII closing gate (T014, T017, T020, T023) reviews the PNG, not the code - it is non-negotiable and separate from `check_village`.
- Commit after each logical group; the final sync back to main is T025 (never force-push).
- No `contracts/` directory: the internal "contracts" (knob, method, check signatures) live in data-model.md.
