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
machinery than the case deserves. **TWO presses, as the GM said** (messages 1 and 5 both say
"twice"): the first press prints a one-line hint that another undoes the selection, the second
undoes it, and any other key after the first press simply starts the note. The session had drafted
one press on the grounds that a second buys nothing on an empty line; the GM's wording is the spec,
and the count is one constant.

**The same undo applies to every default this feature selects** - the pre-paired opposing roll of
Story 14 as well as the open selection here.

Where there is no terminal (a pipe, the tests), the key read is skipped and a bare `c`, `ob` or `d`
as the whole answer switches kind; that typed form also works at a terminal.

**Acceptance Scenarios**:

1. **Given** a history roll, **When** the GM types a note, **Then** it is written as an open line
   with one answer given, and the first character typed is not lost.
2. **Given** a history roll and an empty line, **When** the GM presses Backspace or Left Arrow
   twice, **Then** the full kind question is asked and `c` runs the contested flow exactly as today.
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
record names a school that rolls an extra die on sincerity. (When the Sincerity roll was TAGGED or made
with `sincerity()`, the rank is the recorded one and nothing is inferred - Story 11.) Today those are Merchant and Shosuro
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

### User Story 11 - The GM says what an NPC roll was, and the NPC's numbers are remembered (Priority: P1)

The problem, in the GM's words: the players talk to someone, the GM makes a tact roll, and weeks of
real time later has to make another for the same NPC - *"I would like to use the same tact skill
and not have the NPC's tact vary from session to session."* Nobody remembers every skill of every
NPC, so the record does.

The GM tags a roll with the skill it was: `xky(8, 3) + 10 - sincerity`. The roll still returns its
total and still accepts further `+ N`. From the dice the tool reads the NPC's numbers - kept dice
are the RING the skill uses (tact is an Air skill, so `xky(5, 3) - tact` means Air 3) and rolled
minus kept is the skill RANK (tact 2) - less any extra die the NPC's school rolls on that skill
(Story 8's rule, generalized: every "roll one extra die on ..." line in the rules' school text, not
only sincerity's). Flat bonuses are not part of the inference. With nothing recorded for that skill
or ring, the values are recorded and the tool says so in one line. This is the common case.

The numbers live in a parsable block in the NPC's GM-ONLY notes - never the bio - fetched once when
the conversation begins. Later rolls are checked against the local copy at once, whether or not it
has been persisted yet; persisting rides the conversation's existing debounced write. Nothing else
is assumed to edit the block: one repl, one writer.

**One NPC at a time** (GM: *"perfectly fine for now ... to just assume that whoever we have begun
the conversation with is the only NPC whose skills are being rolled"*). A later feature will track
several; so the numbers are kept per NPC record and a tag never bakes in who rolled.

**Acceptance Scenarios**:

1. **Given** an open conversation and nothing recorded, **When** the GM enters `xky(5, 3) - tact`,
   **Then** Air 3 and tact 2 are recorded, reported in one line, and the expression still
   evaluates to the roll's total.
2. **Given** that, **When** the conversation's next write happens, **Then** the GM-only notes carry
   both values and the public bio carries neither.
3. **Given** a new conversation with the same NPC weeks later, **Then** the recorded values are
   there before the first roll.
4. **Given** an NPC whose record names a school with an extra die on sincerity, **Then**
   `xky(8, 3) - sincerity` records sincerity 4, not 5.
5. **Given** `xky(8, 3) + 10 - sincerity`, **Then** the `+ 10` changes the total and nothing else.

---

### User Story 12 - A roll that disagrees with the record stops and asks (Priority: P1)

When a tagged roll implies a different skill rank OR a different ring than what is recorded, the GM
is told both values and chooses: THE ROLL WAS A MISTAKE, or THE RECORD WAS WRONG. Ctrl-C at that
prompt is caught and means the first - the roll is marked as a mistake so it is never offered as an
opposing roll, the record is untouched, and the GM re-rolls. Choosing the second corrects the record
to what this roll implies and keeps the roll. The GM's example of a wrong record: an earlier roll
that silently included a void point's extra die.

**A third answer appears when a void point would explain it** (message 6). When the roll differs
from the record by EXACTLY 1k1 or 2k2 - the same one or two dice in both rolled and kept, above or
below - the prompt also offers, worded to the case: "This roll spent a void point" / "This roll
spent 2 void points" when the roll is above the record (the roll stands, the record is untouched),
or "The previous roll spent a void point" / "... 2 void points" when it is below (the roll stands
and the record comes down to what this roll says). Any other difference gets the two answers only.

**Acceptance Scenarios**:

1. **Given** tact 2 / Air 3 recorded, **When** the GM enters `xky(6, 3) - tact`, **Then** they are
   told the record says tact 2 and this roll says tact 3, and asked which is wrong.
2. **Given** the same record, **When** the GM enters `xky(6, 4) - tact`, **Then** the RING
   disagreement (Air 3 against Air 4) is reported and "This roll spent a void point" is offered;
   choosing it keeps the roll and leaves Air 3 / tact 2 recorded.
2a. **Given** Air 5 / tact 2 recorded, **When** the GM enters `xky(5, 3) - tact`, **Then** "The
   previous roll spent 2 void points" is offered, and choosing it records Air 3.
2b. **Given** a difference of 3k3, or of 1k0, **Then** no void point answer is offered.
3. **Given** that prompt, **When** the GM presses Ctrl-C, **Then** the repl does not exit or raise,
   the roll is marked a mistake, and the record is unchanged.
4. **Given** that prompt, **When** the GM says the record was wrong, **Then** the record takes the
   new value, in the local copy at once.

---

### User Story 13 - The skill names roll for the NPC (Priority: P1)

`sincerity`, `tact` and the rest are also callable:

- `tact()` rolls the NPC's tact from the record. Whatever is missing is asked for: the skill rank
  (0 to 5 inclusive) or the ring (2 to 6 inclusive), then recorded.
- `tact(2)` states the rank: checked against the record (Story 12), or recorded; the ring comes
  from the record or is asked for. Then it rolls.
- `tact(5, 3)` is exactly `xky(5, 3) - tact`, with the same recording and checks.
- `tact(vp)` spends a void point: one more rolled AND one more kept die, which the tool knows about
  and so does not mistake for a bigger ring. `tact(vp * 2)` spends two; `vp` combines with the
  other forms (`tact(2, vp)`).

**Acting and history are RECORDED, never rolled** (message 6). `acting(2)` and `history(3)` state
that the NPC has that rank and produce no roll, because what they are FOR on an NPC is the free
raises they hand to other skills - one per rank, +5 each, added by the tool to the NPC's roll and
shown in the printed line so the GM can see it happened:

| recorded | adds its free raises to the NPC's | NOT added (conditional - the GM adds by hand) |
|---|---|---|
| acting | sincerity, intimidation | sneaking (only when blending into a crowd) |
| history | law, strategy | culture (GM, message 6); heraldry (places, families and institutions only) |

With no argument, `acting()` / `history()` report the recorded rank, or ask for it. A disagreement
with a recorded rank asks the Story 12 question (no dice, so no void point answer).

Every form prints its dice as `xky` does, returns the same kind of total (so `tact() + 10` works),
and counts as a tagged GM roll for Story 14.

**Acceptance Scenarios**:

1. **Given** Air 3 and tact 2 recorded, **Then** `tact()` rolls 5k3 and asks nothing.
2. **Given** Air 3 recorded and no sincerity, **Then** `sincerity()` asks for the rank, accepts
   0 to 5 and re-asks otherwise, records it, and rolls.
3. **Given** nothing recorded, **Then** `sincerity(2)` asks for Air, accepts 2 to 6, records both.
4. **Given** Air 3 and tact 2, **Then** `tact(vp)` rolls 6k4 and `tact(vp * 2)` rolls 7k5, and
   neither triggers a disagreement nor changes the record.
5. **Given** no open conversation, **Then** a call says there is no NPC to roll for.
6. **Given** `acting(2)`, **Then** acting 2 is recorded, nothing is rolled and no ring is asked for.
7. **Given** acting 2 recorded, **Then** `sincerity()` and `intimidation()` each add +10, say so,
   and a sneaking roll adds nothing.
8. **Given** history 3 recorded, **Then** `law()` and `strategy()` each add +15 and `culture()` and
   `heraldry()` add nothing.

---

### User Story 14 - annotate() already knows the opposing roll (Priority: P1)

When a player's roll has a fixed opposing skill and the GM has a TAGGED roll of that skill in this
conversation, `annotate()` pairs them itself. For a manipulation roll with a tact roll on record,
the GM's words: *"the only thing that I am asked to annotate is adding the note."* The pairing and
the free raises - now from EXACT ranks on both sides, not inferred from a pool - are shown, not
asked. The keystroke undo of Story 3 drops back to the full picker and bonus questions.

Applies to manipulation (tact), sneaking (investigation) and acting (investigation); a line of
questioning takes its sincerity roll directly. Skills that contest THEMSELVES are not pre-paired: a
GM history roll is not evidence that a player's history roll was contested.

**Acceptance Scenarios**:

1. **Given** a manipulation roll and one tagged tact roll, **Then** the pairing and bonuses are
   displayed and the one question is what it was for.
2. **Given** several tagged tact rolls, **Then** the one nearest in time that no other roll has
   used is chosen, and the undo reaches the others.
3. **Given** no tagged tact roll, **Then** the picker of Story 4 appears, 15 entry included.
4. **Given** the GM undoes the pairing, **Then** the picker and both bonus questions are asked as
   today.

---

### Edge Cases

- A roll tagged with NO conversation open (the GM often rolls the NPC's side first): the tag is
  kept on the remembered roll, nothing is recorded or checked because there is no NPC yet, and when
  a conversation begins the recent tagged rolls are recorded or checked then.
- More than ten dice: the inference reads the pool AS ASKED FOR (`xky(12, 3)`), not the capped pool
  actually rolled.
- A tag applied twice, or two different tags on one roll: the second is an error, not a silent
  overwrite.
- A skill whose ring is a choice (pontificate: Water or Air) or whose roll is not ring-plus-rank
  (athletics): tag-only, never inferred from and not callable, until the GM asks for more.
- Correcting a RING does not recompute ranks recorded under the old ring; ranks are stored as
  ranks, not as dice.

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

- **FR-016**: Every skill in the rules' skill list MUST exist at the prompt as a tag usable as
  `<roll> - <skill>`, which marks the GM's roll with that skill and evaluates to the same total.
- **FR-017**: A tagged roll in an open conversation MUST be read as ring = kept dice and rank =
  rolled minus kept, less school extra dice (derived from the rules text), excluding void-point
  dice the tool was told about. The skill's ring MUST be read from the rules, not listed in code.
- **FR-018**: NPC ring and skill values MUST be stored in a parsable block of the NPC's GM-only
  notes, MUST NEVER appear in the bio, MUST be loaded once when the conversation begins, and MUST
  be updated in the local copy immediately and persisted with the conversation's debounced write.
- **FR-019**: A tagged roll disagreeing with the record on rank or ring MUST stop and offer exactly:
  the roll was a mistake, or the record was wrong. Ctrl-C there MUST be caught, MUST mean the
  former, and MUST NOT end the repl or discard anything else. A mistaken roll MUST never be offered
  or pre-paired as an opposing roll.
- **FR-020**: Skill tags MUST be callable as `skill()`, `skill(rank)`, `skill(rolled, kept)`, each
  optionally with `vp` or `vp * N`; missing values MUST be prompted for within 0-5 (rank) and 2-6
  (ring). `skill(rolled, kept)` MUST behave exactly as `xky(rolled, kept) - skill`.
- **FR-020a**: `acting(N)` and `history(N)` MUST record the rank and MUST NOT roll. Recorded acting
  MUST add +5 per rank to the NPC's sincerity and intimidation rolls, and recorded history to law
  and strategy rolls; sneaking, culture and heraldry MUST NOT receive an automatic bonus. Every
  automatic bonus MUST be named in the roll's printed line.
- **FR-019a**: When the disagreement is exactly 1k1 or 2k2, the prompt MUST also offer the void
  point answer worded for the direction and count, with the effects Story 12 gives.
- **FR-021**: `annotate()` MUST pre-pair a manipulation, sneaking or acting roll with a tagged GM
  roll of its opposing skill, compute free raises from the recorded ranks, and ask only for the
  note (plus acting's outcome). The Story 3 undo MUST restore the full questions.
- **FR-022**: On a line that is not grilling the TOOL adds the NPC's 2 casual free raises; the GM
  never adds them by hand (message 5). Any bonus the GM adds to a roll is never adjusted.

### Key Entities

- **NPC numbers**: the rings and skill ranks established for one NPC by the GM's own rolls, kept
  in that NPC's GM-only notes.
- **Skill tag**: the name of a skill at the prompt - marks a roll, and rolls for the NPC when called.
- **Void point marker** (`vp`): says how many void points a called roll spends.

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

## Resolved with the GM (message 5)

- The casual-conversation raises are applied ONLY by the grilling flag, never by hand. The `+ 10`
  in the GM's example was Fumitake's acting 2 (a free raise per rank on sincerity).

## Resolved with the GM (message 6)

- The void point answer exists, in four wordings, for differences of exactly 1k1 or 2k2.
- Acting and history are recorded by `acting(N)` / `history(N)` and never rolled; their
  unconditional free raises are automatic, their conditional ones are the GM's to add.

## Open Questions (for the GM, before the scope closes)

C. **Do the automatic raises also land on `xky(8, 3) - sincerity`, or only on `sincerity()`?** The
   GM ruled `sincerity(5, 3)` is "the same as" `xky(5, 3) - sincerity`, and also plans to type
   `xky(8, 3) + 10 - sincerity` where the `+ 10` IS acting 2 - which, if the tag adds acting as
   well, counts it twice. Proposed: the automatic raises apply to EVERY tagged form, always named
   in the printed line (`+10 acting 2`), so the hand-typed `+ 10` is what gets dropped.
D. **History and culture.** The GM called history's raises on culture conditional. The rules read
   the other way: *"one free raise on all culture, law, and strategy rolls ... You also receive
   these free raises on heraldry rolls, but ... only ... places and families and institutions"* -
   heraldry is the conditional one. The spec follows the GM's words (culture NOT automatic) until
   told otherwise; if the rules are right it is one table row.

## Review history

- 2026-09-19: DRAFT, scope open. The independent `spec-fidelity` review (constitution XVI) runs
  when the GM closes the scope, against gm-request.md as it then stands; no verdict is recorded
  yet and nothing may be implemented until one is.
