# Specification Quality Checklist: The capital map skeleton and the castle

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

1. *Implementation names leaking into requirements.* The draft named `s.castle(...)`, `meta(scale="capital")`, `settlement.py`, `check_village`, `render_png` and `settlement-review` directly in the FRs. Rewritten to state the capability - "the system MUST draw a castle as an enclosure of walls, moats and gates" - and leave the names to the plan. They survive only in the Context and Scope sections, where they locate decisions rather than specify a build.
2. *An untestable success criterion.* "The castle looks impressive" replaced with SC-003 and SC-006, which are checkable by looking at the render and reading the tier doc.
3. *A missing edge case that would otherwise bite in the next feature.* Added the castle-as-keep-out case (FR-006): the enclosure is roughly 85% of a provincial city's ground, so if the skeleton does not RESERVE it, feature 020's packers discover it the hard way. The skill's dev-loop doc is explicit that a feature which must reserve ground has to run before placement and register in a registry the placer honors, so this belongs in the skeleton rather than the fabric.

**A fourth item was considered and deliberately left as-is.** FR-012 ("checks that assume a populated interior must not fire on a skeleton, and must not be weakened") reads like two requirements. It is one, and splitting it would lose the point: the easy way to satisfy the first half is to violate the second. The skill has a recorded history of rules going quiet rather than failing - "a check that never RUNS looks exactly like a check that passes" - so the constraint is stated as a single requirement with its trap attached.

**No [NEEDS CLARIFICATION] markers were needed.** Every decision was settled with the GM on 2026-08-08 before the spec was written, and the Assumptions section names each one and its source.

**One scope judgment is recorded rather than asked about**: the drawn capital is split across two features, with the castle deliberately built FIRST so the GM's explicitly-provisional bailey-wall decision is judged off an early render instead of at the end of a long build. The deferred items are listed by name in the Scope boundary.

**One outcome is defined as success in both directions**: the bailey walls may be removed. The spec says so explicitly in the Assumptions, so a "remove them" verdict cannot later read as the feature having failed.
