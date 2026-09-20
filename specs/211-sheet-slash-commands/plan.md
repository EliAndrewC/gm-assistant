# Implementation Plan: specify the commands, hand them off, verify, and do the capture side

**Feature**: `specs/211-sheet-slash-commands` | **Date**: 2026-09-20 | **Spec**: [spec.md](spec.md)

**THIS SESSION WRITES NO CODE IN THE CHARACTER-SHEET TREE.** The one file it writes there is the
handoff document, left uncommitted for that repository's session to commit (FR-020). The GM reassigned the command layer to the character-sheet
repository's own session (message 3), and forbade this session from editing that tree. So the shape
of the feature is: specify -> hand off -> the GM's other session builds and deploys -> verify by
behavior -> do gm-assistant's own capture-side work.

The handoff document is `discord-slash-commands-requirements.md` at the root of
<https://github.com/EliAndrewC/character-sheet>, written into that working tree (uncommitted - git
writes there are forbidden). It carries the server-side foundation (Part 1), the full command layer
(Part 2), the non-blocking API addition (Part 3), the general audit the GM asked for (Part 4), what
is deliberately out of scope (Part 5), the verification contract (Part 6), and the open questions
(Part 7).

## Why the plan is this thin now

Earlier drafts of this file carried the design for the commands themselves, and before that for the
server-side void spend, the server-side initiative, and the open-tab overwrite fix. All of it has
moved into the handoff document - the first three because they are the sheet app's rules and the
sheet app's bug, the command layer because the GM decided its owning repository should write it.

Nothing measured was lost: the file-and-line evidence is that document's Part 0, and the command
design is its Part 2. What is left here is the part that is genuinely gm-assistant's.

## What is measured and where it came from

All at character-sheet commit `6c4dd9c` (2026-09-20), read through the bind mount at
`/host-l7r-repo/character-sheet`, plus live calls against the deployed app.

| finding | consequence |
|---|---|
| void spending, initiative action dice, Commune's activation cost and the new-round reset are BROWSER code; the server has never deducted a void point or built an action die | handoff Part 0 F1, requirements R1-R3 |
| `POST /characters/{id}/track` takes the tab's whole local state, so an open sheet page silently overwrites anything another writer wrote | handoff Part 0 F2, requirement R4, audit A2 |
| `game_data.SKILLS` holds exactly the 18 non-combat skills; combat is a separate `COMBAT_SKILLS`; iaijutsu is a knack; the two are disjoint | handoff C1.1 - combat is excluded by construction |
| `dice.py` already sets `requires_void_point` for Commune, and `SCHOOL_RING_KNACK_IDS` already pins its ring | handoff R3.2, C3.4; spec Decision 3 |
| `GET /api/rolls` and `GET /api/characters` are LIVE (200 roll rows and the full roster returned for a valid token; 401 without) | handoff R6.1 measures the actual gap: no current state in the character payload. Also the defect fixed below |

## The one defect this feature fixed in passing (Principle XIV)

`webapp/l7r/repl/rolls/sheet.py` and `webapp/l7r/repl/rolls/CLAUDE.md` both said the character-sheet
GM API "DOES NOT EXIST YET". It does, and the client works against it - `characters()` returned the
roster and `recorded_rolls()` returned 200 rows for a 120-day window. A stale "not built yet" is
worse than silence: it sends the next session looking for a fallback it does not need. Corrected
with the measurement recorded at the point of change.

## Design - gm-assistant's own side

### D1. The post formats are a contract, and this side owns half of it

The handoff document's C6 asks that any spend annotation stay inside parentheses, and that the
initiative line not put a bare number immediately before a skill word. Both exist because of how
this repository's parser works:

- `webapp/l7r/repl/rolls/parse.py` `_BREAKDOWN` strips `(...)` spans before matching, so
  `(1 void)` cannot be read as a second roll.
- `_CLUSTER` matches a number followed by a skill word, so `action dice: 2, 5, 7` has nothing to
  match on - provided the wording does not drift into something like `7 initiative`.

Neither property is guaranteed by the other repository's tests. This side pins them with fixtures
of REAL posts once the commands are live (T005). Until then the contract is prose in two documents,
which is exactly the kind of rule this project does not trust.

### D2. Verification is behavioral, and a gap stops the feature

Task 1 runs the handoff document's Part 6 checklist against the deployed app. The response to a
missing blocking requirement is to report it, not to compensate for it (FR-019). The non-blocking
items - the API addition and the audit write-up - are reported and never block.

## Constitution check

- **XVI (literal thing)**: no exceptions carved. FR-020 records the GM's instruction not to edit
  that tree; the knack allow-list is exactly his three; Otherworldliness and the other knacks are
  deferred by his word and recorded as such.
- **XIV (fix defects where you find them)**: the stale API docstring was fixed in this work, with
  its measurement. The two character-sheet findings are not deferred - they are specified to the
  app that owns them, which is the only place either can be fixed correctly.
- **X / no second implementation**: this feature contains no dice, void or initiative rule at all.
- **A guideline in prose is not a rule**: D1 is the live case - the post-format contract becomes
  fixtures the moment there are real posts to pin.

## Rollout

1. Handoff document written and in place. **Done.**
2. The GM's character-sheet session implements Parts 1, 2 and 4 and deploys. Not this feature's
   work; nothing here proceeds until it does.
3. T001 verification against the deployed app.
4. gm-assistant capture fixtures for the new post shapes.

## Open items for the GM

None blocking. Both of the questions this feature raised were answered in message 3: Commune's ring
(School Ring) and who writes the command layer (the character-sheet session).

One thing awaits the GM rather than blocking anyone: this session drafted the matching edit to
`rules/05-school_knacks.md` in `EliAndrewC/l7r`, because he said he had been meaning to make it and
had not had time. It is an uncommitted working-tree change there, alongside unrelated uncommitted
edits of his own, and whether to keep it is his call. The project's standing rule is that a rule
which reads wrong is FLAGGED rather than fixed; this was a case where he had already dictated the
replacement text, but it is still his file.
