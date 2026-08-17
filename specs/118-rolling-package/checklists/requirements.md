# Specification Quality Checklist: rolling.py -> rolling/ Package Split + roll_village Stages

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-17
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

Note on the first two, since this is an internal-architecture feature: the "user" is a future
session of this project and the "business need" is context-window token cost, which is the cost
constitution Principle X clause 13 names by name. The spec therefore does name files and functions -
they are the SUBJECT, not the implementation. It deliberately does not prescribe the partition (that
is `data-model.md`'s job) or the transformer's mechanics (`plan.md`'s).

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous - every FR is checkable by a command (line counts,
      `git diff --stat`, a comment-line census, the byte-identity sweep, `make done`)
- [x] Success criteria are measurable - all six are counts or byte comparisons, not judgments
- [x] Success criteria are technology-agnostic - they state read cost, artifact identity and
      regression count, not how the split is performed
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified - six, including the two the sibling splits learned the hard way
      (decorator-dropping spans, a constant separated from its consumers) and one specific to this
      week (feature 117 cutting `_geom.py` concurrently)
- [x] Scope is clearly bounded - `land.py` is named as out-of-scope debt so the backlog stays
      visible; the tests are explicitly not re-partitioned, with the reason
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows - and are ordered so P1 alone is shippable (the split
      without the decomposition is a complete feature)
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- The clause-12 half is honest about its own footing: by the constitution's stated MEASURE (logic
  units) `roll_village` at 117 statements is not a defect, and the spec says so. It proceeds on the
  project's converged ~150-line practice and on the GM's explicit request naming function size.
  This distinction is recorded rather than smoothed over, because a future session reading only the
  constitution would otherwise find this feature unmotivated.
- Two pre-flight measurements `future-work.md` demanded were taken BEFORE the spec was written, and
  their results are in it. One of them contradicted the prediction on file, which is exactly why
  the rule to measure first exists.
