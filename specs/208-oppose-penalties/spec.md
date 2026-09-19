# Feature Specification: Oppose Social and Oppose Knowledge penalties, applied by themselves

**Feature Directory**: `specs/208-oppose-penalties`

**Created**: 2026-09-19

**Status**: Draft

**Input**: GM request 2026-09-19, reproduced verbatim in [gm-request.md](gm-request.md). Builds on
feature 201 (roll capture), 206 (lines of questioning) and 207 (the NPC's tagged rolls, the hidden
Sincerity roll, retroactive `grilling()`).

## Why

Two school knacks change every later roll in a conversation. A player rolls Oppose Social, the
result is divided by five (rounding down), and the NPC subtracts that from every roll it makes with
Air for the rest of the conversation. Oppose Knowledge does the same to the NPC's Water rolls.

Today the tool does not even see these rolls: the parser reads one skill word beside a number, and
both knacks are two words. So the GM carries the penalty in their head and subtracts it by hand
from every `tact`, `sincerity` and `investigation` roll for the rest of the scene - in the busiest
part of the session, and with a number that is easy to forget ten minutes later.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - An oppose roll is captured and takes effect with nothing asked (Priority: P1)

A player posts `32 oppose social` in Discord during an open conversation. The tool captures it,
tells the GM in the terminal that the NPC now takes -6 on Air rolls, and asks nothing: the roll is
never offered by `annotate()` and never holds `end_conversation()` open.

**Independent Test**: Feed a message `32 oppose social@3` into an open conversation; the roll is
captured, the conversation reports a -6 Air penalty, and `annotate()` has nothing pending.

**Acceptance Scenarios**:

1. **Given** an open conversation, **When** a player posts `32 oppose social`, **Then** the roll is
   captured under the skill `oppose social` and the GM is told the NPC takes -6 on Air rolls.
2. **Given** the same, **When** a player posts `27 oppose knowledge@2`, **Then** the NPC takes -5
   on Water rolls (27 / 5, rounded down) and the rank 2 is kept on the roll.
3. **Given** a captured oppose roll, **When** the GM runs `annotate()` or `end_conversation()`,
   **Then** the oppose roll is not offered for annotation and does not block closing.
4. **Given** the character-sheet bot's form `**Tsuruchi Jimen**: **32** Oppose Social@3`, **When**
   collected, **Then** it is read exactly as the typed form is.
5. **Given** a message `32 oppose` with no second word, **When** collected, **Then** nothing is
   recorded and the GM is told the word could be either knack (today's ambiguous-skill report).

### User Story 2 - The NPC's later rolls with that ring carry the penalty (Priority: P1)

After the -6 Air penalty is in effect the GM rolls for the NPC - `tact()`, `tact(5, 3)`, or
`xky(5, 3) - tact`. The tool subtracts 6, says so, and the total it shows, returns and later pairs
in `annotate()` is the total after the penalty. A Water roll (`investigation()`) is untouched by
Oppose Social, and an Air roll is untouched by Oppose Knowledge.

**Independent Test**: With a -6 Air penalty in effect, `xky(5, 3) - tact` yields a roll whose total
is six below its dice, and `xky(5, 3) - investigation` yields one that is not reduced.

**Acceptance Scenarios**:

1. **Given** Oppose Social 32 in effect, **When** the GM calls `tact()`, **Then** the printed and
   returned total is the roll less 6, and a line says `-6 oppose social`.
2. **Given** the same, **When** the GM tags `xky(5, 3) - tact`, **Then** that roll's total drops by
   6 and the value echoed at the prompt is the reduced one.
3. **Given** the same, **When** the GM rolls a Water skill, **Then** nothing is subtracted.
4. **Given** the same, **When** `annotate()` pairs a player's manipulation with that tagged tact
   roll, **Then** the opposing total used and written is the reduced one.
5. **Given** the same, **When** the GM picks an UNTAGGED `xky` roll (or types a total) as the
   opposing side of a contest whose opposing skill rolls with Air, **Then** the tool subtracts the
   6 and says so, because the pairing is the moment the roll's ring becomes known.
6. **Given** a tagged NPC roll made BEFORE the oppose roll was posted, **When** the oppose roll
   arrives, **Then** that earlier roll is not changed.
7. **Given** no conversation is open, **When** a roll is tagged, **Then** nothing is subtracted
   (feature 207's rule: nothing is recorded or checked without an open conversation).

### User Story 3 - A line of questioning still in progress is affected retroactively (Priority: P1)

The GM declared a line of questioning with the NPC's hidden Sincerity roll. Part way through it a
player rolls Oppose Social. Because that Sincerity roll is still active - it opposes every
interrogation roll on the line until the next line is declared - the penalty comes off it
retroactively, exactly as `grilling()` takes the casual raises off. The private who-won comparison
is re-printed for the rolls already on the line, and the GM-only `Hidden rolls:` entry shows the
penalty beside the Sincerity total.

**Independent Test**: Declare a line with Sincerity 48, land an interrogation roll of 40 (not
detected), then an Oppose Social of 45 (-9): the comparison for that roll is recomputed against
48 + 10 - 9 and the GM-only entry names the -9.

**Acceptance Scenarios**:

1. **Given** a current line with a hidden Sincerity roll and interrogation rolls on it, **When** an
   Oppose Social roll arrives, **Then** each comparison on that line is recomputed with the penalty
   and re-printed in the terminal.
2. **Given** the same, **Then** the GM-only entry reads like
   `sincerity 48 (+10 not grilling, -9 oppose social) - topic: Jimen 40@2 DETECTED`.
3. **Given** an EARLIER line (one that ended when a later line was declared before the oppose
   roll), **When** the oppose roll arrives, **Then** that earlier line is unchanged.
4. **Given** the oppose roll is already in effect, **When** a NEW line is declared with a Sincerity
   roll, **Then** that line's comparison carries the penalty once - not twice, even though the
   Sincerity roll was itself a tagged Air roll made after the oppose roll.
5. **Given** any of the above, **Then** the PUBLIC interrogation line is unchanged: it never showed
   the Sincerity roll and still does not, and the public outcome remains the GM's call through
   `detected()`.
6. **Given** an Oppose Knowledge roll, **When** it arrives mid-line, **Then** the line is
   unaffected (Sincerity rolls with Air).

### User Story 4 - Several oppose rolls do not stack; the highest takes effect (Priority: P1)

Two PCs both roll Oppose Social: Jimen 32 (-6), then Moriko 41 (-8). The penalty in effect becomes
-8, not -14. Had Moriko rolled 20 (-4), Jimen's -6 would have stayed.

**Acceptance Scenarios**:

1. **Given** Oppose Social 32 then 41, **When** the NPC next rolls with Air, **Then** 8 is
   subtracted.
2. **Given** Oppose Social 32 then 20, **Then** 6 is still subtracted and the GM is told the lower
   roll changes nothing.
3. **Given** Oppose Social 32 and Oppose Knowledge 41, **Then** Air rolls take -6 and Water rolls
   take -8: the two knacks never combine or compete.
4. **Given** an oppose roll the GM later discards as a mistake, **Then** it stops counting.

### User Story 5 - The oppose roll is part of the conversation's record (Priority: P2)

The roll is written to the NPC's public bio in the sequence of the conversation, in the open-roll
shape, with a note the tool writes itself - the GM is asked nothing:

```
30 oppose social: Jimen - Otsuki takes -6 on Air rolls
```

**Acceptance Scenarios**:

1. **Given** a captured oppose roll, **When** the conversation writes, **Then** the line above
   appears in sequence with the other rolls, the total rounded down to 5 like any open roll.
2. **Given** a second, lower oppose roll, **Then** its line says it changed nothing; a second,
   higher one says whose penalty it replaced.

### Edge Cases

- An oppose roll posted just before the GM rolls for the NPC, but not yet seen by the 20-second
  watcher: when it IS collected, any tagged NPC roll of the affected ring made after the oppose
  roll's message time is reduced then, and the GM is told which rolls changed. Timing is by MESSAGE
  time, as lines of questioning already are.
- A bare-number Sincerity roll (`new_line_of_questioning("topic", 48)`): the line's penalty is
  applied to it like the casual raises are.
- The manipulation default of 15 ("no roll made") is not a roll and takes no penalty.
- An oppose roll from a poster with no known character is reported as unresolved, like any roll.
- A roll marked a mistake at the disagreement prompt takes no penalty.
- The rules file is missing or an oppose knack's text no longer names a ring: that knack has no
  effect and nothing fails.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The tool MUST capture `oppose social` and `oppose knowledge` rolls from the typed and
  bot-posted forms (number first, optional `@rank` on either side), including unambiguous per-word
  abbreviations (`opp soc`), and from the recorded-roll path.
- **FR-002**: Capturing the two-word knacks MUST NOT change how any existing message parses; the
  real-message corpus count is the regression fixture.
- **FR-003**: The penalty MUST be the roll's total divided by 5, rounded down. Oppose Social applies
  to rolls made with Air; Oppose Knowledge to rolls made with Water. Which ring each knack affects
  MUST be read from the rules text, not copied.
- **FR-004**: An oppose roll MUST take effect with no input from the GM, MUST NOT be offered by
  `annotate()`, and MUST NOT hold `end_conversation()` open.
- **FR-005**: From the oppose roll's message time onward, every roll the tool knows the NPC made
  with the affected ring MUST have the penalty subtracted: the called skill form, the tagged `xky`
  form, and an untagged roll or typed total at the moment `annotate()` pairs it as an opposing roll
  of a skill with that ring. The subtraction MUST be shown to the GM each time.
- **FR-006**: NPC rolls made before the oppose roll MUST NOT change, with ONE exception (FR-007).
- **FR-007**: The hidden Sincerity roll of the line of questioning that was current when an Oppose
  Social roll was made MUST carry the penalty retroactively, as must every later line's. Lines that
  had already ended MUST NOT. Comparisons already printed for the affected line MUST be re-printed.
- **FR-008**: A Sincerity roll MUST never carry the penalty twice (once as a tagged Air roll, once
  as its line's roll).
- **FR-009**: Several oppose rolls of the same knack MUST NOT stack: the highest live one in effect
  at the time of the NPC's roll is the one applied. The two knacks are independent of each other.
  A discarded oppose roll MUST stop counting.
- **FR-010**: The penalty on a hidden Sincerity roll MUST appear only in the terminal and the
  GM-only `Hidden rolls:` block, never in the public bio. The public interrogation line MUST be
  byte-identical with and without an oppose roll.
- **FR-011**: The oppose roll itself MUST be written to the public bio in conversation order, in
  the open-roll shape, with a tool-written note naming the penalty and the ring.
- **FR-012**: With no conversation open, nothing is subtracted from any roll.
- **FR-013**: The tool owns this penalty everywhere. The GM is never expected to subtract it by
  hand, and the tool never adjusts anything else the GM typed onto a roll.

### Key Entities

- **Oppose roll**: a captured player roll of one of the two knacks; its penalty (total / 5,
  rounded down) and the ring it affects are derived from it, never stored beside it.
- **Penalty in effect**: for a ring at a moment - the highest live oppose roll of the matching
  knack made at or before that moment. Derived from the conversation's rolls.
- **NPC roll**: the GM's recorded roll, which now carries the penalty it took separately from the
  bonuses the GM typed, so the two are never confused.

## Decisions the request left open

Settled by the session without asking (the GM starts work and leaves). Each is cheap to reverse.

1. **The oppose roll is written to the bio** (FR-011). The request says the rolls "do not even need
   to be annotated", which presumes they are recorded; the player knows their own roll and the
   rules make the penalty public arithmetic, so nothing leaks. Declined: recording it nowhere
   (the conversation's record would then not explain why the NPC's later totals are low).
2. **The tagged `xky` form takes the penalty too**, although feature 207 gives the automatic
   acting/history RAISES only to the called form. That rule exists because the GM already types
   the acting `+ 10` by hand; nobody types the oppose penalty by hand - automating it is the whole
   request ("All rolls made by the NPC").
3. **An untagged roll, or a typed total, takes the penalty when `annotate()` pairs it** against a
   player's roll, because that is when its skill - and so its ring - becomes known. Declined:
   leaving typed totals alone and printing a reminder; two rules for one penalty is how a number
   gets subtracted twice or not at all.
4. **"Still active" means the line that was current at the oppose roll's message time**, plus every
   later line. Declined: only lines whose Sincerity roll was itself made earlier.
5. **Only these two knacks join the vocabulary.** Other two-word knacks (double attack, ...) would
   each need a ruling on how `annotate()` treats them, which nobody has made.
6. **The NPC's own Oppose rolls against the PCs are out of scope**: the tool tracks no PC rolls'
   arithmetic (the character-sheet app owns it).
7. **"Once per conversation" is not enforced.** A second roll by the same PC is handled by
   highest-wins like any other; policing the table is the GM's job.

## Success Criteria *(mandatory)*

- **SC-001**: After a player's oppose roll, the GM performs zero manual subtractions for the rest
  of the conversation: every NPC roll of the affected ring shows the penalty already applied.
- **SC-002**: The GM is asked zero questions about an oppose roll.
- **SC-003**: The real-message corpus parses to exactly the same rolls as before the feature.
- **SC-004**: No hidden number reaches the public bio (the existing leak test still passes with an
  oppose roll in the conversation).

## Assumptions

- One NPC per conversation (feature 207's ruling), so every oppose roll targets that NPC.
- Players type the knack number-first like every other roll; there are no real examples in the
  corpus to check against, so the forms accepted are the existing ones with a two-word name.
