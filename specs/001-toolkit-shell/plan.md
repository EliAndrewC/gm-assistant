# Implementation Plan: L7R Toolkit Phase 1 - App Shell + Chargen + Relics

**Branch**: `001-toolkit-shell` | **Date**: 2026-05-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-toolkit-shell/spec.md`

## Summary

Modernize the existing chargen CherryPy webapp in place into a multi-section L7R Toolkit with a shared app shell, a relics catalog, and a placeholder for the upcoming Names section. The chargen logic is preserved exactly; only its visual identity joins the new shell. The relics catalog is ported from the static prototype at `/gm-assistant/webapp-prototype/relics/` into server-rendered Jinja2 templates that read from the pool at `/gm-assistant/.claude/skills/relic/pool/`. New Python code lives in an `l7r/` package separate from the legacy `chargen/` package; new code meets Principle X, legacy code retains its grace period.

## Technical Context

**Language/Version**: Python 3.10 (target; works on 3.13 dev sandbox)

**Primary Dependencies**: CherryPy 18.x, Jinja2 3.x, ConfigObj (legacy chargen); Pillow, opencv-python-headless, google-genai (chargen art); requests, requests-oauthlib (chargen OP upload). New code adds: pyyaml (for parsing frontmatter; lighter than full markdown).

**Storage**: Filesystem - pool markdown files at `/gm-assistant/.claude/skills/relic/pool/<fortune>/*.md`; no database. Chargen's existing Obsidian Portal upload is the only persistent storage and is preserved.

**Testing**: pytest + pytest-cov for Python; Playwright (Python async API) with bundled Chromium for UI verification at four standard viewports.

**Target Platform**: Localhost development on Linux/macOS; eventual Fly.io deployment after Phase 1.5 (out of scope for Phase 1).

**Project Type**: Single CherryPy web service at `/gm-assistant/webapp/`.

**Performance Goals**: Localhost-only, single user. No hard SLA. Page load comfortable on a modern laptop browser at 200% zoom.

**Constraints**: No authentication in Phase 1 (localhost-only). No public deployment. New Python code on full Principle X discipline; legacy chargen on grace period.

**Scale/Scope**: 42 relics, 1 user (GM). Three live sections (Landing, Relics, Chargen) + one placeholder (Names).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Each gate marked PASS, N/A (with one-line justification), or DEFERRED (with Complexity Tracking entry).

- **I. Accessibility-First Viewports**: **PASS**. Plan commits to the screenshot/overflow workflow at GM-100 (1850×1050), GM-200 (925×525), tablet (800×1100), mobile (390×844). The existing screenshot.py and DOM-overflow check from the relics prototype port to the live app. No `text-overflow: ellipsis` on substantive content; no `overflow: hidden` clipping; no scrollWidth/scrollHeight > offsetWidth/offsetHeight.

- **II. Bold, Intentional Design**: **PASS**. Aesthetic = editorial Japanese magazine, lifted from the prototype. Typography = Fraunces + EB Garamond + Shippori Mincho. Palette = warm washi + sumi ink + vermillion. No generic AI defaults. Design system in `static/css/l7r.css`.

- **III. Pool Data Conventions**: **N/A for writes**. Phase 1 reads the existing pool only.

- **IV. One Canonical Home for GM Source**: **PASS**. No new SOURCE blocks added. Pool files remain the canonical home; the toolkit reads them.

- **V. Protecting the GM's Writing (NON-NEGOTIABLE)**: **PASS**. Read-only over the pool. No task modifies SOURCE-marker content.

- **VI. Verify Before Reporting Done**: **PASS**. Each implementation task ends with `make done` (lint + format + types + tests + 100% cov on `l7r/`) AND the Playwright screenshot/overflow audit at all four viewports. Delegated subagent work is spot-checked before being relayed.

- **VII. De-Localized Generation by Default**: **PASS**. No generation in Phase 1; the pool was de-localized in prior work.

- **VIII. Direct Voice Over Framing Distance**: **PASS**. Relic prose rendered verbatim from pool files. Toolkit's own copy avoids meta-narrational framings.

- **IX. Setting Integration**: **PASS**. Toolkit cross-references the relic pool. No new setting details invented.

- **X. Python Discipline (NON-NEGOTIABLE)**: **PASS** for the new `l7r/` package:
  - `ruff check` + `ruff format --check` clean
  - `mypy --strict` clean
  - Red-green TDD for non-trivial behavior (pool loader, slug resolution, template filters)
  - `pytest --cov-fail-under=100` on `l7r/`
  - Filesystem boundary tested via real fixture pool files in `tests/fixtures/`, not via `open()` mocks
  - Pinned deps via `requirements.in` → `requirements.txt`
  - No swallowed exceptions; logging not print; no hardcoded magic strings
  - Behavior-named tests; parametrized variants where natural

  Legacy chargen modules retain their grace period (Phase 1 does not add tests or strict types to them).

## Project Structure

### Documentation (this feature)

```text
specs/001-toolkit-shell/
├── plan.md              # This file (/speckit-plan output)
├── spec.md              # Feature spec
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root: `/gm-assistant/webapp/`)

```text
/gm-assistant/webapp/
├── pyproject.toml              # Ruff + mypy + pytest config (Phase 0 - exists)
├── Makefile                    # done / lint / format / types / test / cov / serve (Phase 0 - exists)
├── requirements.in             # Source-of-truth deps (Phase 0 - exists)
├── requirements.txt            # Compiled deps
├── development-defaults.ini    # Existing chargen config
├── development-secrets.ini     # Gitignored secrets
├── chargen/                    # Legacy chargen package - grace period
│   ├── __init__.py
│   ├── website.py              # Updated: routes stay at root; class wired into l7r app
│   ├── templates/
│   │   └── index.html          # Updated to extend l7r/templates/_layout.html (or its own variant)
│   └── ...                     # Other chargen modules unchanged
├── l7r/                        # NEW package - full Principle X discipline
│   ├── __init__.py
│   ├── app.py                  # CherryPy Root for landing/relics/names + mounts chargen
│   ├── pool.py                 # Relic dataclass + load_relics() reader
│   ├── sections.py             # Nav section registry (single source of truth)
│   ├── slugs.py                # Slug parsing / lookup helpers
│   ├── jinja_env.py            # Jinja2 environment with shared loader + filters
│   ├── templates/
│   │   ├── _layout.html
│   │   ├── landing.html
│   │   ├── relics_index.html
│   │   ├── relic_detail.html
│   │   ├── names_placeholder.html
│   │   └── _404.html
│   └── static/
│       ├── css/l7r.css         # Design system (lifted + adapted from prototype)
│       └── js/l7r.js           # Seal-filter behavior (vanilla)
├── tests/
│   ├── conftest.py
│   ├── fixtures/pool_sample/   # Fixture pool for tests (3-5 relics across fortunes)
│   ├── test_pool.py
│   ├── test_slugs.py
│   ├── test_sections.py
│   └── test_app.py
└── orgchart.py                 # Legacy chargen utility - grace period
```

**Structure Decision**: Single-project layout. New `l7r/` package alongside legacy `chargen/` package. Both packages imported into the same CherryPy process. The `l7r.app:Root` is the top-level mount; chargen routes stay at their existing paths via CherryPy's tree mounting.

## Architecture Decisions

1. **Two packages, one process.** `l7r/` and `chargen/` coexist. They share a Jinja2 environment so chargen's template can extend the shared `_layout.html`.

2. **Pool data loaded once at startup, cached in memory.** `load_relics()` parses all `pool/<fortune>/*.md` files into a `list[Relic]`. The CherryPy `Root` is constructed with the pool injected. Pool changes require a server restart - acceptable for localhost.

3. **Routing.**
   - `/` → `landing.html`
   - `/relics` → `relics_index.html`
   - `/relics/<slug>` → `relic_detail.html` (or 404)
   - `/names` → `names_placeholder.html`
   - Chargen's existing routes (`/`, `/generate`, `/upload`, etc.) - **decision change**: chargen's `Root.index` is no longer at root; root is now the L7R landing page. Chargen moves to `/chargen`. Chargen template's AJAX URLs (which currently call `/generate`, `/upload`) MUST be updated to call `/chargen/generate`, `/chargen/upload`. This is one small JS change.

4. **Static assets**: CherryPy `tools.staticdir` for `/static` pointing at `l7r/static/`.

5. **404 handling**: A CherryPy error-page hook that renders `_404.html` through the shared layout.

6. **Template context**: a small helper `make_context(section_slug, **extra)` returns the standard context (nav_sections, current_section, extras). Templates extend `_layout.html`.

7. **Section registry**: `sections.py` defines `SECTIONS` - a tuple of `Section` dataclasses with `slug`, `label`, `path`, `enabled`. Single source of truth for the nav.

## Complexity Tracking

No violations. No deferred gates. No complexity-tracking entries needed.
