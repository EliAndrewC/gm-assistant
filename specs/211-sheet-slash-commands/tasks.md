# Tasks: feature 211 - sheet slash commands

Everything in Phase 1 depends on the GM's character-sheet session finishing and deploying the
handoff document (`discord-slash-commands-requirements.md`, root of the character-sheet
repository). This session writes **no command code** (FR-020). Mark a task done only when verified.

## Phase 0 - specify and hand off

- [x] T000 Write the handoff document into the character-sheet working tree: the server-side
      foundation, the full command layer, the non-blocking API addition, the general audit, the
      out-of-scope list, the verification contract and the open questions. Uncommitted there; the
      GM commits. **Done 2026-09-20.**

## Phase 1 - verify the delivered work (nothing else starts until this passes)

- [ ] T001 Run the handoff document's **Part 6** checklist against the deployed app, by behavior:
      void spent through a command really deducts and refuses cleanly; `/initiative` gives the
      sheet's own action dice, starts the round and leaves `precepts_pool`; `/commune` charges its
      activation point and refuses when unaffordable; `/roll` completes and revalidates; the
      registered set matches C1 with nothing from `COMBAT_SKILLS` reachable; a stale whole-state
      write is rejected and the tab recovers; the posted formats match C6.
      **A missing blocking requirement STOPS the feature and is reported to the GM** (FR-019) - no
      workarounds, and no editing that tree to fix it (FR-020).
- [ ] T002 Report the non-blocking items rather than acting on them: whether `GET /api/characters`
      now carries current void, action dice and the per-roll cap (R6.1), and what the audit (Part
      4) turned up.

## Phase 2 - gm-assistant's capture side (User Story 6, FR-014)

- [ ] T003 Collect one REAL post of each new shape from the game channels: a skill roll with a void
      suffix, a `/commune` roll, an `/initiative` post.
- [ ] T004 Save them as fixtures under `webapp/l7r/repl/rolls/`, alongside the existing
      slash-command fixtures.
- [ ] T005 Assert: each roll post parses to the right skill, total and rank; the void annotation is
      never read as a second roll (`_BREAKDOWN`); an initiative post yields NO roll (`_CLUSTER`
      finds nothing). These are the tests that turn the handoff document's C6 from prose into a
      pinned contract.
- [ ] T006 Update `webapp/l7r/repl/rolls/CLAUDE.md`'s slash-command note for the new formats and
      the command set that now exists.
- [ ] T007 `make done` from `webapp/`, then the stop-work procedure.
