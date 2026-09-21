# Implementation Plan: specify, hand off, then build the conversation side

**Feature**: `specs/212-discern-honor-command` | **Date**: 2026-09-21 | **Spec**: [spec.md](spec.md)

Same shape as feature 211: specify -> hand off -> the GM's character-sheet session builds and
deploys -> verify by behavior -> build gm-assistant's side against the live endpoints.

The handoff document is `discord-design/discern-honor-requirements.md` in
<https://github.com/EliAndrewC/character-sheet>, written into that working tree uncommitted. It
carries the measured findings (Part 0), the requirements D1-D6 (Part 1), what gm-assistant does with
them (Part 2), the out-of-scope list (Part 3), the verification contract (Part 4) and two open
questions.

## What is measured and where it came from

gm-assistant at `4e1d0388`, character-sheet at `b52247d`, both 2026-09-21.

| finding | consequence |
|---|---|
| `honor.advance()` increments on every call; there is no notion of "this conversation" anywhere in `honor.py` | the double-count the GM described would be live the moment a command existed; a second manual call inside one open conversation double counts today (FR-005, FR-007) |
| `discern_honor()` computes and uploads in one step | FR-002 needs the two split: a pure preview, and a commit |
| `models.Conversation` has no id and lives only in memory | FR-011's resume cannot be local; the sheet's unclosed conversation is the only state that survives a REPL crash, hence `npc_ref` |
| `_tick` already collects, announces and debounces writes to the NPC's record every ~20 s | FR-004's commit-on-sight rides the existing tick; no second thread, no second write path |
| `honor.knack_rank` scrapes the PC's public sheet HTML (24 h cache); `sheet.characters()` already returns knack ranks over the API | FR-001 uses the API. The scraper stays for the no-conversation manual call and for PCs the API does not know |
| the sheet's GM API is read-only and says so | handoff D1 asks for a second secret; this side stores it as `[character_sheet] gm_write_token` beside `roll_query_token` |
| existing Obsidian Portal records use `- Jimen (rank 2): told 4.5 after 1 conversation` | FR-006's marker is an OPTIONAL trailing group in `_LINE_RE`; `honor.py`'s "nothing older is read" ruling was about prose notes, not about this block |

## Design - gm-assistant's side

### D1. `honor.py`: split preview from commit, and make commit idempotent

- `Record` gains `last: str = ''` and `was: float | None` - the marker, in the exact format the
  spec's FR-006 pins (` [c-20260921-7f3a, was 4.5]` / ` [c-20260921-7f3a, first]`); parsed by an
  optional group, so old lines round-trip unchanged until they next advance. `rollback(records,
  marker)` is the inverse FR-009 needs: drop `first` records, restore `was` and decrement the rest.
  A manual call outside a conversation writes no marker - it behaves as today.
- `preview(gm_info, pc, rank, die, marker) -> Record`: what the record WOULD be. If the stored
  record's `last` already equals `marker`, it returns the stored record unchanged - this single
  branch is the idempotency rule (FR-005), and every path goes through it.
- `commit(...)`: re-reads the NPC's notes, applies `preview` with the ALREADY-DECIDED told value,
  writes. Re-reading matters: the watcher's own debounced write touches the same field, and a
  commit built on a stale copy would drop its lines.
- The d10 for a first read is rolled once, at preview time, and the resulting told value is what
  travels; commit never rolls.

### D2. `rolls/discern.py` (new): the conversation glue

Pure functions plus injected boundaries, the pattern `conversation.py` and `discern_honor()` already
use: `plan_conversation(characters, gm_info, group) -> {character_id: Record}`, `push`, `poll_asked`,
`close`. `Conversation` gains `conversation_id` and `discern: dict[int, Record]` plus the set already
committed. `begin_conversation` calls plan + resume-check + push; `_tick` calls poll + commit;
`end_conversation` flushes and closes; `abandon_conversation` rolls back, reports who was told
what, and closes. A resume is announced at open, and `begin_conversation(..., new=True)` forces a
fresh conversation over an unclosed one (FR-011).

**Ordering, settled here rather than discovered at the gate**: at open, resume-check BEFORE plan
(a resumed conversation must not re-roll a first read a player has seen - the sheet's copy of
`told` wins for any entry it already holds); in `_tick`, commit BEFORE the roll-line write so both
land in one Obsidian Portal update where the debounce allows.

### D3. `rolls/sheet.py`: three write-side calls

`open_conversation`, `get_conversation`, `close_conversation`, returning the same
`SheetResult`-style "unavailable, and why" that the read calls return, so FR-010 is the default
behavior rather than a try/except at each call site.

### D4. The manual call

Signature unchanged. Conversation open against this NPC: serve from `conv.discern`, commit, and
mark the entry asked on the sheet so the player's command and the GM's screen cannot disagree. No
conversation: exactly today's behavior, one call = one conversation. (A same-calendar-day
suppression was drafted here and struck by the fidelity review: the GM's semantic is a conversation,
not a time window.)

## Constitution check

- **XVI (literal thing)**: the GM's semantic - same conversation, same answer, no increment - is
  FR-005 with no exception carved. `spec-fidelity` struck two departures the author could not see
  (a same-day rule for the manual call; abandon not discarding) - see the spec's Review history.
- **XII / record the why**: each Decision in the spec names the alternatives that were priced.
- **XIV**: the rules-text typo, flagged 2026-08-27 and left, is fixed in this feature at the GM's
  word (FR-018), and the sheet's copy of it is in the handoff (D6).
- **X**: all of D1-D4 is pure logic with injected boundaries; 100% coverage applies.
- **A guideline in prose is not a rule**: SC-002 (advance exactly once) and SC-003 (no true Honor
  leaves) both become tests - the second as an assertion over the serialized push payload.

## Rollout

1. Spec, fidelity review, handoff document, rules-text fix. **This session.**
2. The GM's character-sheet session builds D1-D6 and deploys.
3. T001 verification against the deployed app.
4. gm-assistant's side, T002 onward.

## Open items for the GM

None blocking. Worth a glance when convenient: spec Decisions 2 (the reply does not name the NPC)
and 3 (each `begin` is a new conversation). Each is a one-line change if he would rather have it
the other way.
