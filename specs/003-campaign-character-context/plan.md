# Implementation Plan: Campaign Character Context

**Branch**: `main` (no feature branch - GM handles git) | **Date**: 2026-07-02 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-campaign-character-context/spec.md`

## Summary

Feed the campaign's other character backstories into the synthesis prompt so new backstories stay consistent with the existing cast and can reference named characters via steering notes. Characters live in Obsidian Portal (OP). A new compliant module `chargen/opcache.py` maintains an id-keyed cache `{id: {updated_at, name, tags, bio, game_master_info}}`, refreshed incrementally: one OP list call (gives every character's `updated_at`), then a body fetch only for ids that are new or changed, dropping deleted ids. The cache is a gitignored artifact refreshed + bundled at `make prepare-deploy` (cold-start base) and refreshed in-memory at runtime with a short TTL. `synthesis.build_prompt` gains an `OTHER CAMPAIGN CHARACTERS` section + a consistency instruction; the `synthesize` route reports how many characters were included. Gathering context is non-blocking and non-fatal - unlike the corpus, OP failure degrades to "0 characters in context," never blocks synthesis.

## Technical Context

**Language/Version**: Python 3.13 (chargen webapp).

**Primary Dependencies**: CherryPy + Jinja2; `requests` + OAuth (existing `chargen/op.py`); `google-genai` (existing). No new dependencies.

**Storage**: Files only. New: a gitignored `webapp/opcache/characters.json` cache (bundled into the image, like `setting/`). OP is the durable source of truth.

**Testing**: pytest + pytest-cov; OP boundary via saved fixtures. Playwright for the small UI readout.

**Target Platform**: Linux container (dev) + Fly.io. Ephemeral: scale-to-zero, 2 machines, no durable local disk - each instance reconciles against OP independently.

**Project Type**: Web application (chargen sub-app under the l7r toolkit).

**Performance Goals**: Steady-state context gather = 1 list call + only-changed body calls (usually 0 during a session); short TTL so re-rolls don't re-list. Added latency small and roughly constant vs. cast size.

**Constraints**: Hyphens only in committed files; preserve all existing synthesis behavior; graceful degradation on OP failure (never fail-loud); `gemini-3.1-pro-preview`; GM handles git.

**Scale/Scope**: ~81 characters today, growing. All-campaign scope in v1. ~1 new module + op.py helper + prompt wiring + route/template readout + Makefile/Dockerfile/gitignore + tests.

## Constitution Check

*GATE: passed. Re-checked after design - unchanged.*

- **I. Accessibility-First Viewports (NON-NEGOTIABLE)** - **PASS (committed)**. The only UI change is a small "N campaign characters in context" readout inside the already-audited synthesis result block. Commit to re-running the screenshot suite + DOM audit at GM-100/200/tablet/mobile and a `frontend-review` pass before the UI task is done.
- **II. Bold, Intentional Design** - **N/A**. No new surface; the readout reuses existing chargen styling.
- **III. Pool Data Conventions** - **N/A**. No recurring pool content is produced.
- **IV. One Canonical Home for GM Source** - **N/A**. No SOURCE blocks added or moved. The cache is a derived, read-only, gitignored snapshot of OP (like the corpus snapshot), not a canonical home and not committed.
- **V. Protecting the GM's Writing (NON-NEGOTIABLE)** - **PASS**. The cache only reads OP; no task modifies OP content or any SOURCE block (the existing save/Upload flow is unchanged).
- **VI. Verify Before Reporting Done** - **PASS (committed)**. Five-point Python gate on the new module; OP boundary via saved fixtures; screenshot + DOM audit + frontend-review for the readout; `make done`; a live smoke that campaign context reaches the prompt and that OP-down degrades gracefully.
- **VII. De-Localized Generation by Default** - **N/A**. No pool content generated; runtime per-character output is session-scoped.
- **VIII. Direct Voice Over Framing Distance** - **N/A**. No new committed in-world content.
- **IX. Setting Integration** - **PASS**. Uses the campaign's own character data; invents no new named figures in committed files, so no campaign-names-cache collision.
- **X. Python Discipline (NON-NEGOTIABLE)** - **PASS (committed)**. New pure logic lands in `chargen/opcache.py` under the gate (ruff, `mypy --strict`, 100% coverage, red-green TDD). The OP calls are the boundary: the messy try/except for graceful degradation lives in the grace-listed `chargen/op.py` (its helpers return `[]`/`None` on failure and log), so `opcache.py` stays free of broad excepts and just handles empty/None returns. OP responses tested via saved fixtures (Principle X.5). No new deps; `logging`/`cherrypy.log` not `print`; OP creds via ConfigObj (existing). Coverage gate extended with `--cov=chargen.opcache`.
- **XI. Japanese Authenticity (NON-NEGOTIABLE)** - **N/A**. No new committed Japanese-script content; fetched character bodies are runtime prompt input, not generated pool entries.

No gates DEFERRED; Complexity Tracking empty.

## Project Structure

### Documentation (this feature)

```text
specs/003-campaign-character-context/
├── plan.md              # This file
├── research.md          # Phase 0 decisions
├── data-model.md        # Phase 1 entities
├── quickstart.md        # Phase 1 build/verify/smoke
├── contracts/
│   └── opcache.md       # module API + the synthesize-response extension
└── checklists/requirements.md
```

### Source Code (repository root)

```text
webapp/
├── chargen/
│   ├── opcache.py            # NEW (compliant): id-keyed incremental cache + context assembly
│   ├── test_opcache.py       # NEW: red-green tests, 100% coverage
│   ├── fixtures/             # NEW/EXTEND: saved OP list + body responses
│   ├── op.py                 # MODIFY (grace): add updated_at to existing_characters; add
│   │                         #   get_character_body(id) single-GET; both fail soft (return None/[])
│   ├── synthesis.py          # MODIFY (grace): build_prompt gains OTHER CAMPAIGN CHARACTERS
│   │                         #   section + consistency instruction; excludes self
│   ├── website.py            # MODIFY (grace): synthesize route gathers context, adds count to envelope
│   └── templates/index.html  # MODIFY: small "N campaign characters in context" readout
├── opcache/                  # NEW (gitignored, bundled): characters.json cache
├── Makefile                  # MODIFY: prepare-deploy refreshes + bundles the cache; cov adds opcache
├── pyproject.toml            # MODIFY: keep opcache.py OUT of grace lists (strict + covered)
├── Dockerfile                # MODIFY: COPY opcache
└── .gitignore                # MODIFY: opcache/
```

**Structure Decision**: Same split as the last feature - new compliant logic isolated in `chargen/opcache.py` (gated), the external-boundary mess quarantined in grace-listed `op.py` (fail-soft helpers), thin wiring in the grace-listed route/template. Cache resolution mirrors `brief.py`'s bundle pattern (`chargen/../opcache` -> `webapp/opcache` in dev, `/app/opcache` in prod).

## Complexity Tracking

*No constitutional gates DEFERRED or violated; intentionally empty.*
