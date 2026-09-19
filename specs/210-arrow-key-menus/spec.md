# Feature Specification: Arrow-key menus for every choice in the roll prompts

**Feature Directory**: `specs/210-arrow-key-menus`

**Created**: 2026-09-19

**Status**: Implemented 2026-09-19.

**Input**: GM request 2026-09-19, verbatim in [gm-request.md](gm-request.md), including the plan the
GM approved. Builds on feature 202 (`annotate()`), 207 (the raw-key reader, the two-press undo).

## Why

Every choice in `annotate()` is typed: `o`, `c`, `ob`, a row number. The GM would rather see the
options, have one highlighted, move with the arrow keys and press Enter - at the busiest moment of
the session, looking at a list beats remembering its letters.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A choice is made with Up, Down and Enter (Priority: P1)

Wherever a roll prompt offers a fixed set of options, the GM sees them as a list with one
highlighted, moves the highlight with the Up and Down arrows, and presses Enter to choose.

```
  Open, contested, discard, or open with bonus?
  > open                       o
    contested                  c
    discard                    d
    open with a bonus          ob
    finish - keep what is staged
```

**Acceptance Scenarios**:

1. **Given** the open/contested/discard/bonus question at a terminal, **When** the GM presses Down
   then Enter, **Then** "contested" is chosen, exactly as typing `c` chooses it today.
2. **Given** any of: "Which roll?", "Which of yours?", the always-contested opposing-roll picker
   (with its `f` / `n` / `t` / discard entries), "Which line?", the discard-or-leave-it question
   asked for an interrogation roll when no line has been declared, how the NPC appeared, the
   join-or-discard question of `new_line_of_questioning`, and the mistake / record-was-wrong
   prompts of a tagged or called NPC roll, **Then** each is the same kind of list.
3. **Given** a prompt where a blank line means "finish" today, **Then** the list has an explicit
   finish row that does what the blank line did.
4. **Given** Up on the first row or Down on the last, **Then** the highlight wraps around.
5. **Given** more options than the terminal has rows, **Then** the list scrolls with the highlight.

### User Story 2 - Nothing typed today stops working (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a list, **When** the GM types an option's letters or a row's number, **Then** the
   highlight jumps to it, and Enter chooses it - so `o` Enter, `ob` Enter and `12` Enter all still
   work keystroke for keystroke.
2. **Given** free-text prompts (what the roll was for, a bonus, a typed total, a rank) and the
   MIXED prompt (a note that also accepts `c`, `ob`, `d`, `f`, `n`, `t`), **Then** they are typed
   lines exactly as today, with the two-press undo where it exists.
3. **Given** no terminal (a pipe, a script, the test suite) or a caller that supplies its own
   answers, **Then** every prompt is asked as a typed question exactly as today.
4. **Given** the join-or-discard list of `new_line_of_questioning`, **When** the GM presses Enter
   and nothing else, **Then** the roll joins the line - today's `[P/d]` default, where a bare
   Enter per roll is the GM's habit and "discard" would be data loss.
5. **Given** Ctrl-C in a list inside `annotate()`, **Then** everything staged in that run is
   abandoned, as at every other prompt. At the mistake / record-was-wrong prompt Ctrl-C remains the
   ANSWER "the roll was a mistake" (feature 207).

### User Story 3 - A roll arriving while a list is open does not wreck the screen (Priority: P1)

The background watcher prints each roll above the prompt. With a list open, the announcement
appears above the list and the list is redrawn beneath it with the highlight where it was.

**Acceptance Scenarios**:

1. **Given** an open list, **When** the watcher announces a roll, **Then** the announcement is
   printed above, the whole list is redrawn below it, and the highlight has not moved.

## Requirements *(mandatory)*

- **FR-001**: Every roll prompt that is a choice from a fixed list MUST, at a terminal, be an
  arrow-key list: Up/Down move, Enter chooses, one row always highlighted. That rule governs; the
  prompts that exist today are listed in User Story 1 scenario 2 as illustration, not as a limit.
- **FR-002**: Every answer that can be typed today MUST still select the same option: typing moves
  the highlight to the matching row and Enter chooses it.
- **FR-003**: Free-text prompts and the mixed note-or-letter prompt MUST NOT change.
- **FR-004**: With no terminal, or with a caller-supplied answer source, prompts MUST behave
  exactly as today. The existing scripted tests MUST pass unmodified.
- **FR-005**: Ctrl-C and Ctrl-D MUST mean what they mean at the same prompt today, and the terminal
  MUST be restored whatever happens.
- **FR-006**: A watcher announcement while a list is open MUST leave the list intact and the
  highlight unmoved.
- **FR-007**: One reusable helper MUST implement the list; prompts call it rather than each drawing
  their own. No new third-party dependency.

## Decisions the request left open

1. **Typing MOVES the highlight; Enter chooses.** Declined: a letter choosing instantly. That would
   be one keystroke shorter but would break `ob` (its `o` would choose "open") and every
   two-digit row, and `o` Enter is what the GM's hands already do.
2. **Which row starts highlighted**: whatever a bare Enter means at that prompt today, else the
   first row. So the join-or-discard list opens on "part of this line" (today's `[P/d]` default),
   the no-lines interrogation question on "leave it for now" (today's blank), and the
   record-vs-mistake prompts on "mistake", which is what Ctrl-C already means there.
3. **A defect found on the way and fixed with it** (constitution XIV): when the watcher announces a
   roll while a TYPED roll prompt is open, it redraws the Python `>>> ` prompt instead of the
   question being asked. The announcement now redraws the actual question.
4. **What a finished list leaves behind**: it collapses to ONE line, the question and the chosen
   row (`  Which of your rolls? 27 tact  (5k3: kept 9, 9, 9) at 21:04:10`), so the scrollback
   reads as a record of what was chosen. Not the GM's word - the session's call. Declined:
   leaving the whole list on screen with the highlight on the chosen row, which keeps the
   unchosen rows visible (as today's printed enumeration does) at the cost of five to twenty
   lines of scrollback per choice in a run that makes many.

## Review history

Independent `spec-fidelity` review (constitution XVI), against gm-request.md as written - Message 1
AND the plan Message 2 approved.

- **Round 1 - CHANGES REQUIRED** (2026-09-19). Typing-moves-Enter-chooses, leaving the mixed
  prompt typed, the watcher defect fix, and the two prompts outside `annotate()` were all found
  faithful. Three changes: FR-001's enumeration was exhaustive and missed the no-lines
  "Discard it?" question (now illustrative, and listed); the join-or-discard default was unpinned
  (a list opening on "discard" would turn the GM's Enter-per-roll habit into data loss); and the
  collapse-to-one-line behavior was presented as a requirement when it is the session's decision
  (now Decision 4, with the declined alternative).
- **Round 2 - FAITHFUL** (2026-09-19). All three changes confirmed, in the spec and against the
  code. One aside: wrapping at the ends and scrolling a tall list are the session's calls.

## Success Criteria *(mandatory)*

- **SC-001**: In a whole `annotate()` run at a terminal, every choice can be made without typing a
  letter or a number.
- **SC-002**: Every scripted test that existed before the feature passes unchanged.
- **SC-003**: After any exit from a list - choice, Ctrl-C, Ctrl-D, an error - the terminal echoes
  and line-edits normally.
