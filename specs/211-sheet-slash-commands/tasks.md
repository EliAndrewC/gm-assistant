# Tasks: feature 211 - sheet slash commands

Repository is **character-sheet** unless a task says gm-assistant. Design references (D1-D7) are in
[plan.md](plan.md). Mark a task done only when verified.

## Phase 0 - research (read before writing; the browser JS is the specification)

- [ ] T001 Read `_dice_js.html` `executeRoll` void branch (~l.1970-2090) end to end: what a void
      point gives a SKILL roll, 10k10 overflow, whether worldliness can fund it. Record in the
      design doc.
- [ ] T002 Read `deductVoidPoints` and find where each consequence persists (Ide temp VP, Yogo
      light wounds, Matsu banked bonuses -> which column / `adventure_state` key).
- [ ] T003 Enumerate every key `resetMantisRound()` and `setActionDice()` touch, and where each
      persists server-side.
- [ ] T004 Read `POST /characters/{id}/track` (`routes/characters.py` ~l.1969) and every `save()`
      caller: confirm the whole-state overwrite and list the fields involved.
- [ ] T005 Confirm how the sheet stores combat skills (attack/parry apart from `SKILLS`; iaijutsu
      as a knack) so the registration guard test can assert none of them is ever registered.

## Phase 1 - tracking revision (D5) - ships alone

- [ ] T006 Test first: two stale writers, second gets 409 + current state.
- [ ] T007 `Character.tracking_rev` + migration; `/track` checks and bumps it.
- [ ] T008 Tab handles 409: adopt server state, show a notice. Clicktest.

## Phase 2 - void on skill rolls (D3)

- [ ] T009 Extract `void_spend_config()` from `pages.py` into `services/void_spend.py`; page calls
      it; no behavior change (existing tests stay green).
- [ ] T010 `allocate()` mirror + the JS test cases asserted verbatim in Python.
- [ ] T011 `apply_spend()` with the school consequences from T002; one test per consequence.
- [ ] T012 `execute_roll(void_spent=)`; payload carries `void_spent`; dice card renders it as it
      does for a sheet roll (compare PNG payload fields, not pixels).
- [ ] T013 `run_roll_command`: cap refusal, shortfall refusal (nothing rolled, nothing written -
      assert the RNG was never called), success path in one transaction, rev bumped.
- [ ] T014 Parity test (SC-004): same character + seeded dice through the sheet's recorded payload
      shape and through the command -> same formula, deduction, history row.
- [ ] T015 Registration: every skill + `void` option; default set becomes all; guard test that
      registered names == `SKILLS` + `{roll, initiative}`. Register to the test guild and try it.

## Phase 3 - `/roll` (D2)

- [ ] T016 Interaction type 4 branch; prefix-then-substring match; plain skill names; never errors.
- [ ] T017 Type-2 revalidation of a hand-typed skill; ephemeral error.

## Phase 4 - `/initiative` (D4)

- [ ] T018 Extract the browser's action-dice block into `roll_math.js` `initiativeActionDice` (pure
      move) with a case table: plain, Hiruma 4, Shinjo 4, Kakita, Togashi, Mantis 4, Matsu 10 dice.
- [ ] T019 `services/initiative.py` mirror; same case table; `keep_lowest` in `roll_dice`.
- [ ] T020 `start_round()` per T003; test that `precepts_pool` survives and spent dice do not.
- [ ] T021 Command + post text + `show_total: false` card + history row keyed `initiative`.
- [ ] T022 Open the sheet after `/initiative` in the test guild: dice present, spendable.

## Phase 5 - ship

- [ ] T023 Update the sheet's CLAUDE.md "Roll slash commands" section: the premise "a slash command
      has nobody to ask" now reads "pre-roll choices ride on options; post-roll choices stay on the
      sheet"; record D5 and its declined alternatives.
- [ ] T024 Deploy; register globally.
- [ ] T025 (gm-assistant) Save one real post per new shape as fixtures in
      `webapp/l7r/repl/rolls/`; assert parse results, and that an initiative post yields no roll.
      Update `webapp/l7r/repl/rolls/CLAUDE.md`'s slash-command note.
