# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]

**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]

**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]

**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]

**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]

**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]

**Project Type**: [e.g., library/cli/web-service/mobile-app/compiler/desktop-app or NEEDS CLARIFICATION]

**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]

**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]

**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Each gate must be marked PASS, N/A (with one-line justification), or DEFERRED
(with a Complexity Tracking entry). DEFERRED gates require explicit GM
approval before /speckit-tasks may run.

- **I. Accessibility-First Viewports**: Does the feature introduce or modify
  any UI? If yes, the plan MUST commit to running the screenshot-as-feedback
  workflow at GM-100 (1850×1050), GM-200 (925×525), tablet (800×1100), and
  mobile (390×844) before any UI task is reported done, and MUST commit to a
  zero-overflow DOM audit (no `text-overflow: ellipsis` truncation, no
  `overflow: hidden` clipping of meaningful content, no element with
  `scrollWidth/scrollHeight > offsetWidth/offsetHeight`).

- **II. Bold, Intentional Design**: If the feature introduces new UI surfaces,
  the plan MUST name the aesthetic direction (e.g., "editorial Japanese
  archive," "brutalist tool"), MUST name the typographic system, MUST commit
  to using the `frontend-design` plugin for greenfield UI work, and MUST NOT
  default to generic AI typography (Inter, Roboto, system sans).

- **III. Pool Data Conventions**: If the feature adds or modifies generated
  content of a recurring kind, the plan MUST specify the markdown-with-YAML
  file format, the per-category directory layout under
  `/.claude/skills/<skill>/pool/`, the frontmatter schema (including
  category slug and `clan` tag), and MUST forbid baking specific cities
  (`Kyuden X`, `Shiro X`, `Shinden X`) into frontmatter or prose.

- **IV. One Canonical Home for GM Source**: If the feature adds or moves
  SOURCE blocks, the plan MUST identify the single canonical home for each
  block and list any references-by-path that other files will use.

- **V. Protecting the GM's Writing (NON-NEGOTIABLE)**: The plan MUST NOT
  include any task that modifies content inside SOURCE markers except the
  canonical-source sync workflow described in `/workspace/CLAUDE.md`.

- **VI. Verify Before Reporting Done**: The plan MUST list the verification
  steps each task will run before being marked complete - pytest for Python
  logic, screenshot suite + DOM audit for UI, spot-check of delegated work.

- **VII. De-Localized Generation by Default**: If the feature generates pool
  content, the plan MUST default to generic / reusable framing (clan-level
  designators, family-level named entities) and MUST NOT lock content to
  specific cities or campaign-tied figures without explicit GM scoping.

- **VIII. Direct Voice Over Framing Distance**: If the feature writes in-world
  content, the plan MUST commit to direct-voice phrasing and MUST exclude
  meta-narrational framings ("the temple holds that…," "tradition says
  that…," "skeptics report…").

- **IX. Setting Integration**: The plan MUST cross-reference the relevant
  reference directories (`/setting/`, `/cosmology/`, `/campaigns/`) and
  MUST NOT invent setting details that contradict GM source notes. New
  named figures MUST NOT collide with the campaign-names cache.

- **X. Python Discipline (NON-NEGOTIABLE)**: If the feature ships Python
  code, the plan MUST commit to: `ruff check` + `ruff format --check`
  passing, `mypy --strict` passing on production modules, red-green TDD
  for new non-trivial behavior (test exists and fails before
  implementation lands), `pytest` passing with
  `--cov-fail-under=100` on pure-logic packages, external boundaries
  tested via saved fixtures (not transport-layer mocks), pinned
  dependencies via `requirements.in` → `requirements.txt` (or `uv.lock`),
  no swallowed exceptions, no `print` in production paths, behavior-named
  tests, parametrized variants, and ConfigObj / pydantic-settings for
  configuration (no hardcoded magic).

Document each gate's status in a short bulleted Constitution Check section
in the plan output before proceeding to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
