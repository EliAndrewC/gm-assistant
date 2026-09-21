# Feature Specification: `/discern-honor` from Discord - one answer per conversation, history on Obsidian Portal

**Feature Directory**: `specs/212-discern-honor-command`

**Created**: 2026-09-21

**Status**: Specified and handed off. Not implemented. The gm-assistant side is blocked, by design,
until the character-sheet side ships (see "Who builds what").

**Input**: GM request 2026-09-21, two messages, verbatim in [gm-request.md](gm-request.md). Message
2 approves a shape the session proposed; that proposal is summarized in the same file, because it is
what "yes, please do that" refers to.

## Why

Discern Honor is the one school knack the Discord integration never reached. It is also the odd one
out: it has no dice roll the player makes (`rules/05-school_knacks.md`, **Ring:** N/A). The player
talks to somebody, and the GM tells them a number. Today that number comes from the REPL's
`discern_honor("Otsuki", "Jimen")`, which the GM types by hand mid-scene and then relays aloud.

The GM wants the player to be able to ask from Discord and be told their current read on the
character's Honor directly. Three things stand between today and that:

1. **The true Honor is on Obsidian Portal**, in the NPC's GM-only notes, and only gm-assistant can
   read Obsidian Portal. The character-sheet bot owns the slash commands and cannot.
2. **Discord cannot say who is being talked to, or where one conversation ends.** The REPL already
   holds both facts: `begin_conversation("Otsuki")` ... `end_conversation()` (feature 201).
3. **Nothing today stops a double count.** Every call to `honor.advance()` is a new conversation, so
   a second ask in the same scene moves the player closer to the truth. The GM's words: *"if
   somebody slips up and accidentally runs discern honor twice in the same conversation, then it
   will return the same result rather than incrementing them closer to what the actual number is"*.

## The shape, in one paragraph

When the GM opens a conversation, gm-assistant works out - privately - what each PC who has the
knack would be told in THIS conversation, and hands the sheet app only those told values. The
`/discern-honor` command is then a lookup: it answers at once, to that player only, and the same
conversation always gives the same number because nothing is computed at ask time. gm-assistant
notices which PCs actually asked and records only those on Obsidian Portal. Values nobody asked for
are thrown away; no player ever saw them.

## Who builds what

**The command and the sheet-side storage are built in
<https://github.com/EliAndrewC/character-sheet> by that repository's own session**, exactly as in
feature 211 (GM 2026-09-20: *"I do not want you to edit that tree directly"*). This session writes
one file there, uncommitted: `discord-design/discern-honor-requirements.md`, next to the 211
document that repository moved into `discord-design/`.

**gm-assistant builds**: the conversation-aware knack logic, the precompute and push, the commit to
Obsidian Portal, and the REPL's own idempotency. That work cannot be verified until the sheet's
endpoints exist, so it follows the sheet-side ship, the way 211's capture side does.

**The rules text fix is done in this feature** (message 2), see FR-018.

## User Scenarios & Testing

### User Story 1 - a player asks, and is told their read (P1)

The GM has opened a conversation with an NPC. A player whose character has Discern Honor runs
`/discern-honor` in the game channel and is privately told a number.

1. **Given** an open conversation and a PC with the knack who has never used it on this NPC,
   **When** the player runs `/discern-honor`, **Then** they receive, visible only to them, the first
   read the rule gives: the true Honor adjusted by the hidden d10, with the NPC's Unconventional or
   Virtue applied.
2. **Given** the same PC in a LATER conversation with the same NPC, **When** they run the command,
   **Then** the number is the previous told value moved 0.X toward the truth, X being their knack
   rank, and never past the truth.
3. **Given** a PC whose told value already equals the truth, **When** they ask in any later
   conversation, **Then** they are told that same value, and nothing tells them it is exact.
4. **Given** any of the above, **Then** the reply contains no true Honor, no d10, no count of
   conversations, and no "locked in".

### User Story 2 - asking twice in one conversation changes nothing (P1)

This is the GM's explicit semantic, and the reason the design precomputes.

1. **Given** a player who has already run `/discern-honor` in this conversation, **When** they run
   it again - once or twenty times - **Then** every reply carries the same number as the first.
2. **Given** those repeats, **When** the conversation ends, **Then** the Obsidian Portal record
   shows exactly ONE more conversation than before it began, not one per ask.
3. **Given** the GM calls the REPL's `discern_honor(npc, pc)` by hand for a PC during an open
   conversation with that NPC - before or after the player used the command - **Then** the GM sees
   the same value the player was or will be told, and the record still advances once.
4. **Given** the REPL is restarted mid-scene and the GM opens the conversation again, **Then** it is
   the same conversation: PCs who already asked get the number they were already given, and nobody
   is double counted (FR-011).

### User Story 3 - the history is kept, where it already is (P1)

1. **Given** a PC asked during a conversation, **Then** the NPC's GM-only notes on Obsidian Portal
   carry that PC's line in the existing `Discern Honor:` block, updated: told value, conversation
   count, and which conversation it was last advanced in.
2. **Given** a PC with the knack was present but never asked, **Then** their record is untouched -
   no line created, no count advanced, and the d10 rolled for them is forgotten.
3. **Given** records written before this feature (no conversation marker), **Then** they are read
   as they stand and gain the marker the next time they advance. The GM's live records - Otsuki's -
   are not orphaned.
4. **Given** the GM abandons the conversation (`abandon_conversation()`, the "wrong NPC" exit),
   **Then** anything not yet recorded is discarded. See Decision 6 for what has already been seen.

### User Story 4 - the command when it cannot answer (P2)

1. **Given** no conversation is open, **Then** the player is told, privately, that no conversation
   is open and to ask the GM.
2. **Given** the player's character does not have Discern Honor, **Then** they are told so,
   privately, whether or not a conversation is open.
3. **Given** a conversation is open but gm-assistant could not produce a value for this PC (the NPC
   has no `Honor:` line; the push failed), **Then** the player gets the same "ask the GM" reply, and
   the GM was told why at `begin_conversation` time, in the REPL.
4. **Given** the GM's REPL died and nobody closed the conversation, **Then** the sheet stops serving
   it after the expiry window (FR-016) rather than answering for an NPC who left hours ago.

### Edge cases

- **A player with two characters**: resolved the way 211's commands resolve the invoking character;
  this feature adds no second rule.
- **Rank changes mid-campaign**: the rank used is the rank at the time the conversation opens, read
  from the sheet's API. The stored rank on the Obsidian Portal line is updated to match, as
  `advance()` already does.
- **A PC acquires the knack mid-conversation**: not served until the next conversation. Accepted.
- **An NPC with no `Honor:` line**: `begin_conversation` still opens (roll capture must not be held
  hostage to this), reports that Discern Honor is unavailable for this NPC, and pushes no values.
- **The sheet app is unreachable at `begin_conversation`**: same - the conversation opens, the GM is
  told the command will not answer, and the manual REPL call still works.

## Requirements

### gm-assistant

- **FR-001** On `begin_conversation`, for every PC in the conversation's gaming group whose sheet
  shows Discern Honor at rank 1 or more, gm-assistant MUST compute the value that PC would be told
  in this conversation, using the existing rule code (`first_guess` / `refine`, with `perceived`).
  PCs and ranks come from the sheet's `GET /api/characters`, not from scraping sheet pages.
- **FR-002** The computation MUST be pure preview: nothing is written to Obsidian Portal at open.
- **FR-003** gm-assistant MUST push to the sheet app only a conversation id and, per character, the
  told value. The true Honor, the d10, the conversation count and the locked state MUST NOT leave
  gm-assistant. By default the NPC's name is not sent either (Decision 2).
- **FR-004** The conversation watcher MUST learn from the sheet app which PCs have asked, and for
  each one commit that PC's advanced record to the NPC's GM-only notes. The commit happens when the
  ask is SEEN (through the watcher's existing debounced write), not only at `end_conversation`, so a
  crash after a player was told a number cannot lose the fact that they were told it.
- **FR-005** A commit MUST be idempotent on the conversation id: a record already marked with this
  conversation is never advanced again by it, whichever path gets there first.
- **FR-006** The record line gains a marker naming the conversation it was last advanced in. Lines
  without a marker MUST still parse (User Story 3.3).
- **FR-007** The manual `discern_honor(npc, pc)` call MUST obey the same rule. With a conversation
  open against that NPC it returns the precomputed value for that PC, commits it once, and marks it
  used so the player's command agrees. With NO conversation open it behaves as today, except that a
  repeat for the same PC and NPC on the same calendar day returns the stored value unchanged unless
  the GM passes an explicit "this really is another conversation" argument (Decision 4).
- **FR-008** On `end_conversation`, asked-but-uncommitted records are flushed, the sheet's
  conversation is closed, and unasked values are discarded.
- **FR-009** On `abandon_conversation`, the sheet's conversation is closed and nothing further is
  committed.
- **FR-010** Every failure of the sheet push or poll is reported to the GM in the REPL and MUST NOT
  stop the conversation opening, the roll capture, or the manual call.
- **FR-011** Opening a conversation against an NPC for whom the sheet app still holds an unclosed
  conversation RESUMES it: same id, same served values, no recompute for PCs already present. A
  normal close removes the sheet's conversation, so this fires only after a crash. Opening after a
  normal close is a NEW conversation (Decision 3).

### character-sheet (specified in the handoff document; listed here so the whole is reviewable)

- **FR-012** Authenticated write endpoints for gm-assistant to open (or replace), read and close a
  conversation. The GM API is read-only today and its docstring promises so; the write endpoints
  MUST use a separate secret from the read token, and fail closed when it is unset.
- **FR-013** Storage for one open conversation per gaming group: its id, an opaque NPC reference,
  when it opened, and per character the told value and when it was first asked for.
- **FR-014** A `/discern-honor` slash command that resolves the invoking player's character the way
  the 211 commands do, and replies EPHEMERALLY in every case (User Stories 1, 2 and 4).
- **FR-015** The first ask sets the "asked" timestamp; later asks do not move it and return the same
  value. The command performs no arithmetic on the value.
- **FR-016** A conversation not closed within 12 hours of opening is no longer served.
- **FR-017** The sheet's own copy of the knack's rules text (`app/game_data.py`, `discern_honor`)
  carries the same `(1k1 - 0.5)` typo and is corrected there, by that session.

### Rules text

- **FR-018** `rules/05-school_knacks.md` in `EliAndrewC/l7r`, Discern Honor: `0.5 * (1k1 - 0.5)`
  becomes `0.5 * (1k1 - 5)`, which is what the Virtue and Unconventional texts already say, what the
  code has implemented since 2026-08-27, and what gives the GM's stated range of -2.0 to +2.5.
  **Done 2026-09-21**, as an uncommitted working-tree edit; the GM commits that repository.

## Decisions (each made by the session, each cheap to change)

1. **Precompute and look up, rather than ask-then-resolve.** Priced and declined: the sheet bot
   deferring its reply while gm-assistant resolves the request. It costs 5-20 s of poll latency per
   ask, needs the interaction token carried between the two apps, and still needs idempotency built
   separately. Also declined: the player naming the NPC (`/discern-honor npc:Otsuki`), which leaks
   the NPC roster through autocomplete and leaves "the same conversation" to be guessed from time
   windows. Approved by the GM in message 2.
2. **The reply does not name the NPC.** An NPC's Obsidian Portal name can be a name the players do
   not know yet - somebody traveling under an alias. The players know who they are talking to; the
   bot does not need to tell them. The handoff leaves an optional display label in the payload so
   the GM can opt in per conversation later without a schema change.
3. **Each `begin_conversation` after a normal close is a new conversation**, even the same evening
   with the same NPC. The GM controls the boundary, so the GM controls the count. Put to the GM in
   the proposal; not objected to. Crash recovery is the one exception, and it is detected
   structurally (FR-011), not by a time window.
4. **With no conversation open, the manual call treats a same-day repeat as a slip.** The GM asked
   for protection against a slip; outside a conversation the calendar day is the only boundary
   there is. A real second conversation that day is one explicit argument away.
5. **The player is never told a value is exact.** The rule gives the player a number, not its
   error bar; "locked in" stays a GM-side note.
6. **What an abandoned conversation does with values already seen.** If the ask was already
   committed (FR-004 commits on sight), it stays committed and the GM edits the NPC's notes, which
   `abandon_conversation()`'s own docstring already names as the recovery path for a wrong-NPC open.
   Reversing an Obsidian Portal write automatically was priced and declined: the player HAS now been
   told a number, and which NPC it should count against is a judgment only the GM can make.
7. **Commit on sight, not at close** (FR-004). At-close is simpler and loses the record if the REPL
   dies; the knack's whole premise is that the first answer is remembered.

## Success criteria

- **SC-001** A player with the knack gets their number from Discord in one command, in under three
  seconds, with the GM typing nothing beyond the `begin_conversation` they already type.
- **SC-002** Across any number of asks in one conversation, by command or REPL or both, a PC's
  Obsidian Portal record advances exactly once.
- **SC-003** Nothing the sheet app stores or sends contains a true Honor value.
- **SC-004** Every record written before this feature still reads correctly afterward.

## Review history

See the end of this file once the `spec-fidelity` pass has run.
