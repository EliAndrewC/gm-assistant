# Specification Quality Checklist: settlement/_geom.py -> settlement/_geom/ Package Split

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-17
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
      - the "stakeholder" for an engine refactor IS a session working in this repo, so file and
        module names are the subject matter rather than leaked implementation. Judged the same way
        features 112-116 judged their identical checklists.
- [x] Focused on user value and business needs - the value is context-window tokens per read
      (clause 13's stated cost), quantified in SC-002.
- [x] Written for non-technical stakeholders - to the extent the subject allows; the "Why this file,
      and why now" section leads with the cost, not the mechanism.
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous - every FR is checkable by a command (hash diff,
      grep census, `make done`, the guard test, the audit run).
- [x] Success criteria are measurable - line counts, hash equality, exit codes, consumer-diff count.
- [x] Success criteria are technology-agnostic - as far as the domain permits; they measure
      artifacts and reductions, not internals.
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified - eleven, including the two this file has and its predecessors did
      not: the unnamed module-level guard call, and star-import shadowing.
- [x] Scope is clearly bounded - `rolling.py` and `land.py` are explicitly excluded and recorded as
      standing debt; no function decomposition; `settlement/__init__.py`'s roster untouched.
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows - the split (P1), the proof it is complete (P2), the index
      (P3); each independently shippable.
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification beyond the subject matter itself

## Notes

- Validated in one pass; no spec updates were required by this checklist.
- One correction was made before the claim push: the consumer count was written from memory as "34
  of the 40 files" and measured at **41 of 47**. Recorded here because the shape recurs - a number
  in a spec that nobody measured is the same defect class as a stale timing in a doc.
