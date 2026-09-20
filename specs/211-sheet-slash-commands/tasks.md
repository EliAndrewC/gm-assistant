# Tasks: feature 211 - sheet slash commands

Repository is **character-sheet** unless a task says gm-assistant. Design references (D1-D6) are in
[plan.md](plan.md); the sheet-side prerequisites (R1-R5) are in
`discord-slash-commands-requirements.md` at the root of that repository. Mark a task done only when
verified.

## Phase 0 - the gate (nothing else starts until this passes)

- [ ] T001 **Validate the sheet foundation shipped**, against the deployed app, by behavior:
      R1 (void spent outside the browser deducts, refuses an unaffordable or over-cap spend without
      rolling, records an identical history row), R2 (initiative outside the browser gives the
      sheet's action dice, starts the round, leaves `precepts_pool`), R3.2 (commune charges its
      activation point and refuses when it cannot be paid), R4 (a stale whole-state write is
      rejected and a tab recovers on screen), R5.1 (`GET /api/characters` carries current void,
      action dice and the per-roll cap). **Any gap STOPS the feature and is reported to the GM**
      (FR-019) - no workarounds.
- [ ] T002 Confirm with the GM who writes the command layer (this session editing the mounted tree,
      or his character-sheet session), and that no other session is working in that tree.

## Phase 1 - skill commands with void (D1, D3)

- [ ] T003 `roll_key_for_command`: keep the `SKILLS` branch, add the three-id knack allow-list with
      hyphen-to-underscore mapping. Unknown name -> None.
- [ ] T004 `run_roll_command(void=...)`: activation cost, reserve, refuse-before-rolling, one
      transaction. Assert the RNG is never called on a refusal.
- [ ] T005 Refusal messages name the number (cap, shortfall, activation point).
- [ ] T006 Post text with the void suffix (D6); dice card and history row match a sheet roll with
      the same spend.
- [ ] T007 Registration: one command per `SKILLS` entry, each with the `void` option; default set
      becomes the full set. Guard test: registered == `SKILLS` + 3 knacks + `{roll, initiative}`,
      and nothing from `COMBAT_SKILLS` is reachable.
- [ ] T008 Register to the test guild and run a real one.

## Phase 2 - the three knacks (D1, D3, D4)

- [ ] T009 `/oppose-social` and `/oppose-knowledge` end to end; label and post format.
- [ ] T010 A character without the knack gets an ephemeral refusal (D4), not a generic failure.
- [ ] T011 `/commune`: activation point charged via `requires_void_point`, refused when unaffordable,
      `void:k` checked against what remains. Comment the ordering at the point of change.
- [ ] T012 Test guild: run all three, including a deliberately unaffordable `/commune`.

## Phase 3 - `/roll` (D2)

- [ ] T013 Interaction type 4 branch; prefix-then-substring; plain skill names; skills only; never
      errors to the user.
- [ ] T014 Type-2 revalidation of a hand-typed skill; ephemeral error.

## Phase 4 - `/initiative` (D5)

- [ ] T015 Command calls the sheet's initiative + start-of-round services; post lists the action
      dice; card with `show_total: false`; history row keyed `initiative`.
- [ ] T016 Open the sheet afterwards in the test guild: dice present, unspent, spendable.

## Phase 5 - ship

- [ ] T017 Update the sheet's CLAUDE.md "Roll slash commands" section: the premise "a slash command
      has nobody to ask" now reads "pre-roll choices ride on options; post-roll choices stay on the
      sheet". Record the knack allow-list and why only three.
- [ ] T018 Deploy; register globally.
- [ ] T019 (gm-assistant) Fixtures for each new post shape - void suffix, commune, initiative -
      asserting skill/total/rank parse and that an initiative post yields no roll. Update
      `webapp/l7r/repl/rolls/CLAUDE.md`'s slash-command note.
- [ ] T020 (gm-assistant) `webapp/l7r/repl/rolls/sheet.py` says the GM API endpoints "DO NOT EXIST
      YET"; they do (`app/routes/gm_api.py`, `GET /api/rolls` and `GET /api/characters`). Verify
      against the deployed app and correct the docstring - a stale comment that says a working
      endpoint is missing will send a future session down the wrong path.
