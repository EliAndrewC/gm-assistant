# Specification Quality Checklist: Domain-capital space budget and tier declaration

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-08
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

**Validation run 1 - three issues found and fixed:**

1. *Implementation detail leaking into requirements.* Early drafts named `citybudget.py`, `plan_city`,
   `C_YASHIKI`/`C_TERRACE` and `capital_wall_matches_budget` directly in the FRs. Rewritten to state
   the capability ("price a walled in-wall samurai compound and a retainer terrace as ground-cost
   constants distinct from the existing ones") and leave the names to the plan. The module names
   survive only in the Scope boundary and Context sections, where they are locating the *decisions*
   rather than specifying the build.
2. *Untestable success criterion.* "The budget is trustworthy" replaced with SC-004, which is
   checkable by reading the report.
3. *A missing edge case with real history behind it.* Added the no-budget-declared case (FR-015,
   SC-007). The diagram skill's own dev-loop notes record three separate occasions where a rule gated
   on an optional declaration silently never ran while the gate stayed green - "a check that never
   RUNS looks exactly like a check that passes" - so a capital that simply omits its budget must fail
   rather than skip.

**No [NEEDS CLARIFICATION] markers were needed.** Every decision this feature encodes was settled with
the GM on 2026-08-08 and recorded in `settlements/capitals.md` and `research/cities/capitals.md`
before the spec was written; the Assumptions section names each one and its source rather than
re-opening it.

**One scope judgment is recorded in the spec rather than asked about**: the capital tier is too large
for a single feature, so this one is the budget only, mirroring feature 009's role for provincial
cities and following the project's own budget-first ordering. The deferred items are listed
explicitly in the Scope boundary section so the line is visible rather than implied.
