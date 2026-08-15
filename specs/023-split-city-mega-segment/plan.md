# Implementation Plan: Split the City Mega-Segment

**Branch**: `main` (session-clone workflow, `SPECIFY_FEATURE=023-split-city-mega-segment`) | **Date**: 2026-08-15 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/023-split-city-mega-segment/spec.md`

## Summary

`_seg_0563__city_has_six_ministries` (3,607 lines, 1,040 logical statements, 148 check names -
the whole city/capital urban battery) is the one function feature 022 left past constitution
Principle X clause 12's ~1,000-statement defect line, under an inline annotation recording the
split as debt. This feature pays the debt: a one-shot transformer (recursing the proven 022
recipe one guard level deeper) replaces the mega-segment with ~378 per-statement segment
functions in the same registry position, bodies verbatim, guards preserved, dataflow re-derived
with the same analysis code 022 validated - then the full 022 oracle battery (full-mode byte
identity, targeted-vs-full, teeth check) proves nothing observable moved.

## Technical Context

**Language/Version**: Python 3.14 (container pin)

**Primary Dependencies**: stdlib `ast` only for the transformer; pytest + pytest-cov +
pytest-xdist for the gate. No new dependencies.

**Storage**: N/A (source transformation of `check_village.py`; frozen fixtures under
`pool/regressions/` are read-only oracle inputs)

**Testing**: `make done` in `.claude/skills/diagram/` (ruff + format check + mypy strict, ratchet
fully retired + pytest with 100% coverage over check_village et al.); 022 oracle sweeps
(`specs/022-gate-check-registry/oracle_sweep.py` - reused as-is, it needs no changes)

**Target Platform**: the dev container (linux, 22 cpus)

**Project Type**: engine refactor inside the /diagram skill - one file (`check_village.py`,
~31k lines) plus one-shot tooling in this feature dir

**Performance Goals**: regression replay wall time within ~10% of baseline (expected: faster -
city closures no longer execute the whole 1,040-statement battery); module import time not
materially regressed despite `_SEG_DEPS` being O(n^2) in registry rows (586 -> ~960)

**Constraints**: verdict byte-identity on all 814 manifests (full mode); targeted-vs-full
identity on all 791 fixtures; zero check names added/removed/renamed; execution order preserved
by construction; no check semantics change (latent bugs recorded, deferred)

**Scale/Scope**: 1 mega-segment -> ~83 outer-guard segments + ~295 walled-guard segments; one
registry row -> ~378 rows; 27 nested helper defs re-censused for stale-cell hazards

## Constitution Check

- **I. Accessibility-First Viewports**: N/A - no UI touched.
- **II. Bold, Intentional Design**: N/A - no UI surfaces.
- **III. Pool Data Conventions**: N/A - no generated pool content; frozen regression fixtures
  are read-only inputs.
- **IV. One Canonical Home for GM Source**: N/A - no SOURCE blocks involved.
- **V. Protecting the GM's Writing (NON-NEGOTIABLE)**: PASS - no task touches SOURCE markers;
  the record-the-why comment banks between statements are preserved verbatim by the transformer
  (gap emission, same as 022).
- **VI. Verify Before Reporting Done**: PASS - verification is the feature's core: oracle
  capture/compare (full-mode byte identity), targeted sweep, teeth check, whole affected test
  files, then `make done` backgrounded. Listed per task in tasks.md.
- **VII. De-Localized Generation by Default**: N/A - no content generation.
- **VIII. Direct Voice Over Framing Distance**: N/A - no in-world prose.
- **IX. Setting Integration**: N/A - no setting details created or changed.
- **X. Python Discipline (NON-NEGOTIABLE)**: PASS - ruff + format + mypy strict (no ratchet
  left in this package) + pytest + 100% coverage all must stay green; bodies move verbatim so
  coverage of moved lines is unchanged; new wrapper lines are executed by the same fixtures
  that executed the mega-segment. Clause 12 is the MOTIVATION: post-split, no function in
  check_village.py exceeds ~400 statements (measured leaf max: 51), and the one clause-12
  annotation in the codebase is deleted along with its debt. TDD note: this is a
  behavior-preserving mechanical transformation - the "test that fails first" is the oracle
  baseline captured BEFORE the transform runs (red = any diff), plus the teeth check proving
  the replay still bites; no new behavior is introduced to TDD against.
- **XII. Historical Grounding Bookends (NON-NEGOTIABLE)**: N/A - the feature changes no
  assertion any generator makes about the world; verdict identity on every fixture is the
  explicit contract and is machine-checked (spec FR-003/FR-004).

Post-Phase-1 re-check: unchanged - the design introduces no UI, no content, no new dependency,
and no function above clause-12 scale. No Complexity Tracking entries needed.

## Project Structure

### Documentation (this feature)

```text
specs/023-split-city-mega-segment/
├── plan.md              # This file
├── research.md          # Phase 0: census, split model, guard semantics, risks
├── data-model.md        # Phase 1: transformer entities and registry row model
├── quickstart.md        # Phase 1: how to run the transformer + oracle battery
└── tasks.md             # Phase 2 (/speckit-tasks)
```

No `contracts/` dir: the feature exposes no new external interface - `gate(M, only=...)`'s
signature and semantics are explicitly unchanged (spec FR-004); the registry row shape
(`_GateSeg`) is unchanged.

### Source Code (repository root)

```text
.claude/skills/diagram/
├── check_village.py                      # THE artifact: mega-segment replaced in place
├── test_checks.py                        # registry-pin test (gate_check_names.json) - unchanged assertion
├── test_regressions.py                   # targeted replay - unchanged
└── test_fixtures/gate_check_names.json   # frozen name list - MUST come out byte-identical

specs/023-split-city-mega-segment/
└── split_megaseg.py                      # one-shot transformer (imports 022's analysis helpers)

specs/022-gate-check-registry/
├── transform_gate.py                     # imported for its analysis functions (not re-run)
└── oracle_sweep.py                       # reused verbatim: capture / compare / targeted
```

**Structure Decision**: the transformer is one-shot migration tooling and lives in THIS feature's
dir (022's R7 lifecycle rule); it imports 022's proven analysis helpers rather than copying
them. `check_village.py` remains the hand-maintained source of truth the moment the transform
lands; both transformers stay retired afterwards.

## Complexity Tracking

No constitution violations to justify. (The feature RETIRES the codebase's only clause-12
Complexity Tracking debt, recorded in specs/022 plan.md.)
