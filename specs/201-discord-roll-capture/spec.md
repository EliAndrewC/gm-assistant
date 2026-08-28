# Feature Specification: Discord roll capture into Obsidian Portal

**Feature Directory**: `specs/201-discord-roll-capture`

**Created**: 2026-08-28

**Status**: Draft

**Input**: GM request, this session (2026-08-28). Verbatim scope-setting quotes are reproduced in
Assumptions so the spec can be graded against the GM's own words.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Record a round of open rolls against an NPC (Priority: P1)

During play the GM opens a conversation with an NPC by name at the REPL. Players post their rolls
in the group's Discord channel - some as pasted dice-card images, some typed by hand. The GM closes
the conversation. The round's rolls appear as one line in that NPC's public Obsidian Portal bio,
directly under the portrait, in the GM's existing shorthand, with each total capped and rounded per
the recording rules.

**Why this priority**: This is the entire point of the feature. It removes the transcription work
that currently slows the game, and it makes past rolls readable from the OP page - which a pasted
Discord permalink never has.

**Independent Test**: With a conversation open and a known set of messages in a channel, closing
the conversation produces the expected bio line. Fully testable against saved Discord fixtures with
no live game in progress.

**Acceptance Scenarios**:

1. **Given** a conversation opened with `begin_conversation("Otsuki")` and five players posting
   etiquette rolls of 38, 28, 25, 24 and 19, **When** the GM calls `end_conversation()`, **Then**
   the NPC's public bio gains a line reading `... etiquette: 35 / 25 / 25 / 20 / 15` with the
   players' character names in the same order as their totals.
2. **Given** an open etiquette roll of 68, **When** the round is recorded, **Then** it is written
   as `40`, not `65`.
3. **Given** a conversation opened against a name matching more than one OP character, **When**
   `begin_conversation` is called, **Then** it raises an error listing the candidates and opens
   nothing.
4. **Given** no conversation is open, **When** rolls are posted in Discord, **Then** nothing is
   written to Obsidian Portal.

---

### User Story 2 - Read hand-typed rolls (Priority: P1)

Roughly a third of rolls are typed rather than pasted, and which players type is stable per person.
The system reads those messages and extracts the total, the skill, and the skill rank when stated.

**Why this priority**: Equal to Story 1 in priority because it is the only path that works with no
dependency on the character-sheet app, so it is the path that can be proven first and the one that
keeps the feature useful if the sheet endpoints are unavailable.

**Independent Test**: Run the parser over the saved corpus of real messages and compare against a
hand-checked expected table. No network, no Obsidian Portal.

**Acceptance Scenarios**:

1. **Given** the message `38 Etiquette @3`, **When** parsed, **Then** total 38, skill Etiquette,
   rank 3.
2. **Given** `10->9 8 +5 Streetwise = 32 Law@2`, **When** parsed, **Then** total 32, skill Law,
   rank 2 - the dice trace and the named bonus are ignored rather than summed.
3. **Given** a message containing two rolls on separate lines, **When** parsed, **Then** both are
   returned, attributed to the same character.
4. **Given** `15@1` with no skill named, **When** parsed, **Then** it is reported as unattributable
   to a skill and excluded from the written line rather than guessed at.
5. **Given** an ordinary conversational message containing a number, **When** parsed, **Then** no
   roll is produced.

---

### User Story 3 - Resolve pasted dice cards without reading the image (Priority: P2)

A pasted dice-card PNG is matched to the exact roll it was rendered from by joining the Discord
message's author and timestamp against the character-sheet app's roll history.

**Why this priority**: It covers the larger share of rolls (204 image posts against ~99 typed), but
it depends on endpoints that do not exist yet, so it cannot be the first thing proven.

**Independent Test**: With saved Discord messages and a saved roll-history fixture, the join
produces the correct character, skill, rank and total; an unrelated image in the same channel
produces nothing.

**Acceptance Scenarios**:

1. **Given** a message with an image attachment from a player whose roll history contains one roll
   within the match window, **When** the round is assembled, **Then** that roll is used with its
   exact skill, rank and total.
2. **Given** a message with an image attachment and no roll in the window, **When** the round is
   assembled, **Then** the message is ignored - this is how memes are excluded.
3. **Given** a player who both pasted a card and typed the same roll, **When** the round is
   assembled, **Then** the roll is recorded once, preferring the roll-history record.
4. **Given** the character-sheet endpoints are unreachable, **When** the round is assembled,
   **Then** the typed rolls are still recorded and the GM is told which image posts could not be
   resolved.

---

### User Story 4 - Record a contested roll (Priority: P3)

Two sides roll against each other. Both adjusted totals are shown, along with the margin and the
winner.

**Why this priority**: Less frequent than open rolls and needs both sides present, but the GM has
specified the rule and it shapes the data model, so it is in scope for the first version.

**Independent Test**: Given two rolls marked as opposing sides, the formatter produces the expected
line. Pure logic, no I/O.

**Acceptance Scenarios**:

1. **Given** Jimen rolling 41 against Otsuki's 28 on sincerity, **When** recorded, **Then** the
   line shows both totals unrounded, the winner, and a margin of 10 (13 rounded down to 5s).
2. **Given** the two sides tie, **When** recorded, **Then** the line reports a tie with a margin of
   zero and no winner.

---

### Edge Cases

- A roll is posted before `begin_conversation` or after `end_conversation`: excluded. The
  conversation's open and close times bound the round.
- The same player posts two rolls of the same skill in one conversation: both are kept, in posting
  order. Deduplication applies only across the image and typed paths for the same underlying roll.
- A player's Discord id maps to no character on the sheet: their typed roll is still parsed, and is
  reported to the GM as unattributed rather than written with a wrong name.
- The GM's own posted rolls are NPC rolls and are never filtered out; contested rolls need them.
- Discord returns an error or rate-limits: the conversation stays open and no partial line is
  written.
- The NPC's bio has no portrait embed: the line goes at the top of the bio.
- `end_conversation()` with zero rolls collected: nothing is written and the GM is told so.
- A skill total that is negative or absent: excluded rather than written as `0`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The GM MUST be able to open a conversation by NPC name at the REPL, and the name MUST
  resolve through the same matching used by the existing Discern Honor tool, including its
  ambiguous-match error that lists the candidates.
- **FR-002**: The GM MUST be able to close a conversation, at which point the collected rolls are
  formatted and written.
- **FR-003**: Only rolls posted between the open and the close are included in a conversation.
- **FR-004**: The system MUST read rolls from both group channels, and MUST NOT require any ability
  to post to Discord.
- **FR-005**: The system MUST extract rolls from hand-typed messages, recovering total, skill, and
  stated rank, across the observed forms; a message that is not a roll MUST produce nothing.
- **FR-006**: `@N` in a typed roll MUST be interpreted as a skill rank when N is 5 or less, and as
  a total when N is 10 or more. Between 6 and 9 it is ambiguous and MUST be surfaced to the GM
  rather than guessed. (Skills are capped at rank 5 - `rules/01-character_creation.md`.)
- **FR-007**: The system MUST resolve pasted dice-card images by matching the Discord message's
  author and timestamp against the character-sheet app's recorded rolls, and MUST NOT inspect image
  content.
- **FR-008**: An image with no matching recorded roll MUST be ignored silently, since ordinary
  images share the same filenames as dice cards.
- **FR-009**: When the same roll appears both as a card and as typed text, it MUST be recorded once,
  preferring the recorded roll.
- **FR-010**: Open roll totals MUST be rounded down to the nearest 5.
- **FR-011**: Open Etiquette totals MUST be capped at 40 before rounding.
- **FR-012**: Contested rolls MUST show both sides' totals after each side's bonuses, unrounded,
  plus the winner and the margin, with only the margin rounded down to the nearest 5.
- **FR-013**: The recording rules MUST be expressed so that adding a further rule - another capped
  skill, another rounding increment - is a data or single-function change, not a restructuring.
- **FR-014**: The result MUST be written into the NPC's PUBLIC Obsidian Portal bio, immediately
  below the portrait embed, and MUST NOT modify the GM-only notes.
- **FR-015**: Writing MUST be idempotent in the sense that a failed or repeated write does not
  duplicate or corrupt existing bio content; existing bio text MUST be preserved.
- **FR-016**: When a skill rank is needed and was not stated, it MUST be looked up for that
  character; when it cannot be determined, the roll is still recorded and the rank is omitted.
- **FR-017**: Collection MUST NOT block the REPL prompt.
- **FR-018**: When the character-sheet endpoints are absent or failing, the typed path MUST still
  work end to end, and the GM MUST be told what could not be resolved.
- **FR-019**: `end_conversation()` MUST write immediately, with no confirmation step. A separate
  call MUST be available to abandon an open conversation without writing; it is not part of the
  normal path and nothing blocks on it.
- **FR-020**: Every roll recorded MUST be attributable to a named character; an unattributed roll is
  reported to the GM and excluded from the line.
- **FR-021**: A round of open rolls MUST be written as one line pairing character names with their
  recorded totals in the same order, in the GM's existing shorthand -
  `<name> / <name> / ... <skill>: <total> / <total> / ...`, as in the GM's own example
  `Sadakichi / Moriko / Jimen / Tetsuro / Toshihiro etiquette: 35 / 25 / 25 / 20 / 15`.

### Key Entities

- **Conversation**: an open NPC, the moment it opened, the channel it watches, and the rolls
  collected so far. At most one is open at a time.
- **Roll**: a character, a skill, a total, an optional rank, the source it came from (recorded card
  or typed text), the Discord message it came from, and whether it is one side of a contest.
- **Contest**: two rolls marked as opposing sides, plus the derived winner and margin.
- **Recording rule**: the mapping from a raw total to the number written down - the rounding
  increment and any per-skill cap.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A round of five rolls is recorded into the NPC's record with two REPL calls and no
  hand transcription.
- **SC-002**: Every roll in the saved corpus of real typed messages is either parsed correctly or
  explicitly reported as unparsed; none is parsed WRONGLY.
- **SC-003**: No message that is not a roll produces a roll, measured over the full saved corpus of
  1,400 real messages.
- **SC-004**: Past rolls for an NPC can be read from the Obsidian Portal page alone, with no visit
  to Discord.
- **SC-005**: The recording rules are verified by tests covering the rounding boundary, the
  Etiquette cap, and the contested margin.
- **SC-006**: A new capped skill can be added by changing one line of data.

## Assumptions

- **Verbatim GM instruction on contested rolls** (2026-08-28): *"A contested role should show each
  of the two roles that are being compared after those roles are adjusted for bonuses on each side.
  and then it should show the difference between them and who won. The amount that the winner won by
  should be rounded down to the nearest increment of five, just like all open rolls are rounded down
  to the nearest increment of five."*
- **Verbatim GM instruction on the Etiquette cap** (2026-08-28): *"open etiquette rolls are capped
  at forty ... a very high role on etiquette simply cannot represent something extremely noteworthy
  because a thing which is noteworthy in most circumstances is almost definitionally impolite."*
  This reasoning is recorded with the rule in the code, per the project's record-the-why
  requirement.
- **Verbatim GM instruction on placement** (2026-08-28): *"we would put this in the character bio
  section of Obsidian Portal directly underneath their portrait. We do not need a separate GM only
  section for explaining things like rounding and why things are capped."*
- The GM stated *"there will be more subtleties to be added later"*, so this spec covers the rules
  given so far and requires only that further rules be cheap to add.
- The exact wording of the contested line is not specified by the GM; the format
  `Jimen vs Otsuki sincerity: 41 vs 28, Jimen by 10` is chosen to sit alongside the established open
  format and is trivially adjustable.
- Rolls are collected from the channel of the group the NPC's campaign belongs to; when that cannot
  be determined the GM names the channel when opening the conversation.
- The character-sheet endpoints described in `character-sheet/externally-queryable-roll-results.md`
  do not exist yet. This feature is built against a client for them and tested entirely with saved
  fixtures.
- The Discord bot is read-only by design (permissions 66560) and this feature never posts.
- Existing project machinery is reused rather than rebuilt: NPC name resolution, the Obsidian Portal
  client, and the REPL's background-refresh pattern.
- **The abandon call in FR-019 is an ADDITION beyond the GM's request**, kept only for the
  "opened against the wrong NPC" case. The GM described two calls and no third step, and this
  project forbids pre-review gates on generated content, so `end_conversation()` writes immediately
  and nothing blocks on the abort. To be raised with the GM once the implementation works, per
  constitution Principle XVI.

## Review history

**Round 1** (2026-08-28, `spec-fidelity` Mode 2, independent of the author): **CHANGES REQUIRED.**
Question 1 (does it specify what was asked) passed on every clause of the request, including all
four elements of the contested rule and both halves of the placement instruction. Question 2 found
one unrequested addition and one omission:

1. **FR-019 was a pre-review gate.** As originally written - *"The GM MUST be able to see what will
   be written before it is written"* - it reinserted a manual step at the table, which is the exact
   cost the feature exists to remove, contradicted the spec's own SC-001 ("two REPL calls"), and
   matched the shape CLAUDE.md's NO PRE-REVIEW GATE rule forbids. Rewritten to write immediately,
   with the abort call kept as an explicitly-recorded addition.
2. **No FR carried the output line format**, the single most concrete thing the GM specified; it
   existed only in an acceptance scenario. Added as FR-021, quoting the GM's example.

The reviewer explicitly considered and WITHDREW three findings after reading `research.md` - FR-006's
`@N` threshold, FR-008's silent ignore, and FR-020's exclusion of unattributed rolls - on the
grounds that each handles data outside the domain of a GM rule rather than carving out an exception
inside one. Recorded here so a later reviewer does not re-raise them.

Two items referred to the GM rather than changed, both after the implementation works: whether the
Etiquette cap should also apply to CONTESTED etiquette rolls (the GM's words scope it to open rolls,
but the stated reason - politeness has a ceiling - would apply to both), and whether a bare-number
roll should inherit the conversation's skill.

**Round 2** (2026-08-28, same agent, re-review of the two changes only): **FAITHFUL.** Both changes
were judged applied "correctly and completely", with neither introducing a new addition, carve-out
or contradiction. The reviewer's words: *"The pre-review gate is gone. The write path is now
unconditional and single-step"*, and of FR-021, *"The most concrete thing the GM specified now has a
normative carrier in the FR list rather than living only in an acceptance scenario."* FR-021 was
moved after FR-020 to fix the numbering order the reviewer flagged as cosmetic. Cleared for
implementation.
