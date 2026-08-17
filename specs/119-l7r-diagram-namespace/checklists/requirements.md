# Specification Quality Checklist: One `l7r` Namespace Across the Repo

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-17
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

**On "no implementation details" for an infrastructure feature.** The spec names packages, module
paths and `__init__.py` files. For a user-facing feature that would be a leak; here those names ARE
the requirement - the "user" is a future session and the deliverable is an import surface. The line
held instead: the spec says WHAT must be importable, WHAT must stay byte-identical and WHAT must be
guarded, and leaves HOW (the transformer, the sweep script, the mypy configuration shape) to
`plan.md`. The two flagged risks - mypy's namespace resolution and the coverage `source` list - are
stated as edge cases to solve, not as chosen solutions.

**On the three-landing structure.** Landings 1 and 2 are both P1 because separately neither is the
deliverable: landing 1 alone only frees a name, landing 2 alone is impossible. They remain separate
user stories because they have different blast radii (the deployed webapp vs. the diagram engine)
and must be gated and verified independently.

**Deliberately deferred, recorded so it is not re-derived**: restructuring `webapp/l7r` to
`l7r.toolkit.*` for depth symmetry; converting either tree to an installed distribution; and any
webapp feature that actually renders a map.
