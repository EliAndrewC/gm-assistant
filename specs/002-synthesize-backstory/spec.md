# Feature Specification: Synthesize Backstory

**Feature Branch**: `002-synthesize-backstory`

**Created**: 2026-06-30

**Status**: Draft

**Input**: User description: Ship the "Synthesize Backstory" feature in the chargen webapp, using the full-corpus prompt that won a blind bakeoff. The production prompt is the full canonical corpus (design brief + clan framing + per-clan flavor + the entire l7r.md + budgets.md), sent to gemini-3.1-pro-preview. Productionize the prompt (it currently depends on the dev mount and the temporary bakeoff directory), wire an AJAX route and a button into chargen with re-rolling and GM steering notes, add tests at 100% coverage, then delete the bakeoff harness.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Synthesize a backstory from a generated character (Priority: P1)

After chargen produces a character (clan, family, rank, recognition, honor, traits, advantages/disadvantages), the GM clicks a "Synthesize Backstory" button on the character page and, after a short wait, receives a 1-3 paragraph prose backstory that reconciles the character's mechanical traits into a single believable person, grounded in the campaign setting. It is the text twin of the existing AI-portrait button.

**Why this priority**: This is the feature. A single click that turns a trait sheet into usable prose is the entire value; everything else refines it.

**Independent Test**: Generate any character, click the button, and confirm a coherent 1-3 paragraph backstory appears that is consistent with the character's clan, rank, honor, and traits and contains no setting contradictions. Delivers value on its own even without re-rolling or steering.

**Acceptance Scenarios**:

1. **Given** a generated character is displayed, **When** the GM clicks "Synthesize Backstory", **Then** a 1-3 paragraph prose backstory appears on the page, attributable to that character's traits.
2. **Given** a character whose traits are in tension (e.g. a low-honor minor-clan escort, or a high-honor character with troubling convictions), **When** a backstory is synthesized, **Then** the prose reconciles the tension into one coherent person rather than restating the traits as a list, and treats honor as strength-of-conviction (low honor is not portrayed as cartoon villainy).
3. **Given** the synthesis is in progress, **When** the GM is waiting, **Then** the page shows a clear in-progress state and does not appear frozen or allow a duplicate concurrent request for the same character.

---

### User Story 2 - Re-roll and steer the synthesis (Priority: P2)

If the GM does not like a result, they can re-roll to get a fresh backstory, and they can type freeform steering notes (e.g. "make her a reluctant duelist who lost a sibling") that are given high priority in the next synthesis.

**Why this priority**: Backstory generation is inherently a "try again / nudge" workflow; the GM rarely accepts the first draft verbatim. This mirrors the re-roll/edit affordance of the portrait button.

**Independent Test**: Synthesize a backstory, enter a steering note, re-roll, and confirm the new backstory differs and visibly reflects the steering note without contradicting the character's fixed traits or the setting.

**Acceptance Scenarios**:

1. **Given** a synthesized backstory is shown, **When** the GM re-rolls, **Then** a new backstory is produced for the same character.
2. **Given** the GM has entered steering notes, **When** they synthesize, **Then** the result reflects the steering where it applies, overriding default tendencies but never contradicting the character's generated details or the setting.

---

### User Story 3 - The same backstory quality in the deployed app (Priority: P1)

The backstory the GM gets from the deployed (hosted) app is grounded in the full canonical setting, exactly as in the local dev environment - even though the hosted app has no access to the GM's bind-mounted notes.

**Why this priority**: The winning prompt is the full corpus, which currently lives only on the dev bind-mount and in a temporary local directory. Without this, the button would either fail or silently degrade to a thin prompt in production - the exact failure mode the bakeoff rejected. It is P1 because the feature is not shippable without it.

**Independent Test**: Build the deployment artifact with no bind-mount present, start the app from that artifact alone, synthesize a backstory, and confirm it is grounded in the full setting (e.g. it can anchor events to real, established campaign history and named calendar dates) rather than a generic placeholder.

**Acceptance Scenarios**:

1. **Given** a deployment artifact built without the dev mount, **When** the app synthesizes a backstory, **Then** the prompt contains the full canonical corpus from the bundled snapshot, not a degraded subset.
2. **Given** the GM re-deploys after editing their canonical notes, **When** they next synthesize, **Then** the backstory reflects the updated notes (the bundled corpus is a per-deploy snapshot).

### Edge Cases

- **Model/API failure or timeout**: the GM sees a clear, non-fatal error message and can retry; the page does not crash or lose the displayed character.
- **Missing API credentials**: a clear message explains that the text-model credential is not configured, mirroring the portrait button's behavior.
- **Missing bundled corpus** (artifact built without the snapshot step): synthesis fails loudly with an explanatory error rather than silently sending a thin prompt.
- **Typographic dashes**: synthesized prose may contain em/en dashes from the model; the project's hyphens-only policy applies to project source and templates, and the feature must not introduce typographic dashes into committed files (model output rendered at runtime is not a committed file, but any persisted/exported text should be normalized to hyphens).
- **Unusual characters**: edge-caste (heimen/hinin), monk, or genuine-shugenja characters still produce coherent, setting-appropriate backstories.
- **Very long or empty model output**: empty output is treated as a failure with a retry; over-long output is displayed without breaking the page layout.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The character page MUST present a "Synthesize Backstory" control that generates a 1-3 paragraph prose backstory for the currently displayed character.
- **FR-002**: The synthesis MUST use the full-corpus prompt chosen by the bakeoff: the design brief, the "The Great Clans" framing, the per-clan flavor summary, and the entire canonical notes (l7r.md) plus the economic model (budgets.md), wrapped by the task instructions and the character sheet.
- **FR-003**: The synthesis MUST use the Pro text model (gemini-3.1-pro-preview) as the configured default, and the model MUST remain configurable without code changes.
- **FR-004**: The feature MUST preserve the existing design-brief content unchanged in behavior - specifically the conviction-not-virtue honor model, the good-vs-good conflict guidance, and the calendar date-anchoring instruction.
- **FR-005**: The GM MUST be able to re-roll a synthesis to obtain a fresh result for the same character.
- **FR-006**: The GM MUST be able to provide freeform steering notes that influence the synthesis with high priority, without overriding the character's fixed traits or the setting.
- **FR-007**: The full canonical corpus (l7r.md + budgets.md) MUST be available to the deployed app without relying on the dev bind-mount, via a snapshot bundled into the deployment artifact by the existing deploy-preparation step.
- **FR-008**: The per-clan flavor summary MUST live in the production package (not in the temporary evaluation directory), so the prompt assembles correctly after the evaluation harness is removed.
- **FR-009**: The production prompt assembly MUST produce output equivalent to the evaluation harness's winning ("full") assembly for the same inputs, verified before the evaluation harness is deleted.
- **FR-010**: The system MUST surface model/credential/missing-corpus failures as clear, recoverable errors and MUST NOT silently fall back to a thinner prompt.
- **FR-011**: New production logic MUST be covered by automated tests at 100% line coverage, with the external model call exercised via saved fixtures rather than transport-layer mocks.
- **FR-012**: After the button works and is covered by tests, the temporary evaluation harness (the bakeoff directory) MUST be removed, along with its lint/type/coverage grace-list entries, leaving no dead references.
- **FR-013**: The feature MUST NOT introduce em-dashes or en-dashes into any committed project file.

### Key Entities *(include if feature involves data)*

- **Character**: the generated NPC (clan, family, lineage, school, rank, recognition, experience, honor, traits, and rendered public/private descriptions) that is the input to synthesis.
- **Setting brief (full corpus)**: the assembled prompt context - design brief + clan framing + per-clan flavor + the bundled canonical notes + economic model - that grounds the synthesis.
- **Synthesized backstory**: the 1-3 paragraph prose result, optionally shaped by GM steering notes, displayed to the GM and re-rollable.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: From a displayed character, the GM can obtain a synthesized backstory in a single click (plus the model's response time), with no manual prompt assembly.
- **SC-002**: Synthesized backstories are consistently 1-3 paragraphs and reconcile the character's traits into one coherent person rather than listing them.
- **SC-003**: For characters that stress setting mechanics (rank vs recognition, edge castes, the Doctrine of Three Steps, ministry authority), backstories are free of the basic setting errors that the thin-prompt arms produced in evaluation.
- **SC-004**: Backstories anchor past events to specific, established points in the setting (named calendar dates and real campaign history) rather than generic phrases like "a few years ago", whenever it fits.
- **SC-005**: The deployed app, built with no bind-mount, produces backstories of the same fidelity as the dev environment.
- **SC-006**: The GM can re-roll and steer results; a steering note is reflected in the next result.
- **SC-007**: The project's quality gate passes after the change (lint, format, types, tests, and 100% coverage on production logic), and the repository contains no remaining evaluation-harness code or references.

## Assumptions

- The GM (a single trusted operator) is the only user; there is no multi-user, auth, or rate-limiting concern for this feature.
- A Gemini text-model credential is configured in the environment (the same mechanism the portrait button uses).
- Sending the entire canonical corpus to the external model is acceptable to the GM; token cost is explicitly not a concern for this occasional, per-character use.
- The bundled corpus is a point-in-time snapshot refreshed on each deploy; staleness between deploys is acceptable and expected.
- The deploy-preparation step runs in an environment where the canonical notes are available (the dev container with the mount), so it can snapshot them into the artifact.
- The existing AI-portrait button establishes the interaction pattern (async generate, in-progress state, re-roll) to mirror.
- The honor model and calendar date-anchoring instruction already present in the design brief and instructions are correct and in scope to preserve, not to redesign.
