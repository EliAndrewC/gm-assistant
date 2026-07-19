# Implementation Plan: Dreams Section (Webapp)

**Branch**: `011-dreams-section` (not yet created; GM handles git) | **Date**: 2026-07-19 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/011-dreams-section/spec.md`

## Summary

Add a public "Dreams" section to the L7R Toolkit (`webapp/l7r/`): a landing page at `/dreams` with a hand-authored, player-facing rules & framework writeup followed by a gallery of worked dream-divination example scenes, and a detail page at `/dreams/<slug>` rendering one full scene. Scenes are loaded read-only from the **public** dream pool (`.claude/skills/dream/pool/*.md`) via a loader that mirrors the relic pool loader; the gitignored spoiler tier (`pool-local/`) is never read, bundled, listed, or reachable. Markdown bodies render through the already-vendored `markdown-it-py`. The section reuses the existing design system and is verified with the standard Principle I screenshot + DOM-audit workflow.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: CherryPy (routing), Jinja2 (templates), `markdown-it-py==4.2.0` (markdown→HTML, already vendored), PyYAML (frontmatter). No new dependencies.

**Storage**: Flat markdown-with-YAML files in `.claude/skills/dream/pool/` (public tier). Read-only; no database.

**Testing**: pytest + pytest-cov; Playwright screenshot suite (`tests/screenshot.py`) + `tests/dom_audit.py` for Principle I.

**Target Platform**: Linux server (CherryPy app; Fly.io in production, `python:3.13-slim`).

**Project Type**: Web application (server-rendered pages within the existing `l7r/` package).

**Performance Goals**: Standard web page loads; pool parsed at startup like relics (small N).

**Constraints**: The public/spoiler tier boundary (FR-007) is a hard gate. No content clipping / layout-balance violations across the four standard viewports (Principle I).

**Scale/Scope**: One example scene at launch; a gallery designed to grow data-driven. Two routes, one loader module, one framework markdown file, two templates, one nav entry, one deploy-bundling line.

## Constitution Check

*GATE: evaluated before Phase 0 and re-checked after Phase 1 design. All gates PASS or N/A.*

- **I. Accessibility-First Viewports (NON-NEGOTIABLE)** - **PASS (committed).** This feature adds UI. The plan commits to running `tests/screenshot.py` (GM-100 1850×1050, GM-200 925×525, tablet 800×1100, mobile 390×844) and `tests/dom_audit.py` (zero overflow/ellipsis/clip issues and sibling-height-ratio ≤ 2.5×) on `/dreams` and `/dreams/<slug>` before any UI task is reported done, plus an independent `frontend-review` subagent pass (author ≠ reviewer). Special attention: the four fragment tables and the framework prose block are the tall/wide content most at risk - wide content scrolls inside its own container.
- **II. Bold, Intentional Design** - **PASS (reuse, not greenfield).** Aesthetic direction: the existing "editorial Japanese archive." Typographic system: the site's existing tokens - `Fraunces` (display), `EB Garamond` (body), `Shippori Mincho` (JP) - reused, not replaced. No generic AI typography introduced. Because this extends an established system rather than starting greenfield UI, the `frontend-design` plugin is not required (per the principle's greenfield trigger); the direction is "match Relics."
- **III. Pool Data Conventions** - **PASS (by reference; read-only consumer).** The dream-scene file format (markdown + YAML frontmatter, flat `pool/` directory, `sender`/`tier`/`bands` schema) is already defined by the `/dream` skill; this feature consumes it read-only and defines no new pool format. The dream pool intentionally differs from the relic pool (flat and sender-keyed rather than per-fortune with clan/kanji fields) - that difference lives in the skill, not here. No city names are baked into frontmatter or prose by this feature.
- **IV. One Canonical Home for GM Source** - **N/A.** This feature adds no SOURCE blocks. The framework markdown is dev-authored player-facing prose, not a GM SOURCE excerpt; the `/dream` SKILL remains the canonical home of the framework it adapts.
- **V. Protecting the GM's Writing (NON-NEGOTIABLE)** - **PASS.** No task modifies content inside SOURCE markers. The one existing SOURCE block in the dream skill (Okura's introduction) is untouched.
- **VI. Verify Before Reporting Done** - **PASS (committed).** Per-task verification: `ruff check` + `ruff format --check` + `mypy --strict` + `pytest --cov-fail-under=100` on the new pure-logic loader; screenshot suite + DOM audit + `frontend-review` for the UI; and a manual spot-check that a running `/dreams/<slug>` renders the Daikoku scene and that no `pool-local/` scene is reachable.
- **VII. De-Localized Generation by Default** - **N/A (rendering, not generating).** This feature does not generate pool content; it renders existing scenes. The example scene is a deliberately public, past-campaign example (GM-scoped), which is the intended use of the public tier.
- **VIII. Direct Voice Over Framing Distance** - **N/A.** No new in-world content is authored here. The framework page is expository player-facing rules prose; the scene prose already exists in the pool.
- **IX. Setting Integration** - **PASS.** The rendered example's setting facts (Daikoku's domain, the Aki lineage's war debt, Daidoji Masamune) were cross-referenced against `l7r.md` during scene authoring; named figures (Nagamasa, Governor Kureno, Aki Tomobei) are lineage-scoped inventions checked for collisions. This feature adds no new setting claims.
- **X. Python Discipline (NON-NEGOTIABLE)** - **PASS (committed).** New Python (`l7r/dreams.py` loader, the `dreams` route, markdown-render helper) commits to: ruff + ruff-format clean; `mypy --strict` on the modules; red-green TDD (loader tests written and failing before the loader lands); `pytest --cov-fail-under=100` on the pure-logic loader; malformed-file handling tested via saved fixture files (not transport mocks); no new dependency (pins unchanged); no swallowed exceptions (bad files logged, not silently dropped without a warning); no `print`; behavior-named, parametrized tests; pool directory resolved via env var (`L7R_DREAM_POOL_DIR`), no hardcoded absolute path.
- **XI. Japanese Authenticity (NON-NEGOTIABLE)** - **PASS.** Any kanji surfaced (e.g. a sender's kanji, if shown) comes from already-authored, triangle-checked content; this feature renders it and introduces no new kanji.
- **XII. Historical Grounding Bookends (NON-NEGOTIABLE)** - **N/A.** This feature does not change what any generator asserts about the world (no settlement/compound layout, no claim about how a place was farmed/built/lived). It renders pre-existing, already-grounded content. Recorded in `research.md` with the reasoning. No opening/closing grounding bookend required.

**Gate result: all gates PASS or justified N/A. No DEFERRED gates; no Complexity Tracking entries needed.**

## Project Structure

### Documentation (this feature)

```text
specs/011-dreams-section/
├── plan.md              # This file
├── research.md          # Phase 0 (done)
├── data-model.md        # Phase 1 (done)
├── quickstart.md        # Phase 1 (done)
├── contracts/
│   └── routes.md        # Phase 1 (done) - route + template contract
├── checklists/
│   └── requirements.md  # spec quality checklist (done, passing)
└── tasks.md             # Phase 2 (/speckit-tasks - NOT created here)
```

### Source Code (repository root)

```text
webapp/l7r/
├── dreams.py                    # NEW - DreamScene dataclass + load_dream_scenes(); mirrors pool.py
├── app.py                       # EDIT - _resolve_default_dream_pool_dir(), load scenes into Root,
│                                #        dreams(self, slug=None) route, wire pool dir
├── sections.py                  # EDIT - add Section(slug='dreams', label='Dreams', path='/dreams')
├── content/
│   └── dreams_framework.md      # NEW - hand-authored player-facing rules & framework prose
├── templates/
│   ├── dreams_index.html        # NEW - framework block + examples list (extends _layout.html)
│   └── dream_detail.html        # NEW - one full rendered scene (extends _layout.html)
└── static/css/l7r.css           # EDIT - scene/framework layout using existing tokens (no new fonts)

webapp/tests/
├── test_dreams.py               # NEW - loader unit tests (100% cov), incl. spoiler-tier exclusion
└── fixtures/dream_pool/         # NEW - saved good/malformed scene fixtures for the loader tests

webapp/Makefile                  # EDIT - prepare-deploy copies .claude/skills/dream/pool -> skills/dream/pool
webapp/Dockerfile                # EDIT (if needed) - ensure skills/dream ships; set L7R_DREAM_POOL_DIR
```

**Structure Decision**: Extend the existing `webapp/l7r/` server-rendered app in place, mirroring the Relics section (loader + route + two templates + nav entry + deploy-bundling line). No new project or service; no new runtime dependency.

## Complexity Tracking

No Constitution violations to justify. (Section intentionally empty.)
