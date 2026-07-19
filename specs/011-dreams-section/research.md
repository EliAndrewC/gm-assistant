# Phase 0 Research: Dreams Section (Webapp)

All Technical Context unknowns are resolved below. No open NEEDS CLARIFICATION remain.

## Decision 1: Reuse the relic pool-loader pattern for scene loading

- **Decision**: Add `l7r/dreams.py` with a `DreamScene` frozen dataclass and a `load_dream_scenes(pool_dir)` function that mirrors `l7r/pool.py` (`load_relics`): glob `*.md`, split YAML frontmatter from body with the same regex approach, skip files missing required fields with a logged warning (graceful degradation), sort deterministically, and expose the slug from the filename stem.
- **Rationale**: `l7r/pool.py` is the established, 100%-covered convention for file-backed content (Constitution Principle III). Mirroring it keeps the loaders consistent and inherits the malformed-file-skip behavior FR-008 requires.
- **Alternatives considered**: A generic shared loader abstracting relics + dreams - rejected as premature; the two schemas differ enough (dreams are flat and sender-keyed; relics are per-fortune with clan/kanji fields) that a shared base would add coupling for little gain now.

## Decision 2: Render scene + framework markdown with markdown-it-py (already a dependency)

- **Decision**: Render the dream-scene body and the framework page from markdown to HTML using `markdown-it-py` (`markdown-it-py==4.2.0` is already in `requirements.txt`). Enable only the CommonMark core plus tables; do not enable raw-HTML passthrough (the content is trusted GM/dev-authored markdown, but keeping HTML disabled is defense-in-depth). Wrap the rendered HTML in a scoped container styled to the existing archive aesthetic.
- **Rationale**: Dream scenes use headings, lists, blockquotes, bold/italic, and occasional tables - richer than the relic body, which `l7r/jinja_env.py` handles with a light `*italic*`-only converter. markdown-it-py is present, well-typed, and needs no new dependency (Principle X: pinned deps unchanged).
- **Alternatives considered**: Extend the existing italic-only converter - rejected (would reimplement a markdown parser badly). Add `python-markdown` - rejected (new dependency; markdown-it-py already vendored).

## Decision 3: Pool directory resolution and deploy bundling

- **Decision**: Resolve the dream pool the same way relics do: an env override `L7R_DREAM_POOL_DIR` for production, else the dev default `_HERE.parent.parent / '.claude' / 'skills' / 'dream' / 'pool'`. Extend `make prepare-deploy` to `cp -r ../.claude/skills/dream/pool skills/dream/pool` and set the env var in the Fly/Docker runtime to point at the bundled copy.
- **Rationale**: Identical to the relic path (`_resolve_default_pool_dir` + `L7R_RELIC_POOL_DIR`). `prepare-deploy` already copies `relic/pool` only (never `pool-local`), so extending it copies the **public tier only** - the spoiler tier is excluded at the bundling boundary automatically (FR-007).
- **Alternatives considered**: Read the pool live from `.claude/` at runtime in production - rejected; the Fly image has no repo mount, which is why `prepare-deploy` snapshots pool data into `webapp/skills/` (gitignored build artifact).

## Decision 4: Spoiler-tier exclusion is enforced structurally AND asserted by test

- **Decision**: The loader only ever reads the single configured pool directory (the public `pool/`); it has no knowledge of `pool-local/` and never walks siblings or parents. Add a regression test that constructs a pool dir containing a scene plus a sibling `pool-local/` dir with a decoy scene, and asserts the loader returns only the public scene. Also assert `prepare-deploy` copies `pool` (not `pool-local`) - a grep-style test over the Makefile recipe or a smoke check of the produced `skills/dream/` tree.
- **Rationale**: FR-007 / SC-004 is the load-bearing constraint. Structural exclusion (only-read-the-configured-dir) is the primary defense; a test freezes it so a future refactor cannot silently start walking the tree.
- **Alternatives considered**: A per-scene `spoiler:`/`tier:` frontmatter flag filtered at load time - rejected as the *primary* mechanism (a filter can be inverted by a bug); the directory boundary is the hard line. The frontmatter flag stays as documentation only.

## Decision 5: Framework text is a hand-authored markdown file shipped with the app

- **Decision**: The player-facing rules & framework prose lives in a hand-authored markdown file inside the app package (e.g. `l7r/content/dreams_framework.md`), rendered on the landing page via Decision 2. It is a player/GM-readable adaptation of the /dream skill framework: theology (constant sending, poor receiver, expected noise/silence), attunement, and the roll mechanic (bands, the significant 10 + lucid point pool, rerolls) - omitting authoring internals (pool tiers, fragment-writing, spoiler handling).
- **Rationale**: The GM chose a hand-authored player-facing adaptation over mirroring the SKILL. A markdown file in `l7r/` is COPYed by the Dockerfile (`COPY l7r ./l7r`) with no extra bundling, and is maintained alongside the feature. It is dev-authored prose, not a GM SOURCE block, so Principles IV/V do not constrain it.
- **Alternatives considered**: Auto-derive from `SKILL.md` at request time - rejected (GM chose hand-authored; the SKILL contains GM-only material that must not surface). Inline the prose in the Jinja template - rejected (markdown file is easier to edit and reuses the scene renderer).

## Decision 6: Routing, nav, and access mirror the relics section

- **Decision**: Add a `dreams(self, slug=None)` route on the L7R `Root` (index when `slug is None`, detail otherwise, `_render_404()` for an unknown slug), templates `dreams_index.html` and `dream_detail.html` extending `_layout.html`, and a `Section(slug='dreams', label='Dreams', path='/dreams', enabled=True)` in `sections.py`. No auth change: the root tree defaults to `min_role: anonymous` (public); only `/archive` is GM-gated, so `/dreams` is public automatically.
- **Rationale**: Exact parallel to `/relics`, which is the proven pattern for a public file-backed catalog section.
- **Alternatives considered**: None; consistency with the existing section is the goal.

## Decision 7: Design reuses the existing system (no greenfield UI)

- **Decision**: The Dreams pages reuse the established design system - `--font-display: Fraunces`, `--font-body: EB Garamond`, `--font-jp: Shippori Mincho`, and the existing `l7r.css` tokens and archive aesthetic. No new typefaces, no new color system. New CSS is limited to scene-specific layout (the framework prose block, the scene sections, the fragment tables) built from existing tokens.
- **Rationale**: Principle II is satisfied by extending the site's existing "editorial Japanese archive" system rather than inventing new typography. This is not greenfield UI, so the `frontend-design` plugin is not required; the direction is "match Relics."
- **Alternatives considered**: A distinct visual treatment for Dreams - rejected; consistency with the rest of the toolkit is the point.

## Historical Grounding (Principle XII)

- **Applicability**: N/A. Principle XII gates features that change **what a generator asserts about the world** (settlement/compound layouts, how a place was farmed/built/lived). This feature renders pre-existing, already-grounded dream-divination content; it asserts no new world-facts about places, farming, or building. No opening/closing grounding bookend is required. (The one example scene's setting facts - Daikoku's domain, the Aki lineage debt, Masamune - were verified against `l7r.md` during scene authoring, not by this webapp feature.)
