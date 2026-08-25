# Implementation Plan: Scripted NPC Naming with a Live Used-Name Cache

**Branch**: `200-scripted-npc-names` (no branch; `SPECIFY_FEATURE` on main in the session clone) | **Date**: 2026-08-25 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/200-scripted-npc-names/spec.md`

## Summary

Make the campaign-character cache (`webapp/opcache/characters.json`) the single source of used
names, refreshed after every character creation and when stale; make the `/name` skill pool the
single source of given names for the `/name` skill, the `/names` page and the chargen engine;
move exclusion (loose similarity vs used names) and set-distinctness (strict, vs an avoid list)
INSIDE the engine with `gender=` / `avoid=` constructor arguments, so `/chargen` rolls a correctly
named character in one call. Retire the cookie scraper and the engine's private name lists.

## Technical Context

**Language/Version**: Python 3.14 (webapp), plain-Python skill scripts run from the skill dir
**Primary Dependencies**: existing - `chargen.op` OAuth helpers, `chargen.opcache`, `l7r.names` pool reader
**Storage**: `webapp/opcache/characters.json` (gitignored, atomic write-then-rename from this feature on)
**Testing**: pytest (`make done` in `webapp/`; `pytest` in `.claude/skills/name/`)
**Target Platform**: the dev container; the deployed webapp (pool files already bundled by `make prepare-deploy`)
**Project Type**: library + CLI scripts + web app
**Performance Goals**: a name pick is a file read, never a network call; tests construct hundreds of characters, so the pool and cache reads are memoized (pool by directory, cache by file mtime)
**Constraints**: engine picks are network-free; OP refresh happens only at explicit call sites (post-create, `pick_name.py` staleness check, the `/chargen` Step 2 script, the webapp's hourly thread); every OP call fail-soft
**Scale/Scope**: 200 pool names, ~120 roster names

**Single-artifact target** (constitution VI): `webapp/chargen/test_namepool.py` - the one test file the new pure-logic module is proven on before the whole gate runs; for the skill, `pick_name.py` run once against the live cache before its test file is swept.

**Every step is two steps.** Each phase below separates the reference artifact from the sweep.

## Constitution Check

- **I. Accessibility-First Viewports**: N/A - no UI change (the `/names` page keeps reading the same pool files; the chargen page's Generate button changes behavior, not markup).
- **II. Bold, Intentional Design**: N/A - no new UI surface.
- **III. Pool Data Conventions**: N/A - pool contents untouched (FR-013); the JSONL name pool predates the markdown-with-YAML convention and is not migrated here.
- **IV. One Canonical Home for GM Source**: N/A - no SOURCE blocks.
- **V. Protecting the GM's Writing**: PASS - nothing inside SOURCE markers is touched.
- **VI. Verify Before Reporting Done**: PASS - per-task verification listed in tasks.md; reference artifact then sweep; `make done` backgrounded once at the end; the `/chargen` Step 2 script is executed for real (gender pinned, set of 3) as the end-to-end check.
- **VII. De-Localized Generation**: N/A - no pool content generated.
- **VIII. Direct Voice**: N/A - no in-world prose.
- **IX. Setting Integration**: PASS - the feature is what keeps new names from colliding with the campaign roster.
- **X. Python Discipline**: PASS - new modules (`chargen/similarity.py`, `chargen/namepool.py`, opcache additions) are typed strictly, ruff-clean, 100% covered (added to the Makefile `cov` target); red-green TDD on each new behavior; `op.py` / `character.py` / `constants.py` stay on the grace list but their changes are minimal and exercised by tests; no file approaches 1,000 lines.
- **XII. Historical Grounding Bookends**: N/A - no generator asserts anything about the world; names come from the existing curated pool.
- **XIII. No Known Regressions**: PASS - baseline taken 2026-08-25 on unmodified HEAD in a detached worktree (`git worktree add --detach <scratch>/base HEAD`): `make done` -> `gate green`; `.claude/skills/name` -> 89 passed. Zero new failures at merge.
- **XIV. Fix defects where found**: the engine's never-populated `USED_NAMES` (start-event thread) is fixed here; two pool names that are live NPCs are handled by exclusion (pool deletion would pre-empt the GM's open pool-size question).

## Project Structure

### Documentation (this feature)

```text
specs/200-scripted-npc-names/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── tasks.md
```

### Source Code

```text
webapp/chargen/
├── similarity.py         # NEW canonical: edit_distance, is_too_similar, rhymes, set_conflict (typed)
├── test_similarity.py    # NEW (ported from the skill's tests)
├── namepool.py           # NEW: load pool via l7r.names, used_given_names(cache), pick_name(...)
├── test_namepool.py      # NEW
├── opcache.py            # + atomic save, cache_age(), refresh_if_stale(), used_given_names()
├── test_opcache.py       # + tests for the above
├── op.py                 # create_character: post-create refresh (fail-soft); hourly thread refreshes the cache file
├── character.py          # unused_name(gender, avoid) via namepool; gender=/avoid= on all constructors
├── constants.py          # NAMES/USED_NAMES loading from txt removed; USED_NAMES stays as the in-process set
├── male_names.txt        # DELETED
├── female_names.txt      # DELETED
└── Makefile              # cov target adds chargen.similarity + chargen.namepool
.claude/skills/name/
├── pick_name.py          # reads used names from opcache (refresh-if-stale via OAuth; --refresh forces); stale warning;
│                         #   --avoid a,b and --bank N (N per gender, one mutually distinct set) for FR-015
├── validate_pool.py      # same source
├── fix_pool.py           # same source
├── similarity.py         # thin shim re-exporting webapp/chargen/similarity.py
├── fetch_campaign_names.py, test_fetch_campaign_names.py, campaign-names.txt, setup.sh  # DELETED
└── SKILL.md              # no cookie / no /loop; "refresh names" = pick_name.py --refresh
.claude/skills/chargen/SKILL.md   # Step 2: gender= and avoid=, refresh_if_stale(); re-roll loop and manual set check removed;
                                  #   Step 3b: name bank for invented supporting cast (FR-015)
.claude/skills/synthesize/SKILL.md # Step 2c: name bank (pick_name.py --bank --avoid <subject given name>) for invented supporting cast (FR-015)
.claude/agents/backstory-review.md # collision rule stays as backstop; adds: invented names must come from the bank file
CLAUDE.md                          # skill table rows for /name and /chargen
```

## Phase 0 - Research

See [research.md](research.md): the two name sources measured, the dead start-event thread, the
decision on where refreshes happen, and the accepted supply drop (862 -> 200).

## Phase 1 - Design

- [data-model.md](data-model.md): pool entry, cache entry, used given name, avoid list.
- [quickstart.md](quickstart.md): how to pick a name from the skill, from the engine, and how to verify the cache updated after a creation.
- Contracts: `pick_name.py [--refresh] [--avoid a,b] [--bank N] <m|f|p|N shorthand>`; the engine's constructor kwargs (`gender: str | None`, `avoid: Sequence[str]`), `namepool.pick_name(gender, pool, used, avoid, rng)` raising `NamePoolExhausted`, `opcache.refresh_if_stale(max_age_seconds=3600) -> bool`, `opcache.used_given_names(path) -> frozenset[str]`.

## Phase 2 - Tasks

Generated by `/speckit-tasks` into tasks.md.
