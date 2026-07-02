# Implementation Plan: Synthesize Backstory

**Branch**: `main` (no feature branch created - GM handles git) | **Date**: 2026-06-30 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-synthesize-backstory/spec.md`

## Summary

Ship the "Synthesize Backstory" button in the chargen webapp using the full-corpus prompt that won the blind bakeoff (design brief + "The Great Clans" framing + per-clan flavor + the entire l7r.md + budgets.md), via gemini-3.1-pro-preview. The work is two layers: (A) **productionize the prompt** - lift the corpus and `flavor_clans.md` out of the dev bind-mount and the temporary `bakeoff/` directory so the deployed app can assemble the full brief from a bundled snapshot; (B) **wire the feature** - an `@ajax synthesize` route + button mirroring the existing `generate_art` portrait pattern, with re-roll and GM steering notes. New pure-logic (brief assembly + corpus loading) lands in a Principle-X-compliant module under the coverage gate; the Gemini call stays a fixture-tested boundary. Finish by deleting `bakeoff/` and its grace-list entries. Implementation order is **refactor-first (A) then button (B)**.

## Technical Context

**Language/Version**: Python 3.13 (chargen webapp; pyproject pins py313)

**Primary Dependencies**: CherryPy + Jinja2 (web), `google-genai==2.7.0` (already pinned; no new deps), ConfigObj (chargen config). Playwright for UI verification.

**Storage**: Files only. New: a bundled read-only snapshot of `l7r.md` + `budgets.md` produced at deploy-prep time; relocated `flavor_clans.md` in the chargen package. No database.

**Testing**: pytest + pytest-cov; Playwright screenshot suite + DOM audit for the UI. Gemini boundary tested via saved fixtures.

**Target Platform**: Linux container (dev sandbox) and Fly.io (`python:3.13-slim`). The deployed app has **no bind-mount** - the defining constraint.

**Project Type**: Web application (CherryPy backend + Jinja templates), chargen sub-app mounted under the l7r toolkit.

**Performance Goals**: Not latency-sensitive; a synthesis is one occasional model call per character. The full-corpus prompt is ~345k input tokens by design; token cost is explicitly out of scope as a concern.

**Constraints**: Hyphens only (no em/en dashes) in committed files; preserve the honor model + calendar date-anchoring instruction already in the brief/instructions; never modify GM SOURCE content; must work both in dev (mount or bundle) and prod (bundle only).

**Scale/Scope**: Single trusted user (the GM). ~3 production files touched (synthesis assembly, route, template) + Makefile + pyproject + tests; one directory deleted (`bakeoff/`).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design (unchanged - still PASS).*

- **I. Accessibility-First Viewports (NON-NEGOTIABLE)** - **PASS (committed)**. The feature adds UI (a button, an in-progress state, a result panel, and a steering-notes textarea on the chargen character page). The plan commits to running the screenshot suite at GM-100 / GM-200 / tablet / mobile as multi-scroll contact sheets, a zero-issue DOM audit (clipping + layout-balance), and an independent `frontend-review` pass (author == reviewer) before the UI task is reported done. Verification targets the chargen character page; if the screenshot tooling needs a `/chargen` target URL, adding it is part of the UI task.
- **II. Bold, Intentional Design** - **N/A**. No greenfield UI surface. The control reuses the existing chargen character-page styling and the established `generate_art` button/result pattern; no new typeface, palette, or aesthetic system is introduced. (If the result panel needs styling, it matches the existing portrait panel.)
- **III. Pool Data Conventions** - **N/A**. No recurring generated pool content is added. The bundled corpus is setting *source*, not pool data; runtime backstories are per-character session output, never written to a pool.
- **IV. One Canonical Home for GM Source** - **PASS**. No SOURCE blocks are added or relocated. The canonical home of the GM's notes stays `l7r.md` in the GM's repo; the bundled corpus is a derived, read-only deploy snapshot (same pattern as the existing pool-data bundle), not a second canonical home. `flavor_clans.md` is AI-generated content with no SOURCE markers, free to relocate.
- **V. Protecting the GM's Writing (NON-NEGOTIABLE)** - **PASS**. No task modifies content inside SOURCE markers. The corpus snapshot is a verbatim, read-only file copy; the build never edits l7r.md.
- **VI. Verify Before Reporting Done** - **PASS (committed)**. Per-task verification: the five-point Python gate (ruff check, ruff format --check, mypy --strict, pytest, `--cov-fail-under=100`) on new modules; a programmatic **equivalence check** that the production assembly equals the bakeoff's `briefs.build_tier('full')` for the same inputs *before* `bakeoff/` is deleted; the screenshot suite + DOM audit + frontend-review for the UI; and a live-Gemini smoke of the button.
- **VII. De-Localized Generation by Default** - **N/A**. No pool content is generated; per-character runtime output is inherently session-scoped and is never pooled.
- **VIII. Direct Voice Over Framing Distance** - **N/A**. No new committed in-world content; runtime voice is governed by the existing brief/instructions, which already encode the GM's voice rules.
- **IX. Setting Integration** - **PASS**. The feature consumes the canonical setting notes directly and adds no new named figures to any committed file, so it cannot collide with the campaign-names cache or contradict canon.
- **X. Python Discipline (NON-NEGOTIABLE)** - **PASS (committed)**. New pure-logic (corpus loading + full-brief assembly) lands in a **new, fully-compliant module** added to the coverage source and to `mypy --strict` (not the chargen grace list): ruff-clean, strictly typed, red-green TDD, 100% line coverage. The Gemini call remains the external boundary in the grace-listed `synthesis.py`, tested via **saved fixtures** (a recorded real response), not transport mocks. No new dependencies (`google-genai` already pinned). No swallowed exceptions; `logging` not `print`; behavior-named, parametrized tests; the model id stays config-driven (`[gemini] text_model`). See research.md for the coverage-architecture decision.
- **XI. Japanese Authenticity (NON-NEGOTIABLE)** - **N/A**. The feature adds no new committed Japanese-script content. Any kanji in a runtime backstory is model output governed by the existing brief's Principle XI guidance, not a committed pool entry.

No gates are DEFERRED; Complexity Tracking is empty; no GM approval is blocked.

## Project Structure

### Documentation (this feature)

```text
specs/002-synthesize-backstory/
├── plan.md              # This file
├── research.md          # Phase 0 - key decisions (coverage home, bundling, fixtures, equivalence)
├── data-model.md        # Phase 1 - entities (Character, BriefSources, SynthesisResult)
├── quickstart.md        # Phase 1 - how to build, verify, and smoke the feature
├── contracts/
│   └── synthesize.md    # Phase 1 - the @ajax synthesize endpoint contract
└── checklists/
    └── requirements.md  # spec quality checklist (from /speckit-specify)
```

### Source Code (repository root)

```text
webapp/
├── chargen/
│   ├── synthesis.py            # MODIFY: load_brief/build_prompt delegate to the new brief module;
│   │                           #         synthesize() stays the fixture-tested Gemini boundary
│   ├── brief.py                # NEW (compliant): corpus loading + full-brief assembly (pure logic)
│   ├── test_brief.py           # NEW: red-green tests, 100% coverage
│   ├── test_synthesis.py       # NEW/EXTEND: build_prompt + synthesize() against saved fixtures
│   ├── fixtures/               # NEW: saved Gemini response(s) for boundary tests
│   ├── flavor_clans.md         # MOVED here from webapp/bakeoff/
│   ├── synthesis_brief.md      # unchanged (already carries honor model + calendar instruction)
│   ├── website.py              # MODIFY: add @ajax synthesize route (thin glue, mirrors generate_art)
│   └── templates/index.html    # MODIFY: add the Synthesize Backstory button, result panel, steering box
├── setting/                    # NEW (bundled, gitignored): snapshot of l7r.md + budgets.md at deploy prep
├── Makefile                    # MODIFY: prepare-deploy also snapshots the setting corpus
├── pyproject.toml              # MODIFY: add chargen/brief.py to coverage source + mypy strict; later drop bakeoff entries
└── bakeoff/                    # DELETE at the end (after equivalence check + button shipped)
```

**Structure Decision**: Web application, chargen sub-app. New compliant logic is isolated in `chargen/brief.py` so it can sit under the Principle X gate while the surrounding legacy chargen modules keep their grace period. The CherryPy route and template edits are thin transport/markup that mirror the existing portrait pattern; their testable behavior is pushed down into `brief.py` and the fixture-tested `synthesize()`.

## Complexity Tracking

*No constitutional gates are DEFERRED or violated; this section is intentionally empty.*
