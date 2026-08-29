# Feature Specification: Annotating rolls

**Feature Directory**: `specs/202-roll-annotation`

**Created**: 2026-08-29

**Status**: Draft

**Input**: GM request 2026-08-29, reproduced verbatim in [gm-request.md](gm-request.md). Builds on
feature 201 (`specs/201-discord-roll-capture`), which captures the rolls this feature annotates.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - An unannotated roll is not written (Priority: P1)

A player rolls Precepts. The line the GM would read back months later - `Jimen precepts: 25` - tells
them nothing about what the roll was for, so it is held rather than written. Etiquette is exempt:
those rolls are presumed to be introductions, so annotating each one would add nothing.

**Why this priority**: This is the point of the feature. A record the GM cannot interpret is not
worth writing, and today the tool writes exactly that kind of record for every skill.

**Independent Test**: Collect one Precepts roll and one Etiquette roll; only the Etiquette line
reaches Obsidian Portal.

**Acceptance Scenarios**:

1. **Given** a collected Precepts roll with no annotation, **When** the watcher writes, **Then**
   the Precepts roll does not appear in the record.
2. **Given** a collected Etiquette roll with no annotation, **When** the watcher writes, **Then**
   it appears exactly as it does today.
3. **Given** a Precepts roll that has since been annotated, **When** the watcher writes, **Then**
   it appears with its description.

---

### User Story 2 - end_conversation() refuses to discard unannotated rolls (Priority: P1)

The GM closes a conversation while rolls are still unannotated. Rather than writing a record they
cannot read, or silently dropping the rolls, the call fails and says which rolls need attention.
The conversation stays open.

**Why this priority**: Equal to Story 1 - it is the other half of the same rule. Without it, the
holding behavior would silently lose rolls at the moment of closing.

**Independent Test**: Close a conversation holding one unannotated non-Etiquette roll; the call
raises, names the roll, and the conversation is still open afterwards.

**Acceptance Scenarios**:

1. **Given** one unannotated Precepts roll, **When** `end_conversation()` is called, **Then** it
   raises with a message naming the roll and telling the GM to annotate it, and nothing is written.
2. **Given** that same state, **When** the call has raised, **Then** the conversation is STILL
   OPEN and the watcher is still running.
3. **Given** only Etiquette rolls, **When** `end_conversation()` is called, **Then** it writes and
   closes normally.

---

### User Story 3 - Exiting the REPL saves everything (Priority: P1)

The GM quits the REPL with rolls unannotated. Those rolls are written anyway, annotation or not,
because losing them is worse than recording them bare.

**Why this priority**: The opposite ruling from Story 2, for the one case where refusing would
destroy data. It must not be possible for the two rules to be confused.

**Independent Test**: With unannotated rolls held, the exit path writes them; the manual path does
not.

**Acceptance Scenarios**:

1. **Given** unannotated rolls, **When** the interpreter exits, **Then** they are written.
2. **Given** unannotated rolls, **When** the exit path writes them, **Then** it says that it saved
   unannotated rolls, so the GM knows the record has bare entries in it.

---

### User Story 4 - annotate() (Priority: P1)

The GM runs `annotate()` and is shown the rolls awaiting annotation. They pick one, say whether it
was open or contested, and describe what it was for. A contested roll is paired with one of the
GM's own recorded rolls, including one made before the conversation opened.

**Why this priority**: Nothing above works without it - it is the only way a roll becomes
annotated.

**Independent Test**: Drive the menu with scripted answers and assert the resulting annotation.

**Acceptance Scenarios**:

1. **Given** several unannotated rolls, **When** `annotate()` runs, **Then** the GM chooses which
   one to annotate first.
2. **Given** exactly one unannotated roll, **When** `annotate()` runs, **Then** it goes straight to
   that roll without asking which.
3. **Given** the GM chooses "contested", **When** prompted, **Then** they choose one of the GM's
   own recorded rolls as the opposing side, are offered a per-side bonus defaulted from the inferred
   skill difference, and the result records both totals AFTER THEIR OWN BONUSES, the winner and the
   margin.
4. **Given** a roll made in error, **When** the GM chooses to discard it, **Then** it is never
   written, is not offered again, and does not hold the conversation open.
5. **Given** the GM presses Ctrl-C at any point, **When** the menu exits, **Then** NOTHING is
   annotated or discarded, including anything answered earlier in that session of the menu.
6. **Given** no rolls are awaiting annotation, **When** `annotate()` runs, **Then** it says so and
   does nothing.

---

### User Story 5 - The GM's own rolls are captured with their bonuses (Priority: P2)

The GM rolls for the NPC in the REPL as they always have - `xky(7, 4) + 8`. While a conversation is
that roll and its bonus are remembered so `annotate()` can offer it as the opposing side of a
contest - whether or not a conversation was open when it was made, since rolling the NPC's side
first is the GM's most common order. A bonus decided AFTER seeing the dice, as several schools allow, is added by ordinary
arithmetic on the REPL's `_` - `_ + 15` - which updates the same recorded roll.

**Why this priority**: Contested annotation depends on it, but open annotation does not, so it
follows Story 4.

**Independent Test**: `xky(7, 4) + 8` leaves a recorded roll whose total includes the 8; with no
conversation open, the roll is still recorded and remains available to `annotate()`.

**Acceptance Scenarios**:

1. **Given** an open conversation, **When** the GM evaluates `xky(7, 4) + 8`, **Then** a roll is
   recorded whose total is the kept dice plus 8.
2. **Given** no open conversation, **When** the GM evaluates `xky(7, 4) + 8`, **Then** the roll is
   recorded into the pre-conversation buffer and is offered by `annotate()` once a conversation
   opens.
3. **Given** a recorded roll, **When** the GM evaluates `_ + 15` at the prompt, **Then** that
   roll's recorded total increases by 15 and NO second roll is recorded.
4. **Given** the GM's habitual syntax must keep working, **When** `xky` is called, **Then** its
   return value still behaves as an integer everywhere it is used today.

---

### User Story 6 - The record reads as a sequence (Priority: P2)

Annotated rolls appear in the order they were made, so the GM or a player reading the record later
can follow the conversation.

**Why this priority**: The GM's stated reason for wanting annotation at all, but it is a rendering
concern that depends on everything above.

**Acceptance Scenarios**:

1. **Given** three annotated rolls made in a known order, **When** they are written, **Then** they
   appear in that order.
2. **Given** a round of Etiquette rolls, **When** they are written, **Then** they remain ONE line
   ordered highest-first, as feature 201 established.

---

### Edge Cases

- A roll annotated twice: the second annotation replaces the first.
- A contested annotation when the GM has made no rolls: the menu says so and offers open instead.
- A pre-conversation roll older than the buffer's bound is no longer offered; `annotate()` shows
  the candidates it still has rather than failing.
- A roll the GM discards is never written, never offered again, and does not hold the conversation
  open.
- `annotate()` with no conversation open: an error naming the situation, not a traceback.
- An unparseable menu answer: re-ask rather than crash or guess.
- A roll already written to Obsidian Portal that is then annotated: the record is updated in place,
  as feature 201's rewrite already does.
- Ctrl-C during the description prompt: the same as Ctrl-C anywhere else - nothing is saved.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A roll of any skill other than Etiquette MUST NOT be written to Obsidian Portal until
  it has been annotated, except by the exit path in FR-005.
- **FR-002**: Etiquette rolls MUST be written without annotation, exactly as they are today,
  because they are presumed to be introductions.
- **FR-003**: `end_conversation()` called by the GM MUST raise when unannotated NON-ETIQUETTE
  rolls are HELD - that is, rolls that require annotation under FR-001, collected in the open
  conversation and not yet written - naming them, and MUST leave the conversation open.

  This narrows feature 201's FR-019 for the unannotated case only. `end_conversation()` still writes
  immediately with no confirmation step when every held roll is annotated or Etiquette; the raise is
  a MISSING-INPUT failure, not an approval gate. The GM ruled on that distinction directly
  (2026-08-29): *"I understand that this is different than what I wanted for that other skill, but I
  think it makes sense here. So please accept my ruling and judgment that it is indeed something
  which should gate the end of a conversation when I call the end conversation function manually and
  there are still non annotated rolls."*
- **FR-004**: A conversation holding only annotated and/or Etiquette rolls MUST close normally.
- **FR-005**: The interpreter-exit path - the SAME `end_conversation()`, invoked from the exit hook
  rather than by the GM - MUST write unannotated rolls rather than lose them, and MUST report that it
  did so (see Assumptions - the report is an addition beyond the request). One function, so the exit
  path cannot drift from the formatting the manual path produces.
- **FR-006**: `annotate()` MUST present the rolls awaiting annotation and let the GM choose one when
  there is more than one.
- **FR-007**: `annotate()` MUST let the GM mark a roll open or contested and MUST take a free-text
  description of what the roll was for.
- **FR-008**: A contested annotation MUST let the GM choose one of the GM's own RECORDED rolls -
  including those made before the conversation opened, per FR-011 - as the opposing side, and MUST
  record both totals, the winner and the margin per feature 201's rules.
- **FR-009**: Ctrl-C anywhere in `annotate()` MUST abandon the whole menu session, saving nothing -
  including answers given earlier in that session.
- **FR-010**: While a conversation is open, `xky` MUST record its result as ONE roll, and any bonus
  later added to that value by ordinary arithmetic - in the same expression, as in the GM's habitual
  `xky(7, 4) + 8`, or afterwards once the dice are seen, as in `_ + 15` - MUST UPDATE that same
  recorded roll's total rather than record a new one.
- **FR-011**: `xky` MUST record its result whether or not a conversation is open, into a bounded
  rolling buffer, and `annotate()` MUST offer recent rolls made BEFORE the conversation opened.
  **This REVERSES the original FR-011** ("with no conversation open, `xky` MUST record nothing"),
  which was faithful to the GM's first statement and wrong about their actual workflow
  (2026-08-29): *"I would like to be able to roll the NPCs side before opening. That is actually the
  most common workflow is that by the time I go to annotate something, I have already made the
  role."* The buffer is bounded so it cannot grow without limit across a long session.
- **FR-012**: `xky`'s return value MUST remain usable as an integer everywhere it is used today.
- **FR-013**: A bonus decided after seeing the dice MUST be applied by ordinary arithmetic on the
  returned value (`_ + 15`) per FR-010; no separate function is required. This
  REPLACES the `apply_bonus_to_previous_roll()` function the GM originally proposed, at their own
  suggestion (2026-08-29): *"it also allows me to be able to do `_ + 15` as the mechanism For
  applying a bonus after seeing the results of the role, which is perfect. that can be the thing
  that we do instead of the `apply_bonus_to_previous_roll()` function, which is even better."*
- **FR-014**: Annotated rolls MUST be written in the order they were made.
- **FR-015**: A round of Etiquette rolls MUST remain one line, highest-first, unchanged from
  feature 201.
- **FR-016**: An annotated roll's description MUST appear with it in the record.
- **FR-017**: `annotate()` MUST let the GM DISCARD a roll made in error. A discarded roll is never
  written, never offered again, and does not block `end_conversation()`.
- **FR-018**: When a roll is marked contested, `annotate()` MUST offer a bonus for EACH SIDE
  separately, defaulting to the free raises the rules grant - *"you get a free raise for every point
  your character's skill is higher than your opponent's"* (`rules/02-skills.md:64`), each raise
  adding 5 (line 66). The GM MUST be able to override either value.
- **FR-019**: The default free raises MUST be inferred from the two rolls: a skill roll is
  `(Ring + skill)k(Ring)`, so the skill is the difference between dice rolled and dice kept (a `7k4`
  Law roll implies Law 3). The player's rank, when the character-sheet app supplied one, is EXACT
  and MUST be preferred over the inference. The inference is explicitly unreliable - the GM: *"This
  is not completely reliable because there are things that can cause extra dice to be rolled"* -
  which is why FR-018 requires the override. The inference MUST use the pool the GM ASKED for, not
  the post-cap pool, since `actual_xky` converts dice above ten into a flat bonus.
- **FR-020**: Bonuses MUST be recorded and applied PER SIDE, never netted into one number. The GM's
  reason: *"a player whose Opponent received two free raises should not have this reflected by
  having minus ten applied to their own role because the value of their own role is still
  significant in and of itself. It makes a difference whether they got a 30 or a 40."* A bonus to
  the NPC raises the NPC's total; it never lowers the player's.

### Key Entities

- **Annotation**: what a roll was for (free text), whether it was open or contested, and for a
  contested roll the opposing GM roll.
- **GM roll**: a roll the GM made in the REPL, whether or not a conversation was open - the dice,
  the pool as ASKED for (before the ten-die cap, which the skill inference needs), the total
  including bonuses, and when it happened.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A record written by this feature lets the GM reconstruct what each non-Etiquette roll
  was for, without opening Discord.
- **SC-002**: No unannotated non-Etiquette roll reaches Obsidian Portal except via the exit path.
- **SC-003**: Annotating a roll takes one call. The OPEN path takes three answers - which roll,
  open, and the description. The CONTESTED path takes at most six, the two extra being one bonus per
  side, each pre-filled with the inferred default so that accepting both is a keypress.
- **SC-004**: The GM's existing `xky` habits keep working unchanged, including in code that uses
  the return value arithmetically.
- **SC-005**: Ctrl-C out of the menu leaves the conversation exactly as it was.
- **SC-006**: A roll of the NPC's side made BEFORE `begin_conversation` is offered as an opposing
  roll, because that is the GM's most common order of operations.
- **SC-007**: A contested roll's recorded totals show each side after ITS OWN bonuses, and a
  player's own total is never reduced by a bonus their opponent received.

## Assumptions

- **The output format for an annotated roll is not specified by the GM.** Chosen to extend feature
  201's established shapes: `Jimen law: 40 - assessing whether the arrest was lawful` for an open
  roll, and `Jimen vs Otsuki sincerity: 41 vs 28, Jimen by 10 - claiming he never met the man` for a
  contested one. Trivially adjustable and flagged for the GM.
- **The GM's `xky(7, 4) + 8` form is captured by making `xky` return an int subclass that records
  the result of arithmetic done on it**, rather than by reading the REPL history. The GM offered the
  history as one option and `xky(7, 4, 8)` as another, and said *"maybe it is not actually
  necessary"*. The subclass keeps their habitual syntax working with no new argument and no
  dependence on readline, which a piped or scripted invocation does not have.
- Etiquette is the only skill exempt from annotation, because it is the only one the GM named.
  Further exemptions are a data change if they ever want one.
- `annotate()` loops until the GM stops or nothing is left, rather than annotating exactly one roll
  per call, because rolls arrive in rounds. Combined with FR-009 this means one Ctrl-C discards every
  annotation completed in that run - the literal reading of *"having that not save anything"*, and
  the pairing most likely to surprise in use. Flagged for the GM.
- **The exit path's report in FR-005 is an ADDITION beyond the GM's request**, kept so the GM knows
  the record contains bare entries. To be raised with the GM once the implementation works, per
  constitution Principle XVI - the same treatment feature 201 gave its abandon call.
- **`xky` now always returns the recording subclass**, since FR-011 was reversed. The earlier
  design returned a plain `int` outside a conversation, which had the pleasant property that no
  other code path could mutate a record by doing arithmetic on a roll. That property is GONE,
  deliberately, and the cost is bounded: a stray bonus lands on a buffer entry only `annotate()`
  reads, and the GM sees each candidate's current total when choosing one.
- **The contested bonus prompt shows the inferred default and takes an override per side** - two
  numbers, not one net number, per FR-020.
- **Preferring the character-sheet's exact rank over the dice inference in FR-019 is an ADDITION
  beyond the request.** The GM asked for a default *"based on the two rolls that were made"* and gave
  the dice inference as the method; feature 201 already carries a stated rank on the roll, so the
  exact value is to hand and using it serves the GM's own reason for wanting an override - that the
  inference *"is not completely reliable"*. To be raised with the GM once the implementation works,
  the same treatment FR-005's report clause got.
- **The pre-conversation buffer holds the last 20 rolls.** The GM's own framing is *"recently"*, so
  any reasonable bound satisfies the request; naming it here stops a later session inventing a
  different one and calling it a fix. Twenty is several minutes of a GM rolling steadily, and an
  older candidate is one the GM would not recognize in the menu anyway.
- Subtraction is captured as well as addition, so `xky(5, 2) - 5` records a penalty rather than
  silently dropping it. Not requested; it falls out of the same mechanism and would be surprising by
  its absence.

## Review history

**Round 1** (2026-08-29, `spec-fidelity` Mode 2, independent of the author): **CHANGES REQUIRED.**
Question 1 passed on every clause. Question 2 found three things:

1. **FR-003 contradicted FR-004 in a state the GM's own rules permit.** Etiquette rolls are
   unannotated BY DESIGN, and under feature 201's debounced watcher the last round of them may be
   unwritten when the GM closes - so a conversation holding an annotated Precepts roll plus an
   unwritten Etiquette roll satisfied both "MUST close normally" and "MUST raise". Resolving that
   the wrong way would have made Etiquette block the close, narrowing the exemption the GM stated
   plainly. Scoped to rolls that REQUIRE annotation, with "held" defined at first use.
2. **FR-005's "MUST report that it did so" was unrequested** - the GM's words on the exit path are
   complete without it. Kept, and recorded in Assumptions as an addition to raise with the GM.
3. **The spec did not reconcile FR-003 with feature 201's FR-019** ("MUST write immediately, with no
   confirmation step"), leaving two conflicting MUSTs on one function for whoever implements it. The
   supersession is now written down rather than inferred.

The reviewer explicitly CLEARED three things a later reviewer should not reopen: FR-003 is not a
forbidden pre-review gate (it is a missing-INPUT failure, which CLAUDE.md's own rule carves out, and
the GM ruled on it directly); the `xky` int-subclass is a legitimate implementation decision because
the GM's binding statement was an outcome - keep `xky(7, 4) + 8` working - while both mechanisms they
named were hedged; and the invented output format is unavoidable gap-filling since FR-016 requires
some format and the GM specified none.

One item referred to the GM rather than changed: FR-011 means a GM roll made BEFORE
`begin_conversation` is not offered as a contested opponent, while the GM's own example says *"I have
recently done this in the Python REPL"*. Faithful to what they asked; worth confirming once it works.

**Round 2** (2026-08-29): three of the four findings were re-listed as outstanding against text that
had already been amended. Each was VERIFIED against the file on disk rather than taken on either
party's word - the lesson from feature 201, where a scripted edit failed its own assert inside a
backgrounded command and the failure went unread. One finding was genuinely new and correct:

4. **With FR-013 folded into the arithmetic, FR-010 did not say that later arithmetic UPDATES the
   existing record rather than creating a second one.** Implicit while a named function owned the
   after-the-fact bonus; once `_ + 15` became the whole mechanism, nothing in the spec said it, and
   `xky(7, 4) + 8` could plausibly have been implemented as two recorded rolls. Now stated in FR-010
   and pinned by US5 scenario 3, which would fail on the two-record implementation.

The reviewer also refined FR-005 to name the mechanism the GM stated - the exit hook calls the SAME
`end_conversation()` - so the exit path cannot drift from the manual path's formatting. It notes
that FR-003 ("called by the GM") and FR-005 ("invoked from the exit hook rather than by the GM") now
state the distinguishing condition on both sides, making the raise-on-manual / save-on-exit split
"impossible to read as harmonized". That split was the highest-risk part of this spec, because the
two rules contradict each other by design.

**Round 5** (2026-08-29, after first use): the GM returned three follow-up requirements, recorded
verbatim in `gm-request.md`. One REVERSES FR-011 - the original was faithful to their first
statement and wrong about their actual workflow, which is the kind of error only using the thing
finds. FR-017 to FR-020 and SC-007/SC-008 are new. Pending review.

**Round 4** (2026-08-29, a SECOND reviewer with no prior context, asked to judge the current file on
its merits rather than defer): **FAITHFUL.** It reached the round-1 clearances independently from the
request text - *"I would have cleared them on first read"* - and found no finding the earlier rounds
missed. Two non-blocking items it raised are now fixed: `gm-request.md` did not contain the two later
GM statements the spec quotes, so FR-013's authority could not be checked against the primary record
(both appended verbatim); and SC-003 said "at most three answers" while the contested path needs four
(corrected). Its reason for wanting the first is worth keeping: a quote a future reviewer cannot
check is worth less than one they can.

**Round 3** (2026-08-29, after an explicit instruction to re-read from disk; the reviewer recorded
the file's md5): **FAITHFUL - implement it.**

FR-010, FR-013, US5 scenario 3 and FR-005 all judged correct, with nothing else moved. In fairness
to the reviewer, it pushed back on the paragraph above: its intermediate report had recorded three of
the four as accepted and listed only the fourth. Both readings are of different reports in the same
exchange, and it explicitly declined to make the correction a condition. Recorded here in its words
rather than the author's, since a review history written by the author is worth less than one that
survives the reviewer reading it.

One item stays REFERRED TO THE GM, unresolved by three rounds because it is theirs to answer: FR-011
means a GM roll made just BEFORE `begin_conversation` is not offered as a contested opponent, while
the GM's own example describes rolling the NPC's side beforehand (*"I have recently done this in the
Python REPL"*). Faithful to what they asked for; possibly not what they do. To confirm in testing.

**Round 5 verdict** (2026-08-29, `spec-fidelity` on the amendment): **CHANGES REQUIRED**, seven
findings, all applied. Both questions passed on the three new requirements themselves; every failure
was one thing.

**FR-011 was reversed in exactly one place and left standing in five others.** US5's Independent
Test and acceptance scenario 2 still asserted that nothing is recorded outside a conversation - as a
TEST, so a faithful implementation of the amended FR-011 would have failed it. An Edge Case still
said a pre-conversation roll "is not offered". Key Entities still defined a GM roll as one made
"while a conversation was open". FR-008 still restricted the contested opponent to rolls "made
during the conversation" - two MUSTs with opposite scopes on one behavior. The reviewer's summary:
*"not caution, it is an unfinished sweep"*.

Also found and fixed: SC-003 was stale - the contested path is six answers now, not four, so the
GM's own follow-up request had quietly made their own success criterion unachievable; US4 had no
discard scenario; the SC list skipped SC-006; and FR-019's preference for the character-sheet's exact
rank over the dice inference is an unrequested addition, now recorded in Assumptions as one. The
pre-conversation buffer's bound is named there too, so a later session does not invent a different
one and call it a fix.

**The lesson worth keeping: a reversal is a SWEEP, not an edit.** Reversing a requirement means
finding every place the old rule was asserted - especially acceptance scenarios, which read as tests
and get implemented as tests. Grepping for the requirement's number would not have found any of the
five: the old rule was restated in prose four times without once naming FR-011.
