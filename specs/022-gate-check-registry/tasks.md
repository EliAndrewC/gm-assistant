# Tasks: Gate Check Registry (targeted check execution)

**Input**: spec.md, plan.md, research.md, data-model.md, contracts/gate-api.md, quickstart.md
**Feature**: `022-gate-check-registry` | **Date**: 2026-08-15

All engine paths relative to `.claude/skills/diagram/`; feature paths relative to
`specs/022-gate-check-registry/`. Every task's verification is named inline (Principle VI).

## Phase 1: Setup

- [x] T001 Write `specs/022-gate-check-registry/oracle_sweep.py` (modes: `capture <out>`,
      `compare <baseline>`, `targeted`) per quickstart.md, and run `capture` on the UNTOUCHED
      engine to freeze the baseline (sorted verdicts + stdout sha256 for all 791
      `pool/regressions/*.json` + all 28 pool manifests) to the session scratchpad.
      Verify: baseline file lists 819 manifests, no errors.

## Phase 2: Foundational (blocking)

- [x] T002 [P] Write the analyzer half of `specs/022-gate-check-registry/transform_gate.py`:
      census gate()'s top-level statements into segments with (line span, free names = loads minus
      same-statement stores, writes INCLUDING mutation-as-write per research.md R3 rule 1, literal
      + static-f-string-base check names, meta flag for `_ran`/`_waived`/`fails` readers).
      Verify: census totals match research.md R1 (604 statements, 216 literal-check statements,
      549 unique names, 11 dynamic sites); every legacy check name appears in exactly >=1 segment.
- [x] T003 [P] Red tests first in `.claude/skills/diagram/test_checks.py`: (a) `gate(M,
      only={"nonexistent_check"})` raises ValueError naming it; (b) requesting a META_CHECKS name
      raises ValueError; (c) targeted run on a small synthetic manifest returns the same verdict
      as the full run for the requested name; (d) the registry's base-name set equals the frozen
      legacy 549-name list (stored as a fixture constant emitted by the T002 census); (e)
      `META_CHECKS` exists and contains the waiver meta-checks. Verify: all new tests FAIL (red)
      against the untouched engine.

## Phase 3: User Story 1 - Targeted check execution (P1)

**Goal**: `gate(M, only=...)` with verdicts identical to the full gate; full mode byte-identical.
**Independent test**: oracle sweeps 1 (full-mode compare) and 2 (targeted-vs-full) both zero-diff.

- [x] T004 [US1] Write the generator half of `specs/022-gate-check-registry/transform_gate.py`:
      emit the new `.claude/skills/diagram/check_village.py` - module prelude unchanged, segment
      functions with verbatim dedented bodies + `{k: v for k, v in locals().items() if k in
      _W_nnn}` returns, the ordered `GATE_SEGMENTS` registry with (fn, free, writes, checks,
      meta), `META_CHECKS`, and the new driver `gate(M, verbose, only)` (prelude, namespace dict,
      full mode = all segments in order; only mode = check-segment selection + transitive closure
      in order; ValueError on unknown/meta names). Verify: generated module imports; `ruff format`
      + `ruff check` + `mypy` pass.
- [x] T005 [US1] Run oracle sweep 1: `oracle_sweep.py compare <baseline>` - zero diffs on all 819
      manifests (verdicts AND stdout hashes). Iterate on the transformer (never hand-edit
      generated bodies) until zero. Verify: "IDENTICAL" on all manifests.
- [x] T006 [US1] Run oracle sweep 2: `oracle_sweep.py targeted` - for every fixture, targeted
      verdicts for its fires' base names equal the full run's. T003's tests now green. Verify:
      zero mismatches; `pytest test_checks.py -q -n auto --no-cov` green.

## Phase 4: User Story 2 - Replay switches to targeted mode (P2)

**Goal**: the 791-fixture replay verifies via `only=`, meta fixtures fall back to full.
**Independent test**: replay green in targeted mode; neutered checks still turn it red.

- [x] T007 [US2] Switch `.claude/skills/diagram/test_regressions.py` (both the pytest path and
      `__main__`) to targeted mode with META_CHECKS full-gate fallback; count and report how many
      fixtures actually hit the fallback. Verify: `pytest test_regressions.py -q -n auto --no-cov`
      all 791 pass.
- [x] T008 [US2] Teeth check + measurement: temporarily invert 3 sampled checks spanning small and
      >50KB fixtures - their fixtures MUST go red in targeted mode; restore. Then time the serial
      replay of the 210 >50KB fixtures before/after (baseline numbers in research.md R1). Verify:
      >=5x on the large-fixture cohort, else diagnose before proceeding.

## Phase 5: User Story 3 - Human-scale functions (P3)

**Goal**: clause 12 discharged; registry is the module's structure.
**Independent test**: statement-count audit of the new module.

- [x] T009 [US3] Audit function sizes in the generated `.claude/skills/diagram/check_village.py`
      (logical statements, not lines); add the clause-12 inline justification annotation to
      `city_has_six_ministries` (cohesive ministry-complex audit; split recorded as debt); confirm
      the driver and all other functions are under threshold. Verify: audit output clean except
      the one annotated function.

## Final Phase: Polish & Cross-Cutting

- [x] T010 Run the pre-gate ritual then `make done` (backgrounded, log tailed): ruff format/check,
      mypy, whole test files touched (`test_checks.py test_regressions.py test_villages.py`), then
      the full gate ONCE. Verify: gate green including 100% coverage.
- [x] T011 Re-measure and append the ledger block: `python3 timings.py --note "regression replay
      switched to targeted check execution"` in `.claude/skills/diagram/timings.md`. Verify: block
      appended; replay share and full_gate wall recorded.
- [x] T012 [P] Docs: update `.claude/skills/diagram/CLAUDE.md` (adding a check now = writing a
      registry function; replay runs targeted; retire the stale "huge gate() scope" mypy-collision
      note) and fix the stale constitution reference in root `CLAUDE.md` ("v1.1.0, 10 principles"
      -> v1.5.0, 12 principles, 5 NON-NEGOTIABLE). Verify: grep confirms no stale references.
- [x] T013 Close out: tick all boxes here, update spec status, commit in the clone, run
      `scripts/sync-with-main.sh done`. Verify: main fast-forwarded, render-sync clean.

## Dependencies & Execution Order

- T001 blocks T005 (baseline must precede any engine change). T002 and T003 are [P] with each
  other and with T001.
- T004 -> T005 -> T006 strictly ordered; T007 -> T008; T009 after T005 (needs the generated
  module); T010-T013 last, T012 [P] with T011.
- MVP = Phase 3 (US1): targeted execution proven identical is already shippable; US2 delivers the
  payoff; US3 + polish complete the constitution discharge and the record.

## Implementation Strategy

Never hand-edit generated segment bodies - fix the TRANSFORMER and regenerate (the oracle makes
iteration safe and cheap). The moment the oracle is green and the feature lands, the generated
file becomes the hand-maintained source of truth and the transformer is retired (research.md R7).
