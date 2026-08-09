# Specification Quality Checklist: The capital's ground-reserving layer

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-09
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

1. *Implementation names in the requirements.* The draft named `_OVERLAP_STRUCTS`, `OVERLAP_CLASS`, `_LABEL_GROUP`, `bridges()` and `roads_bridge_water` directly. FR-012 and FR-013 now state the capability - "classified for overlap, given a caption group, and classified as roofed or open-air ground", and "the check MUST read the same complete sets" - and leave the registry names to the plan. They survive only in the Context and Scope sections, which locate decisions rather than specify a build.

2. *A success criterion that could not be checked by looking.* "The lineage compounds are correctly sized" became SC-002: a reader can name all eight lineages and rank them into four bands **without measuring**. That is the property that actually matters - the sizes must be visibly distinct, not merely numerically correct.

3. *An edge case that is this feature's most likely silent failure.* Added the wrong-record-SHAPE case, because feature 019 hit exactly it: a bare dict instead of a list made the largest structure on the map invisible to three independent guardrails at once, and none of them said anything. This layer adds roughly a dozen new feature keys, so the same mistake is available a dozen times over. FR-012 now requires the list shape as part of the classification requirement rather than as a separate note.

**No [NEEDS CLARIFICATION] markers were needed.** Every decision was settled with the GM across 2026-08-08/09 and recorded before the spec was written; the Assumptions section names each and its source.

**Two judgments are recorded rather than asked about:**

- **The scope split is forced by DRAW ORDER**, not chosen. Anything that reserves ground must precede the packs, so the reserving layer and the housing cannot be interleaved. The spec says so in the Scope boundary rather than presenting the split as a preference.
- **Ending not-green is the expected outcome** and is written into the Assumptions, so it cannot later read as the feature having failed. The population check cannot pass until housing lands, and a non-green map cannot enter the swept pool without breaking every other session's gate.
