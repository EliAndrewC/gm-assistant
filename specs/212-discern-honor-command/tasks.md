# Tasks: feature 212 - `/discern-honor`

Phase 2 depends on the GM's character-sheet session building and deploying
`discord-design/discern-honor-requirements.md`. This session writes no code in that tree. Mark a
task done only when verified.

## Phase 0 - specify, hand off, fix the rules text

- [x] T000a Spec written and reviewed by `spec-fidelity` against the GM's words (see the spec's
      Review history).
- [x] T000b Handoff document written into the character-sheet working tree, uncommitted.
      **Done 2026-09-21.**
- [x] T000c `rules/05-school_knacks.md`: `(1k1 - 0.5)` -> `(1k1 - 5)` (FR-018). Uncommitted in the
      GM's l7r working tree; he commits it. **Done 2026-09-21.**

## Phase 1 - verify the delivered sheet-side work (nothing else starts until this passes)

- [ ] T001 Run the handoff document's Part 4 against the deployed app, by behavior: open a
      conversation over the API; `/discern-honor` twice with the knack (identical ephemeral replies,
      one `asked_at`, no channel post, no roll row) and once without; write routes refuse the read
      token; re-`PUT` of the open id preserves `told` and `asked_at`; close, and the command reports
      no open conversation. A missing requirement is REPORTED, not worked around.

## Phase 2 - gm-assistant's side

**Built 2026-09-21, AHEAD of T001, against the sheet session's documented contract** (its status
block in `discord-design/discern-honor-requirements.md`): the sheet side was committed but not
deployed, and the GM starts work and leaves, so the unblocked half was built rather than waited on.
T003's fixtures are therefore a `FakeSheet` written from that contract, not recordings - T001 and
T008 are what prove the two halves actually meet, and both are still open. A read-only dry run
against the real roster and Otsuki's real record already works (three knack-holders found, Jimen's
existing line refined, the marker format as pinned).

- [x] T002 `honor.py`: the FR-006 marker in `_LINE_RE` and `line()`, `preview` / `commit` split,
      idempotent on the marker, and `rollback`. Tests first: an old-format line round-trips; every
      line the writer can produce is matched by the pattern; the same marker twice advances once; a
      new marker advances again; commit never rolls; rollback of a `first` and of a later record.
- [x] T003 `rolls/sheet.py`: `open_conversation` / `get_conversation` / `close_conversation` and
      the `gm_write_token` reader, fixtures recorded from the live endpoints in T001.
- [x] T004 `rolls/discern.py` and the `Conversation` fields: plan, resume-check, push, poll, commit.
      Test the ordering plan.md D2 settles: a resumed conversation never re-rolls a served value.
- [x] T005 Wire into `begin_conversation`, `_tick`, `end_conversation`, `abandon_conversation`.
      Every sheet failure is reported and non-fatal (FR-010) - one test per call site.
- [x] T006 The manual `discern_honor()`: in-conversation agreement with the command; outside a
      conversation, unchanged from today (pinned by a test). Abandon: rollback plus the "who was
      told what" report. Resume: announced, and `new=True` overrides it.
- [x] T007 SC-003 as a test: the serialized push payload contains no true Honor, no die, no count.
- [ ] T008 Prove it on ONE real NPC end to end with a test PC (open, ask twice, close; the Obsidian
      Portal line advanced once and carries the marker), then the whole suite.
- [x] T009 Docs: `webapp/l7r/repl/CLAUDE.md`, `webapp/l7r/repl/rolls/CLAUDE.md`, `honor.py`'s module
      docstring (the marker, and that the `- 5` is now what the rules file says too).
- [ ] T010 `make done` from `webapp/`, then the stop-work procedure.
