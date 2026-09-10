# Feature Specification: Interrogation rolls grouped by line of questioning

**Feature Directory**: `specs/206-interrogation-lines`

**Created**: 2026-09-10

**Status**: Draft

**Input**: GM request 2026-09-10, reproduced verbatim in [gm-request.md](gm-request.md) together
with the session's judgment calls the GM accepted. Builds on feature 201
(`specs/201-discord-roll-capture`, which captures the rolls) and feature 202
(`specs/202-roll-annotation`, which holds them until the GM says what they were for).

## Why interrogation is different

Every other contested roll is written with both totals and the margin. An interrogation roll cannot
be, because its opposing roll is the NPC's Sincerity, and revealing that number tells the players
whether "doesn't seem to be holding anything back" meant the NPC was truthful or merely that the
interrogator rolled too low. The GM keeps the Sincerity roll to themselves. So the interrogation
roll is written ON ITS OWN, exactly as rolled, with the interrogator's skill rank attached so the
number can be read without the opposing side.

The rules (`rules/02-skills.md`, Interrogation) give the NPC two free raises in two situations: the
interrogator is talking casually rather than grilling, or the NPC is telling a lie they believe
cannot be disproven. The first is known to the players and MAY be noted; the second is secret by
construction and MUST NOT appear, since noting it would reveal that the NPC is lying at all.
Situational free raises to the interrogator (a scared or guilty subject) reveal NPC state the same
way. That is why the line carries no bonus for either side.

The rules also say the skill is *"rolled once for each line of questioning"*, so the unit written
to the record is the line of questioning, not the roll - several interrogators on one topic share a
line, and one interrogator on several topics gets several.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - An interrogation roll is written alone, exact, with its rank (Priority: P1)

A player rolls Interrogation. The GM annotates it with what the line of questioning was about. The
record shows the roll exactly as made, with the interrogator's skill rank, and nothing about the
opposing Sincerity roll: `interrogation: 25@2 Jimen - what Fumitake thinks of Tsuruchi`.

**Why this priority**: This is the leak the feature exists to close. Today an interrogation roll
annotated as contested writes the NPC's Sincerity total and the margin.

**Independent Test**: Annotate one interrogation roll; the written line carries the raw roll, the
rank and the note, and no second total, winner or margin.

**Acceptance Scenarios**:

1. **Given** an interrogation roll of 37 by a character whose recorded rank is 2, **When** it is
   annotated and written, **Then** the line reads `interrogation: 37@2 Jimen - <note>`.
2. **Given** a roll of 37, **When** it is written, **Then** it is 37 - not rounded to 35.
3. **Given** the GM has rolled Sincerity for the NPC, **When** the interrogation roll is
   annotated, **Then** the menu never offers that roll as an opposing side, and the Sincerity total
   appears nowhere in the record.
4. **Given** an interrogation roll, **When** the GM annotates it, **Then** no bonus is asked for
   on either side and none is applied.

---

### User Story 2 - Rolls on one line of questioning share a line (Priority: P1)

Two players roll Interrogation on the same topic. The GM annotates the first, and when annotating
the second says it belongs to the same line of questioning. The record shows one line with both
rolls: `interrogation (grilling): 37@2 Jimen / 24@1 Moriko - what Fumitake ordered his escorts to
do`. A roll on a different topic starts a new line.

**Why this priority**: The GM's stated design - the record is read per topic, and one line per
roll would scatter a single line of questioning across the record.

**Independent Test**: Annotate two interrogation rolls onto one line and a third onto a new one;
the record has exactly two interrogation lines.

**Acceptance Scenarios**:

1. **Given** one interrogation line already exists in the conversation, **When** the GM annotates
   another interrogation roll, **Then** the menu lists the existing lines by their notes and asks
   whether the roll joins one of them or starts a new one.
2. **Given** the GM chooses an existing line, **When** the roll is written, **Then** it appears on
   that line, and the GM is NOT asked for a note or whether the line was grilling - the line
   already has both.
3. **Given** the GM chooses a new line, **When** prompted, **Then** they are asked whether the
   interrogator was grilling and what the line of questioning was about.
4. **Given** no interrogation line exists yet, **When** the GM annotates the first interrogation
   roll, **Then** the join-or-new question is skipped and a new line is started.
5. **Given** rolls of 24 and 37 on one line, **When** it is written, **Then** the 37 comes first.
6. **Given** one character rolls Interrogation twice on different topics, **When** both are
   annotated to separate lines, **Then** the record has two lines, each naming that character.

---

### User Story 3 - Grilling is noted, per line (Priority: P2)

The interrogator put the subject to hard questions and did not let them steer. The players know
this, so it is not secret, and the line says so: `interrogation (grilling): ...`. A line where the
interrogator spoke casually has no parenthetical.

**Why this priority**: It is the one conditional Sincerity bonus that is safe to record, and it is
what lets the GM later reconstruct which free raises applied. It depends on Story 2's notion of a
line.

**Independent Test**: Annotate one line as grilling and one not; only the first carries
`(grilling)`.

**Acceptance Scenarios**:

1. **Given** a new line, **When** the GM answers that the interrogator was grilling, **Then** the
   line reads `interrogation (grilling): ...`.
2. **Given** a new line, **When** the GM answers that they were not, **Then** the line reads
   `interrogation: ...` with no parenthetical.
3. **Given** a line marked grilling, **When** a second roll joins it, **Then** the line is still
   grilling and the GM is not asked again.

---

### User Story 4 - A hand-typed roll gets its rank from the GM (Priority: P2)

A player typed their interrogation roll into Discord rather than using the character-sheet app, so
no rank was recorded with it. The menu asks the GM for the rank when annotating that roll, and only
that roll. A blank answer writes the roll with no `@`.

**Why this priority**: Without it, typed rolls - the primary input path per feature 201 - would
write a bare number that cannot be read without the opposing side.

**Independent Test**: Annotate an interrogation roll with no recorded rank, answer 2; the line
shows `37@2`. Annotate another and answer blank; the line shows `37`.

**Acceptance Scenarios**:

1. **Given** an interrogation roll whose rank the character-sheet app recorded, **When** it is
   annotated, **Then** the GM is NOT asked for a rank and the recorded one is written.
2. **Given** an interrogation roll with no recorded rank, **When** it is annotated, **Then** the
   GM is asked for the rank before the line-of-questioning questions.
3. **Given** that prompt, **When** the GM answers blank, **Then** the roll is written as `37`.
4. **Given** a roll of a skill other than Interrogation with no recorded rank, **When** it is
   annotated, **Then** no rank is asked for - nothing about other skills changes.

---

### User Story 5 - Everything else about annotation still holds (Priority: P2)

Interrogation rolls are held until annotated, discarded with `d`, abandoned as a group by Ctrl-C,
written bare by the exit path, and re-annotated by running the menu again - exactly as feature 202
established for every other skill.

**Why this priority**: The feature changes what an interrogation annotation ASKS and WRITES, not
when a roll is written or how the menu is left.

**Acceptance Scenarios**:

1. **Given** an unannotated interrogation roll, **When** `end_conversation()` is called,
   **Then** it raises naming the roll, as for any other held skill.
2. **Given** the GM presses Ctrl-C part way through annotating interrogation rolls, **When** the
   menu exits, **Then** no line of questioning is created and no roll is changed.
3. **Given** an interrogation roll discarded with `d`, **When** the record is written, **Then**
   the roll is absent and a line left with no rolls is not written.
4. **Given** unannotated interrogation rolls at interpreter exit, **When** the exit path writes
   them, **Then** each is written on its own bare line - `interrogation: 37@2 Jimen` - with no
   note and no grouping, since no line of questioning was ever stated.
5. **Given** Etiquette rolls in the same conversation, **When** the record is written, **Then**
   their one-line, highest-first form is unchanged.

---

### Edge Cases

- A roll joins a line and is then re-annotated onto a different line: it moves; the first line
  is written without it, and if that leaves the first line empty it is not written at all.
- Two rolls tie on one line: the order they were made is kept between them.
- The same character rolls twice on the SAME line (a re-roll the GM allowed): both appear on the
  line - every roll on the line is listed, none is deduplicated.
- The rank prompt gets something that is not a whole number: re-ask, as the bonus prompt does.
- The join-or-new prompt gets a number outside the list: re-ask.
- A line whose only roll was discarded still shows in the join-or-new list until the menu commits,
  since staged decisions are not applied until then; once committed it is gone.
- An interrogation roll made before this feature and already written as a contested line: on the
  next write it is rendered by the new rules, since every write REPLACES the conversation's block.
  Its stored opposing total is ignored rather than migrated.
- The GM answers `c` (contested) or `ob` at the kind prompt for an interrogation roll: those
  options are not offered for it; the prompt for an interrogation roll is the line-of-questioning
  prompt, with `d` and blank as its only other answers.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: An interrogation roll MUST be held until annotated and written by the exit path if
  never annotated, exactly as feature 202 requires of every non-Etiquette skill. Nothing in this
  feature changes WHEN a roll is written.
- **FR-002**: An interrogation roll MUST NEVER be paired with an opposing roll. `annotate()` MUST
  NOT offer "contested" for it, and the GM's Sincerity total MUST be written nowhere. The reason is
  the leak described above; this is the GM's ruling (2026-09-10: *"contested interrogation rolls are
  never displayed"*).
- **FR-003**: An interrogation roll MUST be written EXACTLY as rolled - never rounded, and with no
  bonus applied on either side. `annotate()` MUST NOT ask for a bonus on an interrogation roll (the
  `ob` option is not offered for it). The reason is that every bonus in play on either side -
  the NPC's unprovable-lie raises, situational raises for a scared or guilty subject - reveals NPC
  state; grilling is the one exception and is carried by FR-006, not as a number.
- **FR-004**: Interrogation rolls MUST be written GROUPED by line of questioning, one written line
  per line of questioning, in the form
  `interrogation[ (grilling)]: <roll>[@<rank>] <name> / <roll>[@<rank>] <name> - <note>`.
  Roller entries are number-first with no parentheses and are separated by ` / `, as the Etiquette
  line separates its rollers. The example the GM will see:
  `interrogation (grilling): 37@2 Jimen / 24@1 Moriko - what Fumitake ordered his escorts to do`.
- **FR-005**: Within a line, rollers MUST be ordered highest roll first; ties keep the order the
  rolls were made. This is the Etiquette rule, applied so there is one ordering rule for grouped
  lines.
- **FR-006**: Whether the interrogator was grilling MUST be recorded PER LINE OF QUESTIONING and
  asked ONCE, when the line is created; a roll joining an existing line inherits it. A grilling line
  is written `interrogation (grilling):`; any other line `interrogation:`.
- **FR-007**: The interrogator's skill rank MUST be written as `@N` after the roll. The rank the
  character-sheet app recorded with the roll MUST be used when there is one and MUST NOT be asked
  for. When a roll has no recorded rank, `annotate()` MUST ask for it - on interrogation rolls only
  - and a blank answer MUST write the roll with no `@`.
- **FR-008**: When at least one line of questioning already exists in the conversation, annotating
  a further interrogation roll MUST list the existing lines (by note, with `(grilling)` where set)
  and ask whether the roll joins one of them or starts a new one. When none exists, the question
  MUST be skipped and a new line started.
- **FR-009**: Starting a new line MUST ask, in this order: the rank if FR-007 needs it, whether
  the interrogator was grilling, and what the line of questioning was about. Joining an existing
  line MUST ask only for the rank if FR-007 needs it - never for the note or grilling again.
- **FR-010**: Lines of questioning MUST be written in the order they were created, in sequence
  with the conversation's other annotated rolls at the position of the line's first roll, so the
  record still reads as the conversation happened (feature 202's FR-014).
- **FR-011**: Discard (`d`), Ctrl-C abandoning every staged answer, and re-running `annotate()` to
  re-annotate MUST behave for interrogation rolls exactly as feature 202 specifies. A line of
  questioning left with no rolls MUST NOT be written.
- **FR-012**: The exit path MUST write an unannotated interrogation roll bare, one roll per line,
  as `interrogation: <roll>[@<rank>] <name>` - no note, no grouping, no `(grilling)` - since the
  GM never said which line of questioning it belonged to.
- **FR-013**: The record's other lines MUST be unchanged: Etiquette's one-line highest-first form,
  the open line with its ` - ` before the note, and the contested line for every skill other than
  Interrogation.
- **FR-014**: The rank and join-or-new prompts MUST re-ask on an answer they cannot use, and MUST
  go through the same quiet input as the rest of the menu so answers stay out of the REPL's
  history (2026-09-09).

### Key Entities

- **Line of questioning**: one topic put to the NPC - its note (what it was about), whether the
  interrogator was grilling, and the interrogation rolls made on it, in the order they were made.
  Created by the first roll annotated to it; written once, listing every roll on it.
- **Interrogation roll**: a captured roll of the Interrogation skill - the exact total, the
  roller, and the roller's rank when the character-sheet app recorded one or the GM supplied it.
  Never carries an opposing total.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: No number the GM rolled for the NPC's Sincerity, and no margin against it, appears
  in any record this feature writes.
- **SC-002**: Every interrogation roll in the record can be read without the opposing side: the
  exact roll and the interrogator's rank are both on the line whenever a rank is known.
- **SC-003**: A line of questioning with several interrogators is ONE line in the record, and a
  conversation with several topics has one line per topic.
- **SC-004**: Annotating the first interrogation roll on a new line takes at most four answers -
  which roll, grilling, the note, plus the rank only when it was not recorded. Joining an existing
  line takes at most two - which roll and which line - plus that same conditional rank.
- **SC-005**: Nothing about the annotation of any other skill changes: the same prompts, in the
  same order, writing the same lines as before this feature.

## Assumptions

- The rank asked for in FR-007 is the interrogator's Interrogation skill rank, the same number the
  character-sheet app supplies as `rank` on a recorded roll.
- "Grilling" is a property of the line of questioning, not of each roller, because the rules attach
  the casual-versus-grilling distinction to how the line is conducted and the GM's own example
  places `(grilling)` on the line. If two interrogators on one line differed, the GM would start a
  second line.
- The GM's Sincerity roll for the NPC continues to be made with `xky` and kept in the GM's own
  buffer; it is simply never offered to, or stored by, an interrogation annotation. Keeping it in
  GM-only notes was offered and declined for now (2026-09-10).
- Interrogation is the only skill handled this way. A player's own Sincerity roll - open, or
  contested against an NPC's Interrogation - is out of scope and unchanged; the GM raised only the
  player-interrogates-NPC direction, and the other direction is theirs to rule on if it ever
  matters.
