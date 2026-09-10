# Tasks: Interrogation rolls grouped by line of questioning

**Input**: Design documents from `specs/206-interrogation-lines/` - plan.md, spec.md,
research.md, data-model.md, quickstart.md.

**Tests**: REQUIRED - constitution X mandates red-green TDD for new behavior, and the plan names
`webapp/tests/test_rolls_interrogation.py` as the reference artifact (constitution VI). Every
story's tests are written RED before its implementation.

**Organization**: by user story from spec.md. All paths are relative to `webapp/`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies)
- **[Story]**: US1..US5 from spec.md

## Reference-artifact rule (constitution VI)

The reference artifact is `tests/test_rolls_interrogation.py`. Each story lands there first
(red, then green); the sweep is `make done` from `webapp/`, run ONCE in Phase 8. Story phases do
not each re-run the whole suite - they run the reference module and the one existing module whose
assertions they could touch.

---

## Phase 1: Setup

- [ ] T001 Sync the clone (`git -C /gm-assistant/.clones/discord pull origin main`) and confirm
      the baseline in research.md R6 still describes `HEAD` (no rolls-package commits landed since
      `f2a0c885`); if any did, retake the baseline the same way and update R6.
- [ ] T002 Create `tests/test_rolls_interrogation.py` with the shared `roll()` / `conversation()`
      helpers copied from `tests/test_rolls_annotate.py` (module docstring: what the leak is, in
      one paragraph) and the GM's two example lines as the first two tests, both RED:
      `interrogation (grilling): 37@2 Jimen / 24@1 Moriko - what Fumitake ordered his escorts to do`
      and `interrogation: 25@2 Jimen - what Fumitake thinks of Tsuruchi`.

## Phase 2: Foundational

- [ ] T003 Add `line: int | None = None` and `grilling: bool = False` to `Roll` in
      `l7r/repl/rolls/models.py`, with field comments saying lines are DERIVED (research R2) and
      that `opposed_total` / bonuses are ignored for interrogation. Run
      `pytest -q -n auto tests/test_rolls_models.py tests/test_rolls_annotate.py` - unchanged.
- [ ] T004 Add `INTERROGATION = 'interrogation'`, `is_interrogation(roll)`, and
      `lines_of_questioning(rolls) -> list[list[Roll]]` (groups attributed, non-discarded
      interrogation rolls with a `line`; each group highest-total-first, ties in collection order;
      groups in order of first roll) to `l7r/repl/rolls/rules.py`, beside `EXEMPT_FROM_ANNOTATION`
      and `CONTESTED_PAIRS`. Tests for the grouping and ordering in the reference module (RED
      first): two rollers one line, one roller two lines, tie order, a discarded roll excluded.

## Phase 3: User Story 1 - written alone, exact, with rank (P1)

**Goal**: `interrogation: 37@2 Jimen - <note>`; exact total; no opposing side; no bonus.

**Independent test**: render one annotated interrogation roll; assert the line and the absence
of any second total, winner or margin.

- [ ] T005 [US1] RED tests in `tests/test_rolls_interrogation.py`: exact total (37 not 35);
      `@rank` present when `rank` is set and absent when `None`; a roll carrying `opposed_total`
      and bonuses renders identically to one without them (research R5, FR-002, FR-003).
- [ ] T006 [US1] Implement `render_interrogation(rolls, *, bare=False)` in
      `l7r/repl/rolls/rules.py` per data-model.md: `interrogation[ (grilling)]: ` + ` / `-joined
      `<total>[@<rank>] <personal name>` entries + ` - <note>` unless bare. Docstring carries the
      leak reasoning and the "note/grilling read from the first roll" cost (R2). GREEN on T005.
- [ ] T007 [US1] Route interrogation rolls through it in `render_lines`
      (`l7r/repl/rolls/rules.py`): in the annotated pass, the first roll of a line emits the whole
      line, later rolls of that line emit nothing; a roll with `line is None` under
      `include_unannotated=True` emits a bare line. RED test first in the reference module:
      `render_lines` on a conversation with one Etiquette, one open Law and one interrogation roll
      yields three lines in the right order with the right shapes. Then run
      `pytest -q -n auto tests/test_rolls_rules.py tests/test_rolls_watch.py` - unchanged.

## Phase 4: User Story 2 - rolls on one line share a line (P1)

**Goal**: the join-or-new menu; one written line per line of questioning.

**Independent test**: drive `annotate()` with scripted answers for three interrogation rolls -
two joined, one new - and assert two written lines.

- [ ] T008 [US2] RED menu tests in `tests/test_rolls_interrogation.py` using a scripted `ask`:
      (a) first interrogation roll gets the `[n/d, blank to finish]` prompt and NO
      `Lines of questioning so far` listing; (b) second roll sees the listing with `(grilling)`
      where set and joins by number, and is NOT asked grilling or the note; (c) `n` starts a new
      line and asks grilling then note; (d) the `o/c/d/ob` prompt text never appears for an
      interrogation roll; (e) the staged echo shows the whole line including rolls already on it.
- [ ] T009 [US2] Extend `Decision` in `l7r/repl/rolls/annotate.py` with `line`, `grilling`,
      `rank` (data-model.md) and make `_apply` set exactly `note`, `line`, `grilling`, `rank` for
      an interrogation decision - never `opposed_total` or bonuses.
- [ ] T010 [US2] Add `_existing_lines(conv, staged)` (conversation rolls overlaid with staged
      decisions, then `rules.lines_of_questioning`) and `_interrogate(ask, roll, lines, next_id)`
      to `l7r/repl/rolls/annotate.py`: the listing + `Join which line?` prompt when lines exist,
      the `[n/d, blank to finish]` prompt when none; re-ask on an unusable answer; returns a
      `Decision`, a discard, or `None` for blank. Branch into it from `annotate()` BEFORE the kind
      prompt when `rules.is_interrogation(roll)`, with a comment at the branch saying why this
      skill never sees o/c/ob (FR-002, FR-003). Staged echo via `rules.render_interrogation` over
      the line's existing rolls plus this one. GREEN on T008.
- [ ] T011 [US2] Run `pytest -q -n auto tests/test_rolls_annotate.py tests/test_rolls_followup.py`
      - every existing menu assertion unchanged (SC-005).

## Phase 5: User Story 3 - grilling, per line (P2)

**Goal**: `Grilling? [y/N]` once per new line; `(grilling)` on the line; inherited on join.

- [ ] T012 [US3] RED tests in `tests/test_rolls_interrogation.py`: `y` -> `(grilling)`; blank
      and `n` -> no parenthetical; a roll joining a grilling line inherits `grilling=True` without
      being asked; `yes` / `Y` accepted.
- [ ] T013 [US3] Implement the `Grilling? [y/N]` prompt in `_interrogate`
      (`l7r/repl/rolls/annotate.py`) - a small `_yes_no(ask, question, default=False)` helper that
      re-asks on anything but blank/y/yes/n/no. GREEN on T012.

## Phase 6: User Story 4 - a hand-typed roll gets its rank from the GM (P2)

**Goal**: rank prompt only when `roll.rank is None`, only for interrogation; blank = no `@`.

- [ ] T014 [US4] RED tests in `tests/test_rolls_interrogation.py`: recorded rank -> no prompt
      and written as recorded; no rank -> prompt `<name>'s interrogation rank? [none]` appears
      BEFORE the line questions; `2` -> `37@2`; blank -> `37`; `x` re-asks; a Law roll with no
      rank is never asked (US4 scenario 4).
- [ ] T015 [US4] Add `_optional_number(ask, question) -> int | None` beside `_number` in
      `l7r/repl/rolls/annotate.py` and call it from `_interrogate` when `roll.rank is None`;
      copy a recorded rank into `Decision.rank` otherwise. GREEN on T014.

## Phase 7: User Story 5 - everything else about annotation still holds (P2)

**Goal**: held-until-annotated, discard, Ctrl-C, exit path, Etiquette all unchanged.

- [ ] T016 [US5] RED tests in `tests/test_rolls_interrogation.py`: `end_conversation()` raises
      naming an unannotated interrogation roll; Ctrl-C after staging two interrogation decisions
      leaves both rolls with `line is None` and `note == ''`; `d` at the interrogation prompt
      discards and the line it would have joined is written without it; a line whose only roll
      is discarded is absent from the record; the exit path (`include_unannotated=True`) writes
      `interrogation: 37@2 Jimen` bare per roll with no grouping; a re-annotation moves a roll
      between lines and the emptied line disappears (spec edge case).
- [ ] T017 [US5] Fix whatever T016 exposes in `l7r/repl/rolls/annotate.py` /
      `l7r/repl/rolls/rules.py` (expected: nothing beyond T010's `next_id` allocation ignoring
      discarded rolls' ids). GREEN on T016. Run
      `pytest -q -n auto tests/test_rolls_conversation.py` - unchanged.

## Phase 8: Polish, sweep, hand-check

- [ ] T018 Update `l7r/repl/rolls/CLAUDE.md`: add the interrogation line to the "What a written
      line looks like" block; a paragraph under the annotation section on WHY interrogation is
      alone/exact/`@rank`/grouped, the two conditional bonuses and which one is secret, lines
      derived from rolls (R2), and the o/c/ob prompt never being offered; update the `annotate.py`
      row. Update `rules.py`'s module docstring the same way (one paragraph, dated).
- [ ] T019 Sweep: `( cd webapp && make done > <scratch>/gate.log 2>&1 )` and read the tail -
      ruff, format, mypy --strict, hook-guard suites, pytest, 100% coverage on `l7r`. Compare
      against research R6: zero new failures. Fix everything it lists together, re-run once.
- [ ] T020 Hand-check per quickstart.md at the REPL (`./scripts/repl.py`, scratch channel):
      three typed interrogation rolls, `annotate()` with join / new / grilling / rank answers,
      `conversation_status()` shows the two lines; confirm the `xky` Sincerity roll is never
      offered. Record the transcript's two written lines in quickstart.md if they differ from
      the expected ones there.
- [ ] T021 Stop-work: commit in the clone with a message that states the three rulings and their
      why; `scripts/sync-with-main.sh done`; confirm the GitHub push line.

---

## Dependencies

- Phase 1 -> Phase 2 -> Phase 3 (US1) -> Phase 4 (US2) -> Phases 5, 6 (US3, US4: independent of
  each other, both need T010's `_interrogate`) -> Phase 7 (US5) -> Phase 8.
- US1 is the MVP: after Phase 3, an interrogation roll annotated by any path renders without the
  leak. US2 makes the menu match the GM's request; US3/US4 are the two per-line details; US5 is
  the regression story.

## Parallel opportunities

- T003 and T004 touch different files and can be written in one turn.
- T012/T013 (grilling) and T014/T015 (rank) are independent once T010 exists; write both RED
  sets in one turn, both implementations in the next.
- T018 (docs) can be written alongside T016/T017.

## Implementation strategy

Reference module first, always: every RED test goes into `tests/test_rolls_interrogation.py`
and is run with `pytest -q -n auto tests/test_rolls_interrogation.py` (the whole file, never
`-k`). Existing modules are run whole after each phase that could touch their assertions. The
full gate runs exactly once, at T019, then the REPL hand-check, then the push.
