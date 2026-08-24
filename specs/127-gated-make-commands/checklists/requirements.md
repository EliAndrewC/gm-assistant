# Specification Quality Checklist: Every Expensive Path Runs Through a Gated Make Target

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-24
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

**On "no implementation details".** This spec names `/proc`, make, and the process tree. That is a
deliberate departure from the template's usual bar, and the same one features 109, 111 and 126 took:
the SUBJECT of this feature is a mechanism, so a requirement that avoided naming the mechanism would
be untestable. The line held is that requirements state WHAT must be true (FR-003: the determination
must not depend on a caller-settable value) rather than HOW to compute it - which layer, which file,
which function are all deferred to plan.md.

**One judgment call is deliberately unresolved here** and is flagged inline for the fidelity reviewer:
whether read-only diagnostics are inside or outside "essentially everything about our settlement
generation, our automated checks, our performance measurements". See Scope Boundaries. It is recorded
as a boundary rather than silently applied, per Principle XVI - and the spec states the resolution if
the reviewer disagrees (gate them too).

**Not validated by this checklist**: whether the spec matches what the GM asked for. That is
`spec-fidelity`'s job and it is a separate gate, because the author of a spec cannot check it (the
whole basis of Principle XVI). This checklist only asks whether the spec is well-formed.
