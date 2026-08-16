# Tasks: Derive the check_village Gate Registry

**Input**: Design documents from `specs/109-registry-derive/` (plan.md, research.md,
data-model.md, contracts/registry-api.md, quickstart.md)

**Tests**: included - the feature is contract-preservation; the fixture/guard tests ARE the
feature's safety mechanism (spec US2, FR-004), and Principle X's red-green order applies.

All paths relative to the working clone `/gm-assistant/.clones/diagram-tokens/`.
Skill dir shorthand: `DIAG = .claude/skills/diagram`.

## Phase 1: Setup

- [x] T001 Sync-in: `git pull origin main` in the clone; confirm no competing `specs/109*` appeared and re-read any upstream changes to `DIAG/check_village/` (a peer session editing segments would move the derivation's inputs)

## Phase 2: Foundational (blocking)

- [x] T002 Freeze the legacy oracle: write and run a one-off script `specs/109-registry-derive/freeze_fixture.py` serializing the CURRENT `GATE_SEGMENTS` (per row: fn `__name__`, free, writes, checks, needs, meta, always) plus `META_CHECKS` to `DIAG/test_fixtures/registry_legacy_rows.json`; commit the fixture (FR-001)

## Phase 3: User Story 1 - derived registry with identical gate behavior (P1) - MVP

**Goal**: registry.py becomes a small derived surface; every derived row equals the frozen
fixture; zero consumer changes.

**Independent test**: `pytest DIAG/test_registry_derive.py DIAG/test_check_village_surface.py -n auto`
green with the swapped registry, then the full bed in the Polish phase.

- [x] T003 [US1] Write `DIAG/test_registry_derive.py` against the CURRENT registry: fixture-equality by name (all six fields), fixture order a subsequence of registry order, structural guards (unique names/keys, literal `_kept` return census, needs subset-of free, `META_CHECKS` = union over meta rows); run - must be GREEN pre-swap (oracle sanity; red-green discipline is satisfied by T007's fire-proofs)
- [x] T004 [P] [US1] Port the analysis to `DIAG/check_village/registry_analysis.py`, typed for mypy --strict, citing `specs/022-gate-check-registry/transform_gate.py` as provenance (FR-006): `_loads`/`_stores`/`_walk_shallow`/`_bound_anywhere`/`_mutation_targets`/`_free_loads`/`_exposed_reads`/`_check_names`/`_module_emissions` + the helper-mutation fixpoint; unit tests in `DIAG/test_registry_analysis.py` to 100% coverage
- [x] T005 [US1] Replace `DIAG/check_village/registry.py` with the derived surface: module scan of `segments_*` for `_seg_*` fns; free from kwonly signature; writes from the literal `_kept` return tuple; needs/checks/meta/always via `registry_analysis`; `PLACEMENTS` (2 entries: `_seg_0595` after `_seg_0532`, `_seg_0596` after `_seg_0317`, each with its why) and `NEEDS_OVERRIDES` (1 entry: `_seg_0324_500`, why inline per research.md R5); derive-time validation asserts (data-model.md rules 1-6); `META_CHECKS` + `_SEG_DEPS` assembled as today; record-the-why module docstring (FR-006); consumer files untouched (FR-003)
- [x] T006 [US1] Add the source-hash derivation cache per the gencache precedent: gitignored JSON beside the package, atomic tempfile-rename publish, failure-soft load, fn re-bind by name, cache round-trip guard test in `DIAG/test_registry_derive.py`; then measure and record cold/warm import times in `specs/109-registry-derive/research.md` (FR-009, budget < ~1 s warm overhead)

## Phase 4: User Story 2 - guards proven to fire (P2)

**Goal**: every guard demonstrably fails on a violated contract (FR-004, SC-003).

- [x] T007 [US2] Fire-proof each guard red-then-green and record the evidence table below: (a) swap the two PLACEMENTS anchors -> order guard fails; (b) drop a name from the `_seg_0324_500` override -> fixture equality fails naming segment+field; (c) monkeypatch derivation to flip one row's meta -> equality + META_CHECKS guards fail; (d) hide one segment from the module scan -> missing-segment guard fails; (e) corrupt the cache file -> import still succeeds via re-derive (failure-soft proof); restore after each

## Phase 5: User Story 3 - add-a-segment workflow stays documented (P3)

**Goal**: package CLAUDE.md describes the derived design and the new-segment path.

- [x] T008 [US3] Update `DIAG/check_village/CLAUDE.md`: registry entry now describes the derived surface (load registry.py when changing placements/overrides/derivation; registry_analysis.py when changing the AST model); rewrite the add-a-segment workflow (write the function with kwonly sig + literal `_kept` return; position via sub-numbered name, PLACEMENTS only when the name is already taken); sweep other docs: `grep -rn "registry.py" DIAG/CLAUDE.md DIAG/check_village/CLAUDE.md docs/` and fix stale descriptions (FR-007)
- [x] T009 [US3] Dry-run the documented workflow: add a temporary no-op `_seg_0596_500__scratch` per the new CLAUDE.md text, assert it derives at the intended position with correct fields, then revert the scratch segment (spec US3 acceptance)

## Phase 6: Polish & Cross-Cutting

- [x] T010 Full sweep once, at the end (MANDATORY - shared code changed): `ruff check` + `ruff format --check` + `mypy --strict` on `DIAG/check_village` and the new test modules; whole diagram test bed `pytest DIAG -n auto` with coverage 100% on `registry_analysis.py` and the new `registry.py`; background the final run, act on the notification, tail the log before believing green
- [x] T011 Close out: update the `registry_refactor_deferred` memory note (superseded by 109, FR-010); update `specs/109-registry-derive/` artifacts with final numbers; commit; run `scripts/sync-with-main.sh done` from the clone (stop-work ritual)

## Guard fire-proof evidence (T007)

The fire-proofs are PERMANENT TESTS in `test_registry_derive.py` (better than one-off manual
perturbation runs - they re-prove the guards every gate), all green 2026-08-16:

| Perturbation | Guard proven to fire |
|---|---|
| (a) placement anchors swapped / stale entry / missing anchor / cycle / dup key | `test_order_guard_fires_on_*` (5 tests: divergent order or `_DerivationError`) |
| (b) needs name dropped, meta flipped, segment missing | `test_equality_guard_fires_on_*` (3 tests: `_diff_rows` names segment+field) |
| (c) needs override dropped or stale or outside free | `test_dropping_the_needs_override_diverges_from_the_fixture`, `test_derive_guard_fires_on_*` |
| (d) segment shape violated (computed/missing/non-string `_kept` tuple, dup def) | `test_segment_shape_guard_fires_on_*` + `test_derive_guard_fires_on_duplicate_segment_def` |
| (e) cache corrupted / stale key / moved segment set / unwritable dir | `test_cache_round_trip_and_failure_soft`, `test_cache_store_is_failure_soft_when_unwritable` (import re-derives; store only logs) |

T009 dry-run evidence: `_seg_0533_500__scratch_dry_run` derived between `_seg_0533___flow_dir`
and `_seg_0534___drains` with fields `free=('check',) writes=() checks=('scratch_dry_run',)`,
no registry edit; reverted. Caveat found and documented in check_village/CLAUDE.md: sub-numbering
cannot place a segment beside a PLACED segment (0595-0600) - that takes a `_PLACEMENTS` entry.

## Dependencies

- T001 -> T002 -> T003 -> T005 (fixture and oracle tests precede the swap; red-green)
- T004 [P] parallel with T003 (different files); T005 needs T003+T004; T006 needs T005
- US2 (T007) needs T005/T006; US3 (T008, T009) needs T005; T009 needs T008
- T010 needs everything; T011 last

## Implementation strategy

MVP = US1 (T001-T006): the collapse itself, fixture-proven. US2 hardens, US3 documents - both
same-session. Single implementer; [P] marks the one genuinely parallel authoring opportunity
(T004 vs T003). Commit at each phase boundary; the stop-work ritual runs only at T011.
