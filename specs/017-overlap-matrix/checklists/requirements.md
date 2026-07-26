# Specification Quality Checklist: The Overlap Matrix

**Created**: 2026-07-26 | **Feature**: [spec.md](../spec.md)

## Content Quality
- [x] No implementation details beyond the project's own settled vocabulary
- [x] Focused on user value (ends the whack-a-mole; one line to protect a new feature)
- [x] All mandatory sections completed

## Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers - both open decisions were put to the GM and answered (classify all 101 up front; use spec-kit)
- [x] Requirements testable and unambiguous
- [x] Success criteria measurable (101 pairs resolved, zero false positives, coverage held)
- [x] Edge cases identified - the envelope-vs-drawn-extent trap is called out as the central risk
- [x] Scope bounded - the matrix is additive; retiring `_OVERLAP_STRUCTS` is explicitly NOT in scope
- [x] Dependencies and assumptions identified

## Feature Readiness
- [x] Every FR has acceptance criteria
- [x] User scenarios cover the primary flows
- [x] No implementation detail leaks into the success criteria

## Notes
- The **measured** basis is unusual and worth noting: the spec is grounded in a pool-wide survey (101 co-occurring pairs) rather than on intuition, and it states up front that roughly half of those are artifacts of measuring envelopes. That honesty is load-bearing - a matrix built to eliminate the artifacts would be wrong.
- SC-005 ("zero false positives") is the criterion most likely to be gamed by silencing a failure. FR-002 defends it: every permission must carry a reason, so a silenced pair is visible as a permission with a weak reason rather than as an absence.
