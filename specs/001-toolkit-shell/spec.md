# Feature Specification: L7R Toolkit Phase 1 — App Shell + Chargen + Relics

**Feature Branch**: `001-toolkit-shell`

**Created**: 2026-05-27

**Status**: Draft

**Input**: User description: "Fold the existing chargen Python webapp into a 'real' multi-section app called the L7R Toolkit. Phase 1 delivers an app shell with cross-section navigation plus two sections: a modernized chargen (preserving its existing functionality) and a relics catalog (porting the static prototype into the chargen CherryPy backend). Modernize in place — CherryPy stays. Localhost only; no auth in Phase 1."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Browse the relic pool with the prototype's look and feel (Priority: P1)

The GM opens the L7R Toolkit in a browser and navigates to the Relics section. The catalog shows all 42 pre-saved relics grouped by Fortune, with the same visual identity as the static prototype that was previously built: vermillion-stamped kanji headers per Fortune, kanji-dominant cards, clan tags. A sticky filter rail of hanko-style seals lets the GM narrow to a single Fortune. Clicking a relic opens a detail page with the kanji-as-exhibition treatment, the full prose, a meta band of Fortune/Clan/Type/Resides-at/Tied-to, and previous/next navigation within the same Fortune.

**Why this priority**: The relics work is the most recent, the data already exists in the pool, and the prototype already establishes the design system. Porting it into the live app is the highest-confidence delivery of Phase 1 and is what the GM most wants to see end-to-end.

**Independent Test**: Start the L7R Toolkit server on localhost; visit `/relics`; verify all 42 relics appear in 7 Fortune sections with the correct kanji, names, clan tags, and ordering. Click any seal in the filter rail and verify only that Fortune's cards remain visible. Click any card and verify the detail page renders with the expected meta band and prose. Use prev/next within a Fortune to traverse all 6 of that Fortune's relics in a cycle.

**Acceptance Scenarios**:

1. **Given** the L7R Toolkit server is running on localhost, **When** the GM visits `/relics`, **Then** the page shows the relics catalog with 7 fortune sections totaling 42 relic cards, styled identically to the static prototype.
2. **Given** the relics catalog is open, **When** the GM clicks the seal for one Fortune (e.g., Benten), **Then** the other six Fortune sections become hidden and the page scrolls to (or focuses on) the chosen Fortune.
3. **Given** the catalog is open, **When** the GM clicks a relic card, **Then** the browser navigates to `/relics/<slug>` and shows the detail page with the kanji presented at hero scale, the relic's name, romaji, Fortune, Clan, Type, Resides-at, Tied-to, and full prose.
4. **Given** a relic detail page is open, **When** the GM clicks the "next" link in the footer, **Then** the next relic in the same Fortune (wrapping at the end) is shown.
5. **Given** the GM browses at 200% Chrome zoom on a 1850×1173 outer window, **When** they scroll through the catalog and open a detail page, **Then** no text is truncated with `…` or clipped by overflow, no element overflows its container, and all controls remain comfortably usable.

---

### User Story 2 — Use the existing character generator with the new visual identity (Priority: P2)

The GM clicks the Character Generator nav link from any section and lands on the chargen page. The page uses the same shared shell as the rest of the toolkit (the warm-paper / sumi-ink / vermillion palette, the Fraunces + EB Garamond + Shippori Mincho typography, the same nav). The chargen UI's form fields, dropdowns, AJAX behavior, art-generation flow, and Obsidian Portal upload all work exactly as they did in the standalone chargen app.

**Why this priority**: Chargen's existing function must keep working — it's the GM's existing tool. Modernizing it visually is important but the functional regression risk is what makes this P2 rather than P1: any regression here breaks an established workflow.

**Independent Test**: Open `/chargen` (or whichever the route ends up being). Generate a Samurai character; verify the form fields populate. Generate art via the existing Gemini integration; verify the image appears with the existing crop UI. Submit an upload to the test Obsidian Portal campaign; verify it succeeds (or fails gracefully with the existing error path). Compare against the standalone chargen — functionally identical, visually new.

**Acceptance Scenarios**:

1. **Given** the L7R Toolkit server is running, **When** the GM visits `/chargen`, **Then** the chargen UI is rendered inside the new shell (shared nav, shared palette, shared typography) and all form fields are present.
2. **Given** the chargen UI is open, **When** the GM clicks "generate" for a Samurai, **Then** the existing `/generate` AJAX endpoint returns a character payload and the form populates exactly as in the standalone app.
3. **Given** a generated character with art, **When** the GM submits the upload, **Then** the existing `/upload` endpoint executes and the result is shown.
4. **Given** the GM uses chargen at 200% Chrome zoom, **When** they interact with all form controls, **Then** every control is reachable and readable; no labels or option text are clipped.

---

### User Story 3 — Land on a coherent toolkit homepage with discoverable sections (Priority: P3)

The GM visits the root URL and sees a landing page that names the toolkit, briefly explains what it is, and provides clear navigation to each section. The Names section appears in the nav as a placeholder (so the structure is visible) but indicates it is forthcoming.

**Why this priority**: The shell ties everything together but is the simplest piece. It is P3 because without P1 and P2 the shell has nothing meaningful to point to.

**Independent Test**: Visit `/`. Verify the page shows the toolkit name, a short tagline, and nav links to Character Generator, Relics, and Names. Verify each link routes correctly (with Names showing a "coming soon" or similar placeholder). Verify the shell is identical to the shell used by `/relics` and `/chargen`.

**Acceptance Scenarios**:

1. **Given** the server is running, **When** the GM visits `/`, **Then** a landing page renders with the toolkit name, a one-paragraph description, and nav links to all three sections.
2. **Given** the landing page, **When** the GM clicks the Names nav link, **Then** they reach a `/names` page that indicates the section is coming in Phase 1.5 (no broken link, no 404).
3. **Given** the GM moves between sections via nav, **When** they switch from `/`, `/relics`, `/chargen`, or `/names`, **Then** the same nav header is present and the active section is visually indicated.

---

### Edge Cases

- **Long kanji on a relic card**: The relic with the 7-character kanji "太郎兵衛の太鼓" must render without clipping at the 200%-zoom viewport. The prototype already solved this by allowing the kanji to wrap to two lines; the live app preserves that behavior.
- **Long relic prose**: Some entity descriptions are 150–200 characters. The detail page must show the full prose; cards must not truncate the named-entity text.
- **Pool file changes**: If a relic file is added/edited in `/workspace/.claude/skills/relic/pool/`, the catalog must reflect that on the next request (re-read at request time, or re-load at process start with a known way to refresh).
- **A pool file with malformed YAML frontmatter**: Skipping the file with a logged warning is preferred over crashing the catalog page.
- **The chargen `development-secrets.ini` is missing or invalid**: Chargen has its own behavior here; the new shell should not regress that path. Non-chargen sections (Relics, Names) MUST function regardless of chargen-secrets state.
- **Direct deep link to `/relics/<slug>` with an unknown slug**: Render a clean 404 inside the shell, not a CherryPy stack trace.

---

## Requirements *(mandatory)*

### Functional Requirements

#### Shell and navigation

- **FR-001**: The L7R Toolkit MUST serve a landing page at `GET /` showing the toolkit name, a brief description, and navigation to the available sections.
- **FR-002**: The toolkit MUST present a consistent shell across all pages: a header with the toolkit brand, a sticky nav with links to each section (Character Generator, Relics, Names), and a footer.
- **FR-003**: The shell MUST use the canonical design system: warm-washi background (`#F4E8CC`), sumi-ink body text (`#14110E`), vermillion accent (`#B8332A`), and the Fraunces + EB Garamond + Shippori Mincho typographic system.
- **FR-004**: The currently-active section MUST be visually distinguished in the nav.

#### Relics catalog

- **FR-005**: `GET /relics` MUST render all relics from `/workspace/.claude/skills/relic/pool/<fortune>/*.md`, grouped by Fortune, with one section per Fortune.
- **FR-006**: Each relic card MUST show: the Japanese kanji as the visual anchor; the relic_type (main category only, the parenthetical descriptor truncated to the title tooltip); the clan tag; the English name; and the named_entity.
- **FR-007**: The Fortune filter rail MUST be sticky (always visible while scrolling) and present a hanko-stamp seal per Fortune plus an "all" seal.
- **FR-008**: Clicking a Fortune seal MUST hide the other Fortune sections and scroll to the chosen one; clicking "all" MUST restore all sections.
- **FR-009**: `GET /relics/<slug>` MUST render the relic detail page with: the kanji at hero scale; the relic name; the romaji; a meta band of Fortune/Clan/Type/Resides-at/Tied-to; the full prose body; and previous/next navigation within the same Fortune.
- **FR-010**: Markdown-style emphasis (`*italic*`) inside relic prose MUST render as `<em>` HTML. Paragraph breaks (`\n\n`) MUST render as `<p>` elements.
- **FR-011**: A pool file with malformed YAML frontmatter MUST NOT crash the catalog page; the file MUST be skipped with a logged warning.
- **FR-012**: A request to `/relics/<unknown-slug>` MUST return a 404 inside the toolkit shell, not a CherryPy stack trace.

#### Character generator

- **FR-013**: `GET /chargen` MUST render the existing chargen UI inside the new shared shell with the new design system applied to layout, typography, and color, while preserving the chargen form-field structure and all interactive behaviors.
- **FR-014**: The existing chargen AJAX endpoints (`/generate`, `/upload`, and any others used by the chargen template) MUST continue to function on their existing paths.
- **FR-015**: Chargen's existing dependencies (CherryPy, Jinja2, ConfigObj, google-genai, opencv-python-headless, pillow, requests, requests-oauthlib) MUST continue to be installed; the toolkit MUST NOT remove them.

#### Names placeholder

- **FR-016**: `GET /names` MUST render a placeholder page inside the shared shell indicating that the Names section is forthcoming in Phase 1.5.

#### Accessibility and verification

- **FR-017**: At GM-100 (1850×1050 viewport, 100% zoom) and GM-200 (925×525 viewport, 200% zoom), as well as at tablet (800×1100) and mobile (390×844) breakpoints, every page in the toolkit MUST pass the screenshot/overflow audit defined by the project's Playwright suite — no `text-overflow: ellipsis` truncation on substantive content, no `overflow: hidden` clipping of meaningful elements, no element where `scrollWidth/scrollHeight` exceeds the corresponding offset dimension.
- **FR-018**: All interactive controls (nav links, seal filter buttons, card links, detail-page footer links, chargen form controls) MUST have visible focus states (per the existing `:focus-visible` rule in the prototype CSS).
- **FR-019**: All pages MUST render with the canonical typographic stack from Google Fonts loaded over the network (Fraunces, EB Garamond, Shippori Mincho).

#### New code quality

- **FR-020**: All new Python code added to the toolkit (the `l7r/` package containing routing, relic-data loading, template helpers) MUST pass `ruff check`, `ruff format --check`, `mypy --strict`, `pytest`, and `pytest --cov-fail-under=100` on the new package.
- **FR-021**: External boundaries in new code (file I/O against the pool directory) MUST be tested via saved fixtures or against real test files placed in a test fixtures directory, not via transport-layer mocks of `open()`/`Path`.
- **FR-022**: New code MUST follow the constitution's Principle X rules (no swallowed exceptions; logging instead of `print`; ConfigObj or pydantic-settings for config; no hardcoded magic strings).

### Key Entities

- **Relic**: Loaded from `/workspace/.claude/skills/relic/pool/<fortune>/<slug>.md`. Attributes (from frontmatter): `name`, `japanese_romaji`, `japanese_kanji`, `fortune` (slug), `clan` (slug or "any"), `temple`, `named_entity`, `relic_type`. Body: multi-paragraph prose. Derived: `slug` (filename basename without `.md`).
- **Fortune**: One of the seven major Rokugani Fortunes (Benten, Bishamon, Daikoku, Ebisu, Fukurokujin, Hotei, Jurojin). Attributes: `name` (English display), `domain` (e.g., "Fortune of romantic love"), `kanji` (e.g., "弁天"). The catalog groups relics by Fortune.
- **Clan**: A lookup label for the relic's clan tag. Used purely for display (e.g., `crab` → "Crab", `any` → "Anywhere").
- **Section**: A top-level area of the toolkit (Character Generator, Relics, Names). Attributes: route prefix, nav label, "is enabled in this phase" flag.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: From a fresh clone, the GM can install dependencies and start the toolkit on localhost in under 5 minutes.
- **SC-002**: At GM-100 and GM-200 viewports, the relics catalog above-the-fold view shows the masthead, the sticky nav, the first Fortune section header, and at least one full relic card without horizontal scrolling.
- **SC-003**: A round-trip "find a relic and read its detail" task takes the GM no more than four interactions (visit `/`, click Relics, click a Fortune seal, click a card).
- **SC-004**: All 42 pool relics appear in the live catalog; none is missing because of parser errors.
- **SC-005**: Zero text truncation or container overflow is reported by the Playwright DOM audit at any of the four standard viewports.
- **SC-006**: Existing chargen functionality (character generation, art generation, OP upload) shows no regression compared to the standalone chargen app — the GM's existing manual flow continues to work as a smoke test.
- **SC-007**: The `make done` target passes on the new `l7r/` package with 100% coverage and no lint, format, or type errors.

---

## Assumptions

- The GM uses Chrome at 200% browser zoom on a 1850×1173 outer window (per user-accessibility memory). All UI verification targets these dimensions.
- The chargen webapp at `/workspace/webapp/` remains the deployment target; we modernize in place rather than relocating.
- CherryPy 18.x with Jinja2 3.x is the stack for Phase 1. No FastAPI / Flask migration.
- Google Fonts (Fraunces, EB Garamond, Shippori Mincho) are loaded from `fonts.googleapis.com` at request time, as in the prototype. No font self-hosting in Phase 1.
- Pool data is read at process startup and cached in memory for the lifetime of the server. A server restart picks up changes. (Hot reloading is out of scope; a `make` target or process restart suffices.)
- No persistence layer is added in Phase 1. Chargen continues to use its existing Obsidian-Portal-as-storage approach.
- The relics catalog is read-only in Phase 1. Generating new relics via Claude API is Phase 2+.
- Tests for legacy chargen modules are NOT being added in Phase 1. The legacy code retains its one-time grace period per Constitution Principle X. New code is held to the full Principle X standard.
- The toolkit serves a single GM on localhost. No authentication, no rate limiting, no multi-tenancy. Public deployment (Fly.io) and auth come after Phase 1.5.
- Chargen's existing "all config serialized into HTML on /chargen" behavior is preserved (it's a known issue that the new shell doesn't try to fix; localhost-only is the mitigation).
