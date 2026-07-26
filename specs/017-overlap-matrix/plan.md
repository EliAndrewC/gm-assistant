# Implementation Plan: The Overlap Matrix

**Branch**: `main` (session-clone workflow) | **Date**: 2026-07-26 | **Spec**: [spec.md](./spec.md)

## Summary

Replace the hand-written per-pair overlap rules with a **class-based policy matrix**. Every
geometric feature key gets one overlap class; a class-by-class policy (forbidden by default, every
permission carrying its reason) decides every pair at once; a parent-scoped exemption covers annexes
and in-field ditches more precisely than the blanket exemptions it replaces. A ratchet test fails by
name when a key has no class.

The correctness pivot is **drawn extents, not envelopes** - see [data-model.md](./data-model.md) §4.
Testing envelopes is what produced roughly half of the 101 false positives in the survey.

## Technical Context

**Language**: Python 3.14. **Files**: `check_village.py` (the matrix, the check, the ratchet),
`settlement.py` only if a drawn extent turns out not to be recorded, `test_checks.py` /
`test_settlement.py`, `pool/regressions/*.json`. **Testing**: `make done` - ruff, mypy,
`pytest -n auto`, 100% coverage. **Constraint**: every existing pool map must still pass, and every
permission must be a recorded judgment rather than a silenced failure.

## Constitution Check

- **I. Accessibility-First Viewports** - **N/A**. No web UI.
- **II. Bold, Intentional Design** - **N/A**. No new UI surface.
- **III. Pool Data Conventions** - **PASS**. New negative fixtures go to `pool/regressions/` with `_regression` blocks; no pool content format changes.
- **IV / V. GM source** - **PASS**. No SOURCE blocks touched; nothing written to `l7r.md`.
- **VI. Verify Before Reporting Done** - **PASS**. Cheap linters, then whole affected test files, then `make done` once, backgrounded. Every new rule observed RED on a real manifest before the artifact is fixed.
- **VII. De-Localized Generation** - **PASS**. This is engine machinery with no place-specific content.
- **VIII. Direct Voice** - **PASS**.
- **IX. Setting Integration** - **PASS**. The one world-claim the design makes - that grazing/pasture/scrub are permissive while paddy and hatake are not - is the GM's own, recorded in data-model.md §1.
- **X. Python Discipline (NON-NEGOTIABLE)** - **PASS**. ruff + mypy + pytest + 100% coverage; red-green on every new rule.
- **XI. Japanese Authenticity** - **N/A**. No new drawn terms.
- **XII. Historical Grounding Bookends (NON-NEGOTIABLE)** - **PASS, scoped**. This feature changes VALIDATION, not depiction - it adds nothing to any map and asserts nothing new about the world. The single land-use claim it encodes (permissive cover vs worked surface) is grounded in data-model.md §1 rather than in a separate research.md, because there is no drawn element to bookend. The closing obligation is discharged by confirming no map's DEPICTION changed except the one defect being fixed.

## Approach - converge with ONE pool-wide dry run

The skill's own lesson ("converge on a new rule with ONE pool-wide dry-run, not one variant per
turn") governs here, because the classification is empirical: I do not know which of the 101 pairs
are real until the matrix is measured on drawn extents rather than envelopes.

1. Implement classes + drawn-extent extraction + the matrix as a **read-only dry-run script** first.
2. Run it once over the whole pool. Read the report ONCE.
3. Classify from real results: real defect -> fix; legitimate -> permission with a reason.
4. Only then promote the matrix to a gate check + ratchet test.
5. Retire the per-pair checks it subsumes.

## Structure

```text
specs/017-overlap-matrix/{spec,plan,data-model,tasks}.md + checklists/requirements.md
.claude/skills/diagram/check_village.py     # OVERLAP_CLASS, the policy matrix, drawn-extent
                                            # extraction, features_do_not_overlap, the ratchet
.claude/skills/diagram/test_checks.py       # matrix unit tests + the ratchet test
.claude/skills/diagram/pool/regressions/    # the dry-plot-over-water capture, and one per new rule
.claude/skills/diagram/settlements.md       # the contract, documented where authors will read it
```

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
|---|---|---|
| A second overlap registry alongside `_OVERLAP_STRUCTS` | The existing one models **structure x hazard** and has no notion of ground-vs-ground; extending it in place would mean re-typing every entry mid-flight while the gate stays green | Retiring `_OVERLAP_STRUCTS` outright in the same pass would put the whole keep-clear contract - 15 hazards, a proven ratchet test, dozens of fixtures - in flux at once. The matrix is additive first; subsuming the older battery is FR-010 follow-up work, done only where the matrix demonstrably covers it. |
