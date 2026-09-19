# Feature Specification: Roll modes - what each skill may be, and what stays hidden

**Feature Directory**: `specs/207-roll-modes`

**Created**: 2026-09-19

**Status**: Draft - SCOPE STILL OPEN. The GM (2026-09-19): *"I have more things that I want the
feature to cover, so do not begin the implementation yet."* No plan, tasks or code until the GM
closes the scope.

**Input**: GM request 2026-09-19, reproduced verbatim in [gm-request.md](gm-request.md) with the
session's questions and the GM's answers. Builds on feature 201 (roll capture), 202 (annotation)
and 206 (interrogation lines), and REPLACES part of 206 - see "What this changes in feature 206".

## Why

`annotate()` asks the same question of every roll - open, contested, discard, or open with a bonus
- and for most skills most of those answers are impossible or nearly so. Pontificate can only be
open. Manipulation can only be contested. History is open nineteen times in twenty. The GM answers
the question anyway, in the busiest moment of the session.

Separately, two skills have an opposing roll the players must never see. Feature 206 handled
Interrogation by recording the NPC's Sincerity roll NOWHERE. The GM now wants it kept - out of the
players' sight - and wants the public record to say what the players GOT from the roll, because
that is what they will want to look up later. Acting is the same shape: the NPC may see through a
disguise and not let on, so the opposing roll is hidden and the public record carries an outcome.

## The modes

Every rollable skill or knack has exactly one mode. It decides what `annotate()` asks.

| mode | members | what the GM is asked |
|---|---|---|
| ALWAYS OPEN | athletics, pontificate | what it was for |
| ALWAYS CONTESTED, opposing roll REQUIRED | manipulation (vs tact) | which opposing roll - or the 15 default - then bonuses, then what it was for |
| ALWAYS CONTESTED, MAY BE UNOPPOSED | sneaking (vs investigation) | which opposing roll, or "nobody opposed it"; then what it was for |
| HIDDEN OPPOSITION | interrogation (vs sincerity), acting (vs investigation) | never shown an o/c choice; see their own stories |
| DEFAULT OPEN | bragging, intimidation, culture, heraldry, history, underworld, investigation | what it was for, with open already selected and a way to undo it |
| FULL MENU | every other skill (sincerity, tact, law, precepts, strategy, commerce, ...) | today's `o/c/d/ob` question, unchanged |
| EXEMPT | etiquette | nothing (feature 202) |

A player rolling sincerity, tact or investigation is NOT presumed contested: the GM (message 2)
ruled that each has common open uses, and moved investigation to DEFAULT OPEN.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Skills that can only be open are never asked (Priority: P1)

A player rolls athletics or pontificate. `annotate()` does not ask open-or-contested; it asks what
the roll was for and writes an open line.

**Independent Test**: Annotate a pontificate roll; the only question is what it was for.

**Acceptance Scenarios**:

1. **Given** a captured pontificate roll, **When** annotated, **Then** contested is never offered
   and the written line is today's open line.
2. **Given** an athletics roll that had a bonus or was a mistake, **When** the GM answers the
   what-was-it-for prompt with a bare `ob` or `d`, **Then** it is handled as open-with-bonus or
   discard, exactly as those work today.

### User Story 2 - Pontificate and athletics are captured at all (Priority: P1)

Measured 2026-09-19: `31 pontificate`, `25 athletics` and the bot's
`**Roll Tester**: **23** Pontificate@2` all parse to NOTHING today, because the roll vocabulary is
read only from the skill list and both are school knacks. The GM: *"They definitely can be made,
and they can be captured. So we should make sure that we are capturing them."*

**Acceptance Scenarios**:

1. **Given** a typed or bot-posted pontificate or athletics roll, **When** the conversation
   collects it, **Then** it is captured like any skill roll.
2. **Given** the corpus sweep of real messages, **When** the vocabulary grows, **Then** every
   change in the number of rolls found is individually read and explained before the pinned count
   moves (it is a regression fixture).

### User Story 3 - Default-open skills arrive with open selected, and the GM can undo it (Priority: P1)

A player rolls history. The GM is not asked the kind; the prompt reads as open and asks what it was
for. Nothing is pre-entered that a bare Enter would accept - an empty answer re-asks (or finishes,
as blank does today). To make it contested instead, the GM undoes the selection.

**The undo is a KEYSTROKE** (GM, message 4: *"I would really like to have keystrokes detected"*).
With the line still empty, pressing Backspace or Left Arrow undoes the selection and the full
`o/c/d/ob` question is asked instead. The session first proposed a typed answer on the grounds that
readline cannot call back into Python on a key; that is true of readline and beside the point,
because the key can be read from the terminal BEFORE readline is handed the line: the prompt is
printed, one key is read with the terminal in cbreak mode, and then either the selection is undone
or that key is fed back as the first character of an ordinary readline-edited line. So the note
keeps full line editing and the quiet-history behavior (2026-09-09).

**One accepted limit, recorded so it is not mistaken for a bug**: the undo is recognized only while
NOTHING has been typed. Once a character is in, the line belongs to readline, and deleting back to
empty and pressing Backspace again does nothing. Lifting that means replacing readline for these
prompts (a full line editor such as prompt_toolkit), which was priced and declined as far more
machinery than the case deserves. **One press, not the GM's floated two**: on an empty line
Backspace and Left Arrow have no other meaning, so a second press would buy nothing - one constant
to change if an accidental undo ever happens in play.

Where there is no terminal (a pipe, the tests), the key read is skipped and a bare `c`, `ob` or `d`
as the whole answer switches kind; that typed form also works at a terminal.

**Acceptance Scenarios**:

1. **Given** a history roll, **When** the GM types a note, **Then** it is written as an open line
   with one answer given, and the first character typed is not lost.
2. **Given** a history roll and an empty line, **When** the GM presses Backspace or Left Arrow,
   **Then** the full kind question is asked and `c` runs the contested flow exactly as today.
3. **Given** an investigation roll, **Then** it behaves as history does.
4. **Given** a pasted note, or one starting with a non-ASCII character, **Then** it arrives whole.
5. **Given** Ctrl-C at the key read, **Then** it abandons the run exactly as at any other prompt.

### User Story 4 - Manipulation always has an opposing tact roll, 15 by default (Priority: P1)

Manipulation goes straight to the opposing-roll picker. The picker lists the GM's recent rolls and
one more entry: **15, no roll made** - the value someone gets who is not actively rolling. Choosing
it presumes the NPC's tact is ZERO, so the default bonus to the manipulator is their full rank in
free raises. The entry is offered even when the GM has no recent rolls (today that case silently
falls back to open, which for manipulation is wrong).

**Acceptance Scenarios**:

1. **Given** a manipulation roll at rank 3 and the GM picks "15", **Then** the contest is against
   15 with a default bonus of +15 to the manipulator and +0 to the NPC, both overridable.
2. **Given** a manipulation roll, **Then** neither open nor "unopposed" is offered. Discard is.

### User Story 5 - Sneaking is always contested but may have nobody opposing it (Priority: P1)

Sneaking goes straight to the picker, which carries an entry for **nobody opposed it**. Unopposed,
the roll is written like an open line, rounded down to 5, with no marker:
`25 sneaking: Jimen - blending into the crowd` (GM-confirmed, message 3).

**Acceptance Scenarios**:

1. **Given** a sneaking roll and an opposing investigation roll, **Then** the contested line is
   written as today (both skills named, investigation takes a tie).
2. **Given** a sneaking roll and "nobody opposed it", **Then** the open-shaped line is written.

### User Story 6 - A line of questioning is declared by the GM, with the hidden Sincerity roll (Priority: P1)

The GM calls `new_line_of_questioning("Fumitake's contributions to the Wasp treasury",
xky(8, 3) + 10)` - normally BEFORE the players roll, since players ask whether it is a new line
before rolling again. Interrogation rolls made AFTER that call and before the next one belong to
that line.

**Earlier rolls are never pulled in silently; the GM is asked about each** (message 4). When the
function is called and there are PREVIOUS interrogation rolls that might belong to the new line, it
prompts once per roll: part of this line, or discard. Two kinds of roll qualify, and no others:

- a roll on NO line yet - the case the GM named, a player rolling before the first declaration;
- a REPEAT roll on the line being left - a PC's second or later roll there. The skill is rolled
  once per line of questioning, so a second roll is either the new topic's roll made early or a
  mistake. Joining is the default answer; a PC's FIRST roll on the old line is never asked about.

The Sincerity roll is optional - the GM does not roll it when the NPC is simply telling the truth - and
the public record MUST look the same either way.

The public line groups the rollers as Etiquette does, but exact and ranked, and ends with what they
got:

```
interrogation: 37@2 Jimen / 24@1 Moriko - Fumitake's contributions to the Wasp treasury: nothing hidden detected
```

**Acceptance Scenarios**:

1. **Given** one line declared and two interrogation rolls after it, **Then** one public line
   lists both, highest first, with the default outcome.
2. **Given** a roll captured before the first `new_line_of_questioning` call, **When** the GM
   makes that call, **Then** they are asked whether the roll joins the line or is discarded, and
   it is never attached without being asked.
2a. **Given** Jimen has rolled twice on the current line, **When** the GM declares a new line,
   **Then** they are asked about Jimen's second roll only, with joining the new line the default.
3. **Given** two lines declared, **Then** rolls go to the line that was current when each was
   made, and two public lines are written.
4. **Given** a line declared with no Sincerity roll, **Then** the public line is identical in
   shape and default outcome to one declared with a roll.
5. **Given** any of the above, **Then** the Sincerity total, the margin and the winner appear
   nowhere in the public bio.

### User Story 7 - A PC who detects something is split out, even long after the roll (Priority: P1)

Free raises build over a line of questioning, so who detected what is often settled after the roll
was captured and written. The GM calls something like `detected("Jimen", "he is lying about the
amount")` at any point while the conversation is open. That interrogator leaves the group and gets
their own line under the same label, with the GM's words as the outcome:

```
interrogation: 24@1 Moriko - Fumitake's contributions to the Wasp treasury: nothing hidden detected
interrogation: 37@2 Jimen - Fumitake's contributions to the Wasp treasury: he is lying about the amount
```

**Acceptance Scenarios**:

1. **Given** a written line with two rollers, **When** the GM marks one as having detected
   something, **Then** the record is rewritten with that roller on their own line.
2. **Given** every roller on a line detected the same thing, **Then** they stay grouped on one
   line carrying that outcome.
3. **Given** the PC rolled on several lines, **Then** the GM can say which line is meant, and the
   current line is the default.

### User Story 7a - Grilling, declared up front or part way through (Priority: P1)

The rules give the NPC 2 free raises when the interrogator is speaking casually rather than
grilling. A line is NOT grilling unless the GM says so: `new_line_of_questioning(description, roll,
grilling=True)`. When a player starts grilling midway, the GM calls `grilling()`: the current line
becomes a grilling line, the casual-conversation raises the NPC had been given are taken back
RETROACTIVELY for every roll on the line, the private comparisons are printed again with the new
numbers, and the public line gains `(grilling)`. A second `grilling()` on the same line changes
nothing and says that grilling was already recorded.

**Acceptance Scenarios**:

1. **Given** a line declared without `grilling`, **Then** the NPC's side of every private
   comparison carries the 2 casual free raises and the public line has no `(grilling)`.
2. **Given** `grilling()` is called after two rolls, **Then** both comparisons are recomputed
   without those raises and reprinted, and the public line is rewritten with `(grilling)`.
3. **Given** `grilling()` is called again on that line, **Then** a message says it was already
   recorded and nothing else happens.
4. **Given** `grilling()` with no line declared, **Then** an error says to declare one first.

---

### User Story 8 - The repl tells the GM, privately, how the contest stands (Priority: P2)

With the Sincerity roll in hand the repl can work out the free raises. The NPC's Sincerity rank is
INFERRED from the roll's dice: rolled minus kept, minus one more when the NPC's Obsidian Portal
record names a school that rolls an extra die on sincerity. Today those are Merchant and Shosuro
Actor; the list is READ from the rules' school text, not written into the code. (Schools whose
first Dan lets the player CHOOSE the extra die are deliberately ignored - the GM: *"I don't think
that that will actually come up in practice."*) The interrogator's rank comes from the roll.

As each interrogation roll arrives the repl prints the comparison in the GM's terminal, e.g.
`Jimen 37 (+5) vs sincerity 38: not detected`. The terminal is never screen-shared (GM, message 3).
**This is advisory**: it does not set the public outcome, which stays the default until the GM
marks a detection - situational raises and raises built over the line live in the GM's head.

**Acceptance Scenarios**:

1. **Given** an NPC whose record names the Merchant school rolling 8k3 sincerity, **Then** their
   rank is taken as 4; for any other NPC, 5.
2. **Given** a line with no Sincerity roll, **Then** nothing is compared and nothing is printed
   about a contest.
3. **Given** a tie, **Then** interrogation takes it (feature 202's pairing rule).

### User Story 9 - Acting is always opposed, the opposing roll is hidden (Priority: P1)

Acting is contested against investigation (rules corrected 2026-09-19). `annotate()` always takes
an opposing investigation roll for it, and the players never see it. The public line is the exact
roll with its rank and an outcome, defaulting to the GM's *"no signs of your persona being seen
through"*:

```
acting: 32@1 Jimen - posing as a rice factor from Ryoko Owari: no signs of the persona being seen through
```

**Acceptance Scenarios**:

1. **Given** an acting roll, **Then** the GM is asked for the opposing roll, what it was for, and
   the outcome with the default offered; open and "unopposed" are never offered.
2. **Given** the written public line, **Then** it carries no opposing total, margin or winner, and
   the acting total is exact, not rounded.
3. **Given** the GM types a different outcome, **Then** that text is written instead.

### User Story 10 - Hidden numbers go to the GM-only notes, never the bio (Priority: P1)

Every hidden opposing roll - the Sincerity roll of each line of questioning, the investigation roll
against each acting roll - is recorded in the NPC's GM-only notes in its own labeled block, the way
Discern Honor keeps one, with enough beside it to read later: what it opposed, the label, the
totals, who won. It is rewritten in place as the conversation goes, never stacked.

**Acceptance Scenarios**:

1. **Given** a line declared with a Sincerity roll, **Then** the GM-only block gains an entry and
   the public bio gains none of its numbers.
2. **Given** the block already exists from an earlier conversation, **Then** new entries are added
   and old ones are untouched.
3. **Given** the GM-only write fails, **Then** the public write still happens and the failure is
   reported in the terminal.

### Edge Cases

- An interrogation roll arrives and `new_line_of_questioning` is never called: the roll is held,
  `end_conversation()` refuses as it does for any unannotated roll, and the message names the
  function. The interpreter-exit path writes it bare, as feature 206 specifies.
- A typed interrogation or acting roll has no recorded rank: `annotate()` asks for the rank and
  nothing else (206's FR-007); until then the roll is written without `@N`.
- A roll marked as a detection and later discarded leaves no line behind.
- `detected()` names a PC with no interrogation roll in the conversation: an error naming the PCs
  who have one.
- Ctrl-C in `annotate()` still abandons everything staged in that run. `new_line_of_questioning`
  and `detected` take effect when called; they are not part of a staged run.

## What this changes in feature 206

- KEPT: written alone, exact, `@rank`, grouped per line, highest first, no bonus on the public
  line, `(grilling)` as the one public flag, the bare exit-path line.
- REPLACED: the join-which-line menu in `annotate()`. Lines are declared by function and rolls
  attach by time.
- REVERSED, by the GM: 206's rule that the Sincerity total is *"written nowhere"*. It is now
  written to the GM-only notes. The PUBLIC half of that rule is unchanged and is SC-001 here.
- NEW on the public line: the outcome after the label.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every name in the roll vocabulary MUST have exactly one mode, and a test MUST fail
  when a vocabulary entry has none - the table cannot silently fall behind the rules.
- **FR-002**: The roll vocabulary MUST include the rollable school knacks, at minimum pontificate
  and athletics, READ from the rules repository like the skills are.
- **FR-003**: ALWAYS OPEN skills MUST never be offered contested. Open-with-bonus and discard MUST
  stay reachable.
- **FR-004**: DEFAULT OPEN skills MUST skip the kind question with open selected and MUST NOT
  accept a bare Enter as a note. At a terminal, Backspace or Left Arrow on the still-empty line MUST
  undo the selection and ask the full kind question; any other first key MUST become the first
  character of a normally edited line. Without a terminal the typed `c` / `ob` / `d` form MUST work.
- **FR-005**: Manipulation MUST always be written as a contest. Its picker MUST offer "15, no roll
  made" whether or not the GM has recent rolls, and choosing it MUST presume an opposing rank of 0.
- **FR-006**: Sneaking MUST never be offered open. Its picker MUST offer "nobody opposed it", which
  MUST write the open-shaped line rounded down to 5 with no marker.
- **FR-007**: `new_line_of_questioning(description[, sincerity roll][, grilling=False])` MUST open
  a line of questioning in the open conversation. Interrogation rolls attach to the line current
  when they were MADE (message time, not capture time).
- **FR-007a**: On that call the GM MUST be prompted, once per roll, about every interrogation roll
  on no line and every REPEAT roll by the same PC on the line being left: part of the new line, or
  discard. No earlier roll may join a line without being asked about, and no other roll is asked
  about.
- **FR-007b**: `grilling()` MUST mark the current line as grilling, remove the casual-conversation
  free raises from the NPC's side for every roll on the line, reprint the comparisons, and rewrite
  the public line with `(grilling)`. Called again on the same line it MUST change nothing and say
  so.
- **FR-008**: A line's public form MUST be
  `interrogation[ (grilling)]: <roll>[@<rank>] <name> / ... - <description>: <outcome>`, with the
  default outcome `nothing hidden detected`, identical whether or not a Sincerity roll was given.
- **FR-009**: The GM MUST be able to mark an interrogator as having detected something, with their
  own words, at any time while the conversation is open, including after the roll was written.
  Rollers on a line are grouped BY OUTCOME: one written line per distinct outcome.
- **FR-010**: An interrogation roll attached to a declared line and carrying a rank MUST need no
  `annotate()` answer at all.
- **FR-011**: The NPC's Sincerity rank MUST be inferred as rolled minus kept dice, less one when
  the NPC's Obsidian Portal record names a school the rules give an extra sincerity die; that set
  MUST be derived from the rules text. An unreadable record MUST mean no adjustment, reported.
- **FR-012**: The repl MUST print the comparison for each interrogation roll on a line that has a
  Sincerity roll, to the terminal only. It MUST NOT change the public outcome.
- **FR-013**: Acting MUST always take an opposing investigation roll. Its public line MUST be
  `acting: <roll>[@<rank>] <name> - <note>: <outcome>`, exact, with the default outcome
  `no signs of the persona being seen through`, and MUST carry nothing of the opposing roll.
- **FR-014**: Every hidden opposing roll MUST be written to a labeled block in the NPC's GM-only
  notes and MUST NEVER be written to the bio. The block MUST be updated in place.
- **FR-015**: Everything else MUST be unchanged: Etiquette's line, the FULL MENU skills' prompts,
  the open and contested line shapes, per-side bonuses, Ctrl-C, quiet input, the two closing rules.

### Key Entities

- **Mode**: what a skill's roll may be - one per vocabulary entry.
- **Line of questioning**: a description, an optional hidden Sincerity roll, whether grilling, and
  the interrogation rolls made while it was current. Declared by the GM, not derived from a menu.
- **Outcome**: what the players got from a hidden-opposition roll, per roller; a default unless
  the GM says otherwise.
- **Hidden roll record**: the GM-only entry for one opposing roll the players must not see.

## Success Criteria *(mandatory)*

- **SC-001**: No Sincerity total, no investigation total opposing an acting roll, and no margin or
  winner derived from either, appears in any public bio this feature writes.
- **SC-002**: Annotating an always-open or default-open roll takes ONE answer.
- **SC-003**: An interrogation roll with a rank, on a declared line, takes ZERO `annotate()`
  answers.
- **SC-004**: A public interrogation line reads the same whether the NPC was truthful, lied
  successfully, or was never rolled for.
- **SC-005**: Pontificate and athletics rolls posted in any shape an existing skill parses in are
  captured.
- **SC-006**: Every hidden roll made in a conversation can be found afterwards in the NPC's GM-only
  notes.

## Assumptions

- The GM's terminal and the GM-only notes are never screen-shared (GM, message 3).
- The outcome wording is the GM's "something like" - the two defaults above are the session's
  tidied forms and are one constant each to change.
- A detection splits to its own line rather than being marked inline; the GM offered either.

## Resolved with the GM (message 4)

- Rolls that precede their line: prompted per roll at declaration, never silent (Story 6).
- Grilling: `grilling=False` by default, plus a retroactive `grilling()` (Story 7a).
- The undo is a real keystroke (Story 3).
- Acting's outcome needs NO change-it-later path: *"The worst case scenario is that I can just edit
  Obsidian Portal directly."*

## Open Questions (for the GM, before the scope closes)

1. **Who adds the casual-conversation raises - the GM or the tool?** In
   `new_line_of_questioning("Chizuru's death", xky(8, 3) + 10)`, is that `+ 10` the NPC's 2 casual
   free raises, already included by hand? `grilling()` can only "subtract the free raises which the
   NPC received" if the tool knows they are there. Proposed: the TOOL adds them to a non-grilling
   line, and whatever the GM adds to the roll is everything else (the unprovable-lie raises,
   situational ones). The wrong reading double-counts 10 silently, so this one is asked.

## Review history

- 2026-09-19: DRAFT, scope open. The independent `spec-fidelity` review (constitution XVI) runs
  when the GM closes the scope, against gm-request.md as it then stands; no verdict is recorded
  yet and nothing may be implemented until one is.
