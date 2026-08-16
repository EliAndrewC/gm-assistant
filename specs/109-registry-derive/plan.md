# Implementation Plan: Derive the check_village Gate Registry

**Branch**: `109-registry-derive` (no branch; `SPECIFY_FEATURE=109-registry-derive`) | **Date**: 2026-08-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/109-registry-derive/spec.md`

## Summary

Replace the 8,432-line hand-maintained `check_village/registry.py` with a derived surface per
constitution clause 14. Every row field is reproducible from the segment modules themselves -
proven empirically by the two probes in this directory across all 1,367 rows: `free` is the
keyword-only signature (exact), `writes` is the literal `_kept` return tuple (exact),
`checks`/`meta`/`always` derive from the body AST (exact), `needs` derives from the
upward-exposed-reads analysis plus the via_helpers fixpoint (exact but one row), and order
derives from the numeric name key (exact but two rows). The three exceptions are genuine
decisions and stay as explicit data: a 2-entry `PLACEMENTS` table and a 1-entry
`NEEDS_OVERRIDES` table, each entry with its why. Derivation output is cached keyed by a hash
of the segment sources (feature 026 gencache precedent) so the ~1.4 s AST cost is paid only
when a segment file changes. The pre-collapse rows are frozen as a committed JSON fixture; a
by-name equality test plus structural guards (each proven to fire) hold the contract. Zero
consumer changes: `driver.py`, `__init__.py`, and the four test call sites are untouched.

## Technical Context

**Language/Version**: Python 3.14 (system, per constitution Technical Standards)

**Primary Dependencies**: stdlib only (`ast`, `inspect`, `json`, `hashlib`, `pathlib`); analysis
logic ported (with types) from `specs/022-gate-check-registry/transform_gate.py`

**Storage**: gitignored JSON derivation cache next to the package (atomic tempfile-rename
publish, per the gencache pattern); committed JSON frozen fixture under the diagram skill's
test fixtures

**Testing**: pytest (`-n auto`), pytest-cov at 100% on the new pure-logic modules; existing
diagram test bed as the behavioral oracle

**Target Platform**: dev container (Linux), same as the rest of the diagram skill

**Project Type**: library-internal refactor of the `/diagram` validator package

**Performance Goals**: warm import overhead < ~1 s over today (measured; cache hit path is a
hash + JSON load); cold (cache miss) re-derive ~1.4 s, paid only when segment sources change

**Constraints**: FR-002 exact row equality to the frozen fixture; FR-003 zero consumer changes;
no new dependencies; mypy --strict; ruff clean

**Scale/Scope**: 1,367 rows x 7 fields; 12 segment modules (~30k lines parsed); one file
replaced, two new modules, one test module, one fixture

## Constitution Check

- **I. Accessibility-First Viewports**: N/A - no UI.
- **II. Bold, Intentional Design**: N/A - no UI.
- **III. Pool Data Conventions**: N/A - no pool content.
- **IV. One Canonical Home for GM Source**: N/A - no SOURCE blocks touched.
- **V. Protecting the GM's Writing**: PASS - no task touches SOURCE-marked content.
- **VI. Verify Before Reporting Done**: PASS - verification per quickstart.md: fixture-equality
  + guard tests, full diagram test bed (regression corpus included) run once at the end, ruff +
  mypy --strict + 100% coverage on the new modules, measured import timing.
- **VII. De-Localized Generation**: N/A - no generated content.
- **VIII. Direct Voice**: N/A - no in-world prose.
- **IX. Setting Integration**: N/A - no setting content.
- **X. Python Discipline (NON-NEGOTIABLE)**: PASS - this feature IS a clause-14 application.
  Ruff/format/mypy --strict/pytest/100%-coverage on the new modules; red-green order: the
  fixture is frozen and the equality + guard tests written against the CURRENT file first (they
  must pass against it, and the guards' fire-proofs run red-then-green); clause 12: derivation
  functions stay small; clause 13: new modules well under 1,000 lines; clause 14 method followed
  in order (census done in research.md R1 -> guards -> derive -> full gate).
- **XI. Japanese Authenticity**: N/A - no kanji-bearing content.
- **XII. Historical Grounding Bookends (NON-NEGOTIABLE)**: N/A - no generator assertion about
  the world changes (research.md R8); SC-002 (identical gate results on the regression corpus)
  is the closing proof that map-facing behavior is untouched.

No DEFERRED gates; Complexity Tracking not needed.

## Project Structure

### Documentation (this feature)

```text
specs/109-registry-derive/
├── spec.md
├── plan.md               # this file
├── research.md           # probe findings R1-R9
├── data-model.md         # entities: rows, PLACEMENTS, NEEDS_OVERRIDES, cache, fixture
├── quickstart.md         # verification commands
├── contracts/registry-api.md
├── probe_derivation.py   # phase-0 probe (naive transform-style)
├── probe2_refined.py     # phase-0 probe (the design, 0 mismatches + 3 decided facts)
├── checklists/requirements.md
└── tasks.md              # /speckit-tasks output
```

### Source Code (working clone)

```text
.claude/skills/diagram/
├── check_village/
│   ├── registry.py            # REPLACED: ~150-line derived surface - _GateSeg, PLACEMENTS,
│   │                          #   NEEDS_OVERRIDES, assembly, META_CHECKS, _SEG_DEPS, cache use
│   ├── registry_analysis.py   # NEW: typed port of the 022 AST analysis (loads/stores/
│   │                          #   mutation targets/exposed reads/check census/helper fixpoint)
│   ├── segments_*.py          # UNTOUCHED (12 modules - the single source of truth)
│   ├── driver.py              # UNTOUCHED (FR-003)
│   ├── __init__.py            # UNTOUCHED (FR-003)
│   └── CLAUDE.md              # UPDATED: registry entry + add-a-segment workflow (FR-007)
├── test_registry_derive.py    # NEW: fixture equality, structural guards, cache round-trip,
│                              #   override/placement liveness, fire-proof perturbations
├── test_fixtures/registry_legacy_rows.json   # NEW: frozen pre-collapse rows (committed)
└── (gitignored) check_village derivation cache JSON
```

**Structure Decision**: two production modules keep both under clause-13 scale: `registry.py`
stays the import surface (same module path, so every consumer import line is untouched) and
holds the decided data + assembly; `registry_analysis.py` holds the ported pure-AST analysis,
independently testable to 100%. The fixture lives under the existing `test_fixtures/` directory
alongside the diagram skill's other saved fixtures. Cache location and gitignore entry follow
the gencache precedent (exact path decided at implementation against `gencache.py`'s layout).

## Phase-2 implementation order (input to /speckit-tasks)

1. **Freeze first**: generate `registry_legacy_rows.json` from the CURRENT registry; write
   `test_registry_derive.py`'s fixture-equality test so it passes against the current file
   (oracle sanity), plus the structural guards. Red-green: guards' fire-proofs (perturbations)
   run and are recorded BEFORE the swap.
2. **Port the analysis**: `registry_analysis.py`, typed, with unit tests to 100%.
3. **Build the derived registry**: assembly + PLACEMENTS + NEEDS_OVERRIDES + cache; swap
   `registry.py`; fixture equality must go green unchanged.
4. **Docs + budget**: package CLAUDE.md registry entry + add-a-segment workflow; measure import
   times; record everything.
5. **Full sweep once, at the end**: whole diagram test bed + ruff + mypy + coverage; docs and
   memory-note closeout (FR-010); stop-work ritual.
