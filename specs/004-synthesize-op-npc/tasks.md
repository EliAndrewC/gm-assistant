# Tasks: /synthesize skill for existing Obsidian Portal NPCs

**Feature**: `specs/004-synthesize-op-npc/` | **Plan**: [plan.md](plan.md)

Test-first (red-green) per Constitution Principle X. Pure logic (`opsynth.py`) at
100% coverage; the `op.py` network boundary is fixture-tested. `[P]` = safe to do
in parallel (distinct files, no incomplete-task dependency). Tasks that touch the
same file (`opsynth.py`, `test_opsynth.py`, `op.py`, the skill) are not `[P]`
with each other.

All Python paths are under `webapp/`; run tooling from `/gm-assistant/webapp`.

## Phase 1: Setup

- [x] T001 [P] Save the real OP character-page HTML (already fetched this session for `daidoji-no-etsuko-jitsuyo`, containing `<div class='tagline'><p><em>drinking companion of Kyoma</em></p></div>` plus the empty banner tagline) to `webapp/chargen/fixtures/op_character_page.html`.
- [x] T002 [P] Save a real OP character JSON (the raw `get_character_body`-shaped response incl. `description`, `game_master_info`, `tags`, `updated_at`) to `webapp/chargen/fixtures/op_character.json`.
- [x] T003 Create `webapp/chargen/opsynth.py` (module docstring, `from __future__ import annotations`, `logging.getLogger(__name__)`, marker + cache-path constants) and an empty `webapp/chargen/test_opsynth.py`.

## Phase 2: Foundational (blocking prerequisites)

- [x] T004 [US1] Add fail-soft `fetch_character_page(character_url) -> str | None` to `webapp/chargen/op.py` (GET via `_get_browser_session`, return HTML on 200 else None, log on failure, never raise); add a fixture-replayed test in `webapp/chargen/test_op.py` that feeds `op_character_page.html` through a stubbed session and asserts the HTML is returned, plus a failure path returning None.

## Phase 3: User Story 1 - Reviewable backstory for a named wiki character (P1)

**Goal**: `/synthesize <name>` resolves the character, reads their data + tagline, and presents a grounded backstory.
**Independent test**: run the skill for a real NPC and confirm a backstory appears that reflects the tagline and does not contradict the cast.

- [x] T005 [P] [US1] Write failing tests in `webapp/chargen/test_opsynth.py` for `match_character(query, characters)`: unique/token-subset match ("Daidoji Jitsuyo" -> "Daidoji no Etsuko Jitsuyo"), ambiguous (>1 candidate) result, and no-match with nearest names; parametrize the name variants.
- [x] T006 [US1] Implement `match_character` in `webapp/chargen/opsynth.py` to pass T005.
- [x] T007 [US1] Write failing tests for `parse_tagline(html)` using `fixtures/op_character_page.html` (returns "drinking companion of Kyoma", not the empty banner tagline) and an empty/absent-tagline case returning "".
- [x] T008 [US1] Implement `parse_tagline` to pass T007.
- [x] T009 [US1] Write failing parametrized tests for `infer_caste(tags, gm_info)`: monastic markers -> Monk, peasant markers -> Peasant, clan tags/default -> Samurai, precedence and case-insensitivity.
- [x] T010 [US1] Implement `infer_caste` to pass T009.
- [x] T011 [US1] Write failing tests for `build_synthesis_character(body, tagline)` (maps to `full_name`/`tags`/`summary`/`public`/`private`, empty-string coalescing).
- [x] T012 [US1] Implement `build_synthesis_character` to pass T011.
- [x] T013 [US1] Add `description` to `op.get_character_body`'s projection; update the `test_op.py` fixture assertion to include `description`.
- [x] T014 [US1] Author `.claude/skills/synthesize/SKILL.md`: front matter + the resolve -> gather (body + page tagline) -> infer-caste -> synthesize flow, calling the modules via Bash snippets and writing the scratchpad handoff JSON; present the backstory. (US2 adds the menu; US3 adds related context.)

## Phase 4: User Story 2 - Review dispositions and safe save (P2)

**Goal**: present the review (two listed options plus a free-text changes box) and save into GM-only notes without clobbering existing notes.
**Independent test**: exercise each choice; confirm as-is/with-changes save correctly and existing notes survive; a second save yields one section.

- [x] T015 [P] [US2] Write failing tests for `merge_backstory(existing_gm_info, prose)`: append-when-absent (preserves prior notes, one blank-line gap), replace-in-place-when-present, idempotence (twice -> one section, unchanged), and preservation of text after the block.
- [x] T016 [US2] Implement `merge_backstory` in `webapp/chargen/opsynth.py` to pass T015.
- [x] T017 [US2] Extend `.claude/skills/synthesize/SKILL.md` with the review (AskUserQuestion): two listed options - (1) upload as-is, (2) generate another -> re-run synthesis + re-present - plus the free-text ("Other") box treated as "upload with changes" (typed text IS the changes; apply then upload). On upload: re-fetch `game_master_info`, `merge_backstory`, `op.update_character(id, game_master_info=...)`, and report exactly what was written. (Refined post-implementation from a three-button menu to two-plus-free-text at the GM's request.)

## Phase 5: User Story 3 - Surface related characters (P3)

**Goal**: when the tagline names a cast member, surface others linked to the same NPC as extra grounding.
**Independent test**: synthesize a character whose tagline names an NPC referenced by others; confirm those others are surfaced; a tagline naming no cast member proceeds cleanly.

- [x] T018 [P] [US3] Write failing tests for `related_by_tagline(subject_tagline, cast_taglines, cast_names)`: finds the named cast member, returns others whose taglines reference the same name, returns [] when no cast member is named.
- [x] T019 [US3] Implement `related_by_tagline` in `webapp/chargen/opsynth.py` to pass T018.
- [x] T020 [US3] Write failing tests for `refresh_taglines(cache, characters, page_fetch, parse)` (injected fetch/parse): fetch only new/changed ids, keep unchanged, drop absent; assert the injected fetch is called only for the expected ids.
- [x] T021 [US3] Implement `refresh_taglines` as PURE logic in `webapp/chargen/opsynth.py` (injected `fetch_tagline`) - moved here from `op.py` so the incremental-merge logic is under the 100% coverage gate; the skill wires the real `op.fetch_character_page` + `opsynth.parse_tagline`. Cache file `webapp/opcache/taglines.json` (gitignored).
- [x] T022 [US3] Extend `.claude/skills/synthesize/SKILL.md` to compute + include related-character context when the tagline names a cast member (fail-soft: skip if the tagline cache is empty/unreachable).

## Phase 6: Polish & Cross-Cutting

- [x] T023 Confirm `webapp/opcache/taglines.json` is covered by the existing `webapp/.gitignore` opcache ignore (add if needed).
- [x] T024 Run `make done` from `webapp/` (ruff + format + mypy --strict + pytest + 100% coverage) and fix any gaps; ensure `opsynth.py` is at 100% and not on a grace list.
- [x] T025 Read-only end-to-end verification DONE against Daidoji Jitsuyo: resolve worked, tagline "drinking companion of Kyoma" read, caste Samurai inferred, 80 cast in context, backstory reflected the relationship grounded in Kyoma's real role. The live round-trip PATCH was DEFERRED to the GM by design - writing test content to a real OP NPC is an outward-facing change; `merge_backstory` is 100% unit-proven and `update_character` is the existing note-intake path, so the first real save is the GM's to trigger via the skill.
- [x] T026 Document the skill in `webapp/CLAUDE.md` (Synthesize Backstory section) and add it to the skills table in `/gm-assistant/CLAUDE.md`; record a memory note on the tagline-only-via-page finding.

## Dependencies & MVP

- **Setup (T001-T003)** -> **Foundational (T004)** -> stories.
- **US1 (T005-T014)** is the MVP: a reviewable, grounded backstory for a named
  NPC. Delivers value even before save exists.
- **US2 (T015-T017)** depends on US1 producing a backstory.
- **US3 (T018-T022)** is independent enrichment; can follow US1/US2 or be skipped
  without breaking them.
- **Polish (T023-T026)** last.

**Parallel opportunities**: T001/T002 together; each story's first test task
(T005, T015, T018) is `[P]` relative to other stories' work once Foundational is
done; within `opsynth.py`/`test_opsynth.py` tasks run sequentially (same files).

**Suggested MVP**: Phases 1-3 (through T014) - synthesize and present; add save
(US2) immediately after for a genuinely useful tool.
