# Implementation Plan: Gate Check Registry (targeted check execution)

**Branch**: `022-gate-check-registry` (no branch - `SPECIFY_FEATURE=022-gate-check-registry`) | **Date**: 2026-08-15 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/022-gate-check-registry/spec.md`

## Summary

Split `check_village.py`'s 12,944-line `gate()` into an ordered registry of segment functions
(one per legacy top-level statement, bodies moved verbatim, free variables as explicit
parameters), add `gate(M, only={base names})` that executes only the requested checks plus their
dependency closure, and switch the regression replay (791 fixtures) to targeted mode. Full-mode
behavior is preserved byte-for-byte (order = legacy textual order); a three-sweep oracle proves
it. Design and measured facts: [research.md](research.md). Expected payoff: the replay's ~61% of
suite CPU collapses (210 frozen whole-city fixtures currently pay a 2-6 s full gate each to
verify one check).

## Technical Context

**Language/Version**: Python 3.14 (container pin)

**Primary Dependencies**: stdlib only (`ast` for the one-shot transformer); pytest + pytest-xdist
+ pytest-cov for the gate

**Storage**: none new; regression fixture format unchanged

**Testing**: pytest via `make done` (ruff, format, mypy, pytest -n auto, 100% coverage);
feature-specific oracle sweeps (see quickstart.md)

**Target Platform**: dev container, Linux

**Project Type**: engine refactor inside `.claude/skills/diagram/`

**Performance Goals**: serial replay of the 210 large fixtures ≥5x faster; replay share of suite
CPU from ~61% to <25%; `make done` wall clock measurably down; recorded in timings.md

**Constraints**: full-mode verdicts, order, and stdout byte-identical on all 791 fixtures + 28
pool maps; no fixture format change; no module-level mutable state (xdist safety); check_village
stays under the 100% coverage gate

**Scale/Scope**: 604 segments, 549 unique check names, ~15.7k-line module; one-shot script-driven
transform + a small hand-written driver + replay/test updates

## Constitution Check

- **I. Accessibility-First Viewports**: N/A - no UI.
- **II. Bold, Intentional Design**: N/A - no UI.
- **III. Pool Data Conventions**: N/A - no pool content changes (fixture format untouched).
- **IV. One Canonical Home for GM Source**: N/A - no SOURCE blocks involved.
- **V. Protecting the GM's Writing**: PASS - no task touches SOURCE markers.
- **VI. Verify Before Reporting Done**: PASS - verification is the feature's core: baseline
  capture -> transform -> zero-diff compare, targeted-vs-full sweep, teeth check, `make done`,
  timings block. Steps enumerated in quickstart.md and tasks.
- **VII. De-Localized Generation by Default**: N/A - no generated content.
- **VIII. Direct Voice Over Framing Distance**: N/A - no in-world prose.
- **IX. Setting Integration**: N/A - no setting assertions.
- **X. Python Discipline**: PASS - ruff/format/mypy/pytest/coverage all hold (`make done`);
  red-first where new behavior exists (driver semantics: unknown-name error, meta-check refusal,
  targeted equivalence - tests written before the driver lands); no new deps. **Clause 12**: the
  feature EXISTS to discharge it; disposition of the one over-threshold extracted function
  (`city_has_six_ministries`, 2,390 lines) is an inline justification annotation with a recorded
  debt to split it later - see research.md R6 and Complexity Tracking.
- **XII. Historical Grounding Bookends**: N/A - the feature changes no assertion about the world;
  verdict identity on every existing manifest is the proof (nothing a map asserts changes).

**Post-design re-check (after Phase 1)**: unchanged - PASS/N/A as above; no new violations
introduced by the design.

## Project Structure

### Documentation (this feature)

```text
specs/022-gate-check-registry/
├── plan.md              # This file
├── research.md          # Phase 0: AST census, decomposition/targeting/oracle decisions
├── data-model.md        # Segment / context / targeted-request / meta-set / fixture
├── quickstart.md        # Oracle + gate commands
├── contracts/gate-api.md
├── transform_gate.py    # One-shot migration tool (analyzer + generator) - lives HERE, not in
│                        #   the skill dir; never imported by engine code (research.md R7)
├── oracle_sweep.py      # capture / compare / targeted sweeps (also one-shot, lives here)
└── tasks.md             # Phase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
.claude/skills/diagram/
├── check_village.py     # THE refactor target: prelude + driver gate() + ~600 segment functions
│                        #   + ordered registry + META_CHECKS constant
├── test_regressions.py  # replay switches to targeted mode (meta -> full fallback)
├── test_checks.py       # + registry pin tests (name set, order), driver unit tests
├── timings.md           # new ledger block after
└── CLAUDE.md            # check-authoring guidance updated (new checks = registry functions)
```

**Structure Decision**: single existing module refactored in place; migration tooling quarantined
in the feature directory so it can never be mistaken for engine code or fall under the coverage
gate.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| One extracted function (`city_has_six_ministries`) remains ~2,390 lines, over the clause-12 ~1,000 threshold, carrying the inline justification annotation | It is one cohesive ministry-complex audit; splitting it inside this feature adds hand-refactor risk to a mechanical, oracle-protected transform | Hand-splitting now was rejected because it converts a zero-diff verbatim move into a semantic rewrite of the largest single check, for no perf gain (recorded as debt in the annotation and research.md R6) |
