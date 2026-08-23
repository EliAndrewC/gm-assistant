# Specification Quality Checklist: Derived lanes, and settlement form as a rolled knob

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-23
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

**On "no implementation details".** The spec names `farmhouses_reach_a_way`, `LEGACY_FROZEN_GENS`
and the 48-seed cohort. These are kept deliberately: in this project the GM IS the technical
stakeholder, and the constitution requires a spec to say which existing rules a change invalidates.
Naming the rule that encodes the nucleated premise is the requirement (FR-009), not an implementation
leak - the requirement would be untestable if it said "some rules" instead. No file paths, function
signatures or algorithms appear in the requirements themselves.

**Two clarifications were resolved rather than asked**, per the project's stop-and-ask calculus:

1. *Which forms are in scope?* The existing knob offers five. Nucleated, dispersed and linear are in;
   `water_town` and `dike_top` are out, because they describe SITES this tier does not generate
   (a hamlet on a canal network, a hamlet on a polder dike crest) rather than settlement HABITS, so
   including them would mean generating new site types, which is a different feature.
2. *What happens when a rolled form does not fit its site?* Fall back to a buildable form and record
   the substitution. A hard failure would make the cohort's pass rate a function of luck, and a
   silent substitution would make the form knob untrustworthy.

**One risk is accepted and recorded in the spec** (Assumptions, last bullet): rolling the form per
seed means a seed's map can change kind, so strict per-seed regression comparison degrades. The spec
falls back to the project's documented rule for exactly this case - the pass RATE must not drop, and
every newly-failing check is diagnosed individually.
