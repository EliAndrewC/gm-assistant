# Specification Quality Checklist: settlement/city.py -> settlement/city/ Package Split

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-16
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

**On "no implementation details" for a refactor spec.** This feature's user is a future session
reading the code, and its deliverable IS a file layout - so submodule names, the composed-mixin
mechanism and the byte-identity oracle are the subject matter, not leaked implementation. The test
applied instead: does the spec say WHAT must be true (nothing changes about what the engine draws;
one subsystem costs one file) rather than HOW to achieve it (which transformer, which slice
boundaries, which commit order within a stage)? The HOW lives in plan.md and tasks.md. Feature 112
resolved the same tension the same way, and this checklist is marked complete on that basis.

**Clarifications resolved without asking** (GM 2026-08-15 standing instruction - answer spec-kit's
own questions, record the decision where it arose):

1. *Does `governor_mansion` move out of the package?* No - scoped out. Relocating it is a topical
   judgment that would make US1 impure, and an impure move is exactly what feature 112 research R14
   says is expensive to merge.
2. *Which methods count as "oversized" for US2?* The five over ~90 lines: `city_wall` (339),
   `channel_footbridges` (195), `farmland_ring` (121), `moat` (111), `log_boom` (97). The ~150-line
   bar in FR-009 is the ceiling that must hold afterward; the five are the ones worked.
3. *Does this feature raise the coverage ratchet?* Only if its own split re-covers city wings, and
   only to a figure it measured itself. The peer session left `SETTLEMENT_COV_FLOOR` at 94
   deliberately so the attribution stays clean; FR-012 owns it and the floor never falls.
4. *Wait for the peer reorg, or land first?* Wait. The peer confirmed it touches nothing under
   `settlement/`, so there is no file-level collision either way - but its tip moves three paths
   this feature's tooling uses (`tests/settlement/`, `python3 -m pipeline.regen`, the
   `engine_files()` prune). Building on its tip costs nothing; building under it means rewriting
   quickstart and tasks paths mid-feature.
